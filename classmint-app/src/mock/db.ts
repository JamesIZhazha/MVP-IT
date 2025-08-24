type Tx = { id:number; user_id:number; amount:number; type:'earn'|'redeem'; token?:string; created_at:number }
type Ledger = { id:number; tx_id:number; prev_hash:string; record_hash:string; created_at:number }

// 新增：ClassMint令牌类型
type ClassMintToken = { 
  amount: number; 
  one: number; 
  exp: number; 
  nonce: string; 
  desc?: string;
  used?: boolean;
  created_at?: number;
}

const LS = { 
  users:'cm_users', 
  accounts:'cm_accounts', 
  tokens:'cm_tokens', 
  classmint_tokens:'cm_classmint_tokens', // 新增：ClassMint令牌存储
  txs:'cm_transactions', 
  ledger:'cm_ledger', 
  seq:'cm_seq' 
}

const get = <T,>(k:string, def:T):T => (localStorage.getItem(k) ? JSON.parse(localStorage.getItem(k)!) as T : def)
const set = (k:string, v:any)=> localStorage.setItem(k, JSON.stringify(v))

function sha256Lite(s:string){ let h=0; for(let i=0;i<s.length;i++){ h=(h<<5)-h+s.charCodeAt(i); h|=0 } return ('00000000'+(h>>>0).toString(16)).slice(-8) }

// 新增：验证ClassMint令牌
function validateClassMintToken(tokenData: any): ClassMintToken {
  if (!tokenData || !tokenData.amount || !tokenData.exp || !tokenData.nonce) {
    throw new Error('令牌数据不完整');
  }
  
  // 检查过期时间
  const now = Math.floor(Date.now() / 1000);
  if (tokenData.exp < now) {
    throw new Error('令牌已过期');
  }
  
  return tokenData;
}

// 新增：检查ClassMint令牌是否已使用
function isClassMintTokenUsed(nonce: string): boolean {
  const usedTokens = get<string[]>(LS.classmint_tokens, []);
  return usedTokens.includes(nonce);
}

// 新增：标记ClassMint令牌为已使用
function markClassMintTokenAsUsed(nonce: string) {
  const usedTokens = get<string[]>(LS.classmint_tokens, []);
  if (!usedTokens.includes(nonce)) {
    usedTokens.push(nonce);
    set(LS.classmint_tokens, usedTokens);
  }
}

