import os, sqlite3, json, time, hashlib, hmac, base64
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, g, request, redirect, url_for, render_template, session, send_file, jsonify, flash
from flask_bcrypt import Bcrypt
import qrcode
from io import BytesIO


APP_SECRET = os.environ.get("CM_SECRET", "change-me-secret")  # HMAC 密钥
DB_PATH = "classmint.db"

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-key")
bcrypt = Bcrypt(app)


# 数据库连接
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

from datetime import datetime

@app.template_filter("datetime")
def _fmt(ts: int):
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "-"


@app.teardown_appcontext
def close_db(_e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE, password_hash TEXT
    );
    CREATE TABLE IF NOT EXISTS tokens (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      token TEXT UNIQUE, amount INTEGER, one_time INTEGER,
      expires_at INTEGER, issued_by INTEGER, status TEXT DEFAULT 'ACTIVE',
      created_at INTEGER, description TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS claims (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      token_id INTEGER, claimer TEXT, amount INTEGER, created_at INTEGER
    );
    CREATE TABLE IF NOT EXISTS ledger (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      tx_id INTEGER, prev_hash TEXT, record_hash TEXT, created_at INTEGER,
      block_data TEXT
    );
    """)
    
    # 检查并添加缺失的列
    try:
        db.execute("SELECT description FROM tokens LIMIT 1")
    except sqlite3.OperationalError:
        db.execute("ALTER TABLE tokens ADD COLUMN description TEXT DEFAULT ''")
    
    try:
        db.execute("SELECT block_data FROM ledger LIMIT 1")
    except sqlite3.OperationalError:
        db.execute("ALTER TABLE ledger ADD COLUMN block_data TEXT")
    
    # 默认管理员
    u = db.execute("SELECT 1 FROM users WHERE username='admin'").fetchone()
    if not u:
        pw = bcrypt.generate_password_hash("admin123").decode()
        db.execute("INSERT INTO users (username, password_hash) VALUES (?,?)", ("admin", pw))
        db.commit()

# 身份验证
def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("uid"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper

# 工具函数
def now_ts(): return int(time.time())
def sha256(s: bytes) -> str: return hashlib.sha256(s).hexdigest()
def b64url(data: bytes) -> str: return base64.urlsafe_b64encode(data).decode().rstrip("=")
def sign_payload(payload: dict) -> str:
    """生成token: CM1.<payload_b64>.<sig>"""
    p = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sig = hmac.new(APP_SECRET.encode(), p, hashlib.sha256).digest()
    return f"CM1.{b64url(p)}.{b64url(sig)}"

def verify_token_sig(token: str) -> dict | None:
    try:
        prefix, p64, s64 = token.split(".")
        if prefix != "CM1": return None
        p = base64.urlsafe_b64decode(p64 + "==")
        s = base64.urlsafe_b64decode(s64 + "==")
        if not hmac.compare_digest(hmac.new(APP_SECRET.encode(), p, hashlib.sha256).digest(), s):
            return None
        return json.loads(p.decode())
    except Exception:
        return None

def add_block(tx_id: int, claim_data: dict = None):
    """添加新区块到区块链"""
    db = get_db()
    prev = db.execute("SELECT record_hash FROM ledger ORDER BY id DESC LIMIT 1").fetchone()
    prev_hash = prev["record_hash"] if prev else ""
    
    # 构建区块数据
    block_data = {
        "tx_id": tx_id,
        "timestamp": now_ts(),
        "prev_hash": prev_hash,
        "claim_data": claim_data
    }
    
    payload = json.dumps(block_data, separators=(",", ":"))
    record_hash = sha256((prev_hash + payload + str(now_ts())).encode())
    
    db.execute("INSERT INTO ledger (tx_id, prev_hash, record_hash, created_at, block_data) VALUES (?,?,?,?,?)",
               (tx_id, prev_hash, record_hash, now_ts(), payload))
    db.commit()
    return record_hash

# 页面路由
@app.route("/login", methods=["GET","POST"])
def login():
    init_db()
    if request.method == "POST":
        username = request.form.get("username","")
        password = request.form.get("password","")
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row and bcrypt.check_password_hash(row["password_hash"], password):
            session["uid"] = row["id"]; session["uname"] = row["username"]
            return redirect(url_for("dashboard"))
        flash("账号或密码错误")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    db = get_db()
    tokens = db.execute("SELECT * FROM tokens ORDER BY id DESC LIMIT 50").fetchall()
    claims = db.execute("SELECT c.*, t.token FROM claims c LEFT JOIN tokens t ON t.id=c.token_id ORDER BY c.id DESC LIMIT 20").fetchall()
    
    # 获取统计数据
    total_tokens = db.execute("SELECT COUNT(*) as count FROM tokens").fetchone()["count"]
    total_claims = db.execute("SELECT COUNT(*) as count FROM claims").fetchone()["count"]
    active_amount = db.execute("SELECT COALESCE(SUM(amount), 0) as total FROM tokens WHERE status='ACTIVE'").fetchone()["total"]
    blockchain_length = db.execute("SELECT COUNT(*) as count FROM ledger").fetchone()["count"]
    
    return render_template("dashboard.html", 
                         tokens=tokens, 
                         claims=claims, 
                         uname=session.get("uname"),
                         stats={
                             "total_tokens": total_tokens,
                             "total_claims": total_claims,
                             "active_amount": active_amount,
                             "blockchain_length": blockchain_length
                         })

@app.route("/token/new", methods=["POST"])
@login_required
def token_new():
    try:
        # 金额从元转换为分
        amount_yuan = float(request.form.get("amount", "0"))
        amount_cents = int(amount_yuan * 100)
        
        if amount_cents <= 0:
            flash("金额必须大于0")
            return redirect(url_for("dashboard"))
            
        one_time = 1 if request.form.get("one_time") == "on" else 0
        minutes = int(request.form.get("expire_minutes", "60"))
        description = request.form.get("description", "").strip()
        
        if minutes <= 0:
            flash("有效期必须大于0分钟")
            return redirect(url_for("dashboard"))
        
        payload = {
            "amount": amount_cents, 
            "one": one_time, 
            "exp": now_ts() + minutes*60, 
            "nonce": sha256(os.urandom(16)),
            "desc": description
        }
        
        token_str = sign_payload(payload)
        db = get_db()
        db.execute("INSERT INTO tokens (token, amount, one_time, expires_at, issued_by, status, created_at, description) VALUES (?,?,?,?,?,?,?,?)",
                   (token_str, amount_cents, one_time, payload["exp"], session["uid"], "ACTIVE", now_ts(), description))
        db.commit()
        
        flash(f"成功生成 ¥{amount_yuan:.2f} 的奖励令牌！")
        return redirect(url_for("dashboard"))
        
    except ValueError:
        flash("请输入有效的金额")
        return redirect(url_for("dashboard"))
    except Exception as e:
        flash(f"生成令牌失败: {str(e)}")
        return redirect(url_for("dashboard"))

@app.route("/token/qr/<int:token_id>")
@login_required
def token_qr(token_id:int):
    db = get_db()
    row = db.execute("SELECT token FROM tokens WHERE id=?", (token_id,)).fetchone()
    if not row: return "Not found", 404
    
    # 生成二维码
    url_text = f"https://classmint.local/claim?token={row['token']}"
    img = qrcode.make(url_text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.route("/token/void/<int:token_id>", methods=["POST"])
@login_required
def token_void(token_id:int):
    db = get_db()
    db.execute("UPDATE tokens SET status='VOID' WHERE id=? AND status='ACTIVE'", (token_id,))
    db.commit()
    flash("令牌已作废")
    return redirect(url_for("dashboard"))

@app.route("/blockchain")
@login_required
def blockchain_view():
    """区块链可视化页面"""
    db = get_db()
    blocks = db.execute("SELECT * FROM ledger ORDER BY id ASC").fetchall()
    return render_template("blockchain.html", blocks=blocks, uname=session.get("uname"))

# API接口
@app.route("/api/token/create", methods=["POST"])
def api_token_create():
    # 需要鉴权：header X-Admin-Key = APP_SECRET
    if request.headers.get("X-Admin-Key") != APP_SECRET:
        return jsonify({"detail":"unauthorized"}), 401
    
    try:
        data = request.get_json(force=True)
        amount_yuan = float(data.get("amount", 0))
        amount_cents = int(amount_yuan * 100)
        
        if amount_cents <= 0:
            return jsonify({"detail": "amount must be positive"}), 400
            
        one_time = 1 if data.get("one_time", True) else 0
        minutes = int(data.get("expire_minutes", 60))
        description = data.get("description", "")
        
        if minutes <= 0:
            return jsonify({"detail": "expire_minutes must be positive"}), 400
        
        payload = {
            "amount": amount_cents, 
            "one": one_time, 
            "exp": now_ts() + minutes*60, 
            "nonce": sha256(os.urandom(16)),
            "desc": description
        }
        
        token_str = sign_payload(payload)
        db = get_db()
        db.execute("INSERT INTO tokens (token, amount, one_time, expires_at, issued_by, status, created_at, description) VALUES (?,?,?,?,?,?,?,?)",
                   (token_str, amount_cents, one_time, payload["exp"], 0, "ACTIVE", now_ts(), description))
        db.commit()
        tid = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        
        return jsonify({
            "token_id": tid, 
            "token": token_str,
            "amount_yuan": amount_yuan,
            "expires_at": payload["exp"]
        })
        
    except ValueError:
        return jsonify({"detail": "invalid amount"}), 400
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route("/api/claim", methods=["POST"])
def api_claim():
    """提交token + user_id，核销并记账 + 写链"""
    try:
        data = request.get_json(force=True)
        token_str = (data.get("token") or "").strip()
        claimer = str(data.get("user_id") or data.get("claimer") or "unknown")

        if not token_str:
            return jsonify({"detail": "token is required"}), 400

        db = get_db()
        t = db.execute("SELECT * FROM tokens WHERE token=?", (token_str,)).fetchone()
        
        if not t: 
            return jsonify({"detail":"invalid token"}), 400
        if t["status"] != "ACTIVE": 
            return jsonify({"detail":"token inactive"}), 400
        if now_ts() > t["expires_at"]: 
            return jsonify({"detail":"token expired"}), 400

        # one-time 限制：已被核销就不能再次使用
        if t["one_time"]:
            used = db.execute("SELECT 1 FROM claims WHERE token_id=?", (t["id"],)).fetchone()
            if used: 
                return jsonify({"detail":"token already claimed"}), 400

        # 写领取记录
        db.execute("INSERT INTO claims (token_id, claimer, amount, created_at) VALUES (?,?,?,?)",
                   (t["id"], claimer, t["amount"], now_ts()))
        db.commit()
        tx_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        # 构建领取数据用于区块链
        claim_data = {
            "claimer": claimer,
            "amount": t["amount"],
            "token_id": t["id"],
            "description": t.get("description", "")
        }

        # 写链
        block_hash = add_block(tx_id, claim_data)

        # 如果 token 为单次使用，立刻标记失效
        if t["one_time"]:
            db.execute("UPDATE tokens SET status='USED' WHERE id=?", (t["id"],))
            db.commit()

        # 返回本次金额与 block hash
        return jsonify({
            "ok": True, 
            "amount": t["amount"], 
            "amount_yuan": t["amount"] / 100,
            "tx_id": tx_id, 
            "block_hash": block_hash,
            "description": t.get("description", "")
        })
        
    except Exception as e:
        return jsonify({"detail": f"claim failed: {str(e)}"}), 500

@app.route("/api/ledger/verify")
def api_ledger_verify():
    """验证区块链完整性"""
    try:
        db = get_db()
        rows = db.execute("SELECT * FROM ledger ORDER BY id ASC").fetchall()
        
        if not rows:
            return jsonify({"ok": True, "length": 0, "message": "区块链为空"})
        
        prev = ""
        for r in rows:
            try:
                # 解析区块数据
                if r["block_data"]:
                    block_data = json.loads(r["block_data"])
                else:
                    # 兼容旧数据
                    block_data = {"tx_id": r["tx_id"]}
                
                payload = json.dumps(block_data, separators=(",", ":"))
                expect = sha256((prev + payload + str(r["created_at"])).encode())
                
                if expect != r["record_hash"]:
                    return jsonify({
                        "ok": False, 
                        "broken_at": r["id"],
                        "expected_hash": expect,
                        "actual_hash": r["record_hash"],
                        "message": "哈希不匹配"
                    })
                prev = r["record_hash"]
                
            except (json.JSONDecodeError, TypeError) as e:
                # 如果数据格式有问题，使用基本验证
                payload = json.dumps({"tx_id": r["tx_id"]}, separators=(",", ":"))
                expect = sha256((prev + payload + str(r["created_at"])).encode())
                
                if expect != r["record_hash"]:
                    return jsonify({
                        "ok": False,
                        "broken_at": r["id"],
                        "message": "区块数据格式错误，但哈希验证失败"
                    })
                prev = r["record_hash"]
        
        return jsonify({
            "ok": True, 
            "length": len(rows),
            "message": "所有区块验证通过",
            "last_hash": prev
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/ledger/status")
def api_ledger_status():
    """获取区块链状态信息"""
    try:
        db = get_db()
        total_blocks = db.execute("SELECT COUNT(*) as count FROM ledger").fetchone()["count"]
        total_transactions = db.execute("SELECT COUNT(*) as count FROM claims").fetchone()["count"]
        total_amount = db.execute("SELECT COALESCE(SUM(amount), 0) as total FROM claims").fetchone()["total"]
        
        # 获取最新的几个区块
        recent_blocks = db.execute("""
            SELECT l.*, c.claimer, c.amount 
            FROM ledger l 
            LEFT JOIN claims c ON l.tx_id = c.id 
            ORDER BY l.id DESC 
            LIMIT 5
        """).fetchall()
        
        return jsonify({
            "ok": True,
            "total_blocks": total_blocks,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "total_amount_yuan": total_amount / 100,
            "recent_blocks": [
                {
                    "block_id": b["id"],
                    "tx_id": b["tx_id"],
                    "hash": b["record_hash"],
                    "timestamp": b["created_at"],
                    "claimer": b["claimer"],
                    "amount": b["amount"]
                } for b in recent_blocks
            ]
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# 启动入口
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="127.0.0.1", port=5050, debug=True, use_reloader=False)