export const db = {
  ensureInit(){
    console.log('开始初始化数据库...')
    if(!localStorage.getItem(LS.seq)){
      console.log('数据库未初始化，开始创建初始数据...')
      set(LS.seq, {tx:1, ledger:1})
      set(LS.users, [{id:1, username:'student', password:'123456'}])
      set(LS.accounts, [{user_id:1, balance:0}])
      set(LS.tokens, [
        {token:'DEMO-100', amount:100, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-200', amount:200, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-300', amount:300, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-400', amount:400, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-500', amount:500, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-600', amount:600, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-700', amount:700, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-800', amount:800, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-900', amount:900, used:false, expires_at:Date.now()+86400000},
        {token:'DEMO-1000', amount:1000, used:false, expires_at:Date.now()+86400000}
      ])
      set(LS.classmint_tokens, []) // 新增：初始化ClassMint令牌存储
      set(LS.txs, [] as Tx[]); set(LS.ledger, [] as Ledger[])
      console.log('数据库初始化完成')
    } else {
      console.log('数据库已经初始化')
      // 确保ClassMint令牌存储存在
      if (!localStorage.getItem(LS.classmint_tokens)) {
        set(LS.classmint_tokens, [])
      }
    }
  },
  login(username:string, password:string){
    console.log('数据库登录函数被调用，用户名:', username, '密码:', password)
    const users = get<any[]>(LS.users, [])
    console.log('当前用户列表:', users)
    const u = users.find(x=>x.username===username && x.password===password)
    console.log('找到的用户:', u)
    const result = u ? {ok:true, user_id:u.id} : {ok:false}
    console.log('登录函数返回结果:', result)
    return result
  },
  balance(user_id:number){
    const acc = get<any[]>(LS.accounts, []).find(a=>a.user_id===user_id) || {user_id, balance:0}
    const recent = get<Tx[]>(LS.txs, []).filter(t=>t.user_id===user_id).sort((a,b)=>b.created_at-a.created_at).slice(0,10)
    return {balance: acc.balance, recent}
  },
  
  // 修改：支持ClassMint令牌和旧格式令牌
  claim(user_id:number, tokenStr:string){
    console.log('开始处理令牌领取，用户ID:', user_id, '令牌:', tokenStr)
    
    try {
      // 尝试解析为ClassMint令牌
      let tokenData: any;
      try {
        tokenData = JSON.parse(tokenStr);
        console.log('解析为ClassMint令牌:', tokenData)
        
        // 验证ClassMint令牌
        const validatedToken = validateClassMintToken(tokenData);
        
        // 检查是否已使用
        if (isClassMintTokenUsed(validatedToken.nonce)) {
          throw new Error('令牌已使用');
        }
        
        // 标记为已使用
        markClassMintTokenAsUsed(validatedToken.nonce);
        
        // 处理ClassMint令牌
        return this.processClassMintClaim(user_id, validatedToken);
        
      } catch (parseError) {
        console.log('不是ClassMint令牌，尝试旧格式:', parseError)
        
        // 尝试旧格式令牌
        const tokens = get<any[]>(LS.tokens, [])
        const t = tokens.find(x=>x.token===tokenStr)
        if(!t) throw new Error('无效令牌')
        if(t.used) throw new Error('令牌已使用')
        if(Date.now()>t.expires_at) throw new Error('令牌已过期')
        
        // 处理旧格式令牌
        return this.processLegacyClaim(user_id, t);
      }
      
    } catch (error: any) {
      console.error('令牌处理失败:', error)
      throw error;
    }
  },
  
  // 新增：处理ClassMint令牌领取
  processClassMintClaim(user_id: number, tokenData: ClassMintToken) {
    console.log('处理ClassMint令牌领取:', tokenData)
    
    // 更新账户余额
    const accs = get<any[]>(LS.accounts, []); 
    const target = accs.find(a=>a.user_id===user_id) || (accs.push({user_id, balance:0}), accs[accs.length-1])
    target.balance += tokenData.amount; 
    set(LS.accounts, accs)

    // 创建交易记录
    const seq = get<any>(LS.seq, {tx:1, ledger:1}); 
    const txs = get<Tx[]>(LS.txs, [])
    const tx:Tx = { 
      id:seq.tx++, 
      user_id, 
      amount:tokenData.amount, 
      type:'earn', 
      token:`CM1_${tokenData.nonce.substring(0,8)}`, 
      created_at:Date.now() 
    }
    txs.push(tx); 
    set(LS.txs, txs); 
    set(LS.seq, seq)

    // 创建区块链记录
    const ledger = get<Ledger[]>(LS.ledger, []); 
    const prev = ledger[ledger.length-1]?.record_hash || ''
    const payload = JSON.stringify({
      tx_id:tx.id, 
      user_id, 
      amount:tokenData.amount, 
      created_at:tx.created_at,
      token_type: 'classmint',
      nonce: tokenData.nonce
    })
    const record_hash = sha256Lite(prev + payload)
    ledger.push({ 
      id:seq.ledger++, 
      tx_id:tx.id, 
      prev_hash:prev, 
      record_hash, 
      created_at:tx.created_at 
    })
    set(LS.ledger, ledger); 
    set(LS.seq, seq)

    console.log('ClassMint令牌处理完成，新余额:', target.balance)
    return {balance: target.balance, tx_id: tx.id, block_hash: record_hash}
  },
  
  // 新增：处理旧格式令牌领取
  processLegacyClaim(user_id: number, token: any) {
    console.log('处理旧格式令牌领取:', token)
    
    const tokens = get<any[]>(LS.tokens, [])
    token.used = true; 
    set(LS.tokens, tokens)

    const accs = get<any[]>(LS.accounts, []); 
    const target = accs.find(a=>a.user_id===user_id) || (accs.push({user_id, balance:0}), accs[accs.length-1])
    target.balance += token.amount; 
    set(LS.accounts, accs)

    const seq = get<any>(LS.seq, {tx:1, ledger:1}); 
    const txs = get<Tx[]>(LS.txs, [])
    const tx:Tx = { 
      id:seq.tx++, 
      user_id, 
      amount:token.amount, 
      type:'earn', 
      token:token.token, 
      created_at:Date.now() 
    }
    txs.push(tx); 
    set(LS.txs, txs); 
    set(LS.seq, seq)

    const ledger = get<Ledger[]>(LS.ledger, []); 
    const prev = ledger[ledger.length-1]?.record_hash || ''
    const payload = JSON.stringify({tx_id:tx.id, user_id, amount:token.amount, created_at:tx.created_at})
    const record_hash = sha256Lite(prev + payload)
    ledger.push({ 
      id:seq.ledger++, 
      tx_id:tx.id, 
      prev_hash:prev, 
      record_hash, 
      created_at:tx.created_at 
    })
    set(LS.ledger, ledger); 
    set(LS.seq, seq)

    console.log('旧格式令牌处理完成，新余额:', target.balance)
    return {balance: target.balance, tx_id: tx.id, block_hash: record_hash}
  },
  
  verify(){
    const ledger = get<Ledger[]>(LS.ledger, []); 
    const txs = get<Tx[]>(LS.txs, []); 
    let prev = ''
    for(const r of ledger){
      const tx = txs.find(x=>x.id===r.tx_id)
      const expect = sha256Lite(prev + JSON.stringify({tx_id:tx?.id, user_id:tx?.user_id, amount:tx?.amount, created_at:tx?.created_at}))
      if(expect !== r.record_hash) return {ok:false, broken_at:r.id}
      prev = r.record_hash
    }
    return {ok:true, length:ledger.length}
  }
}