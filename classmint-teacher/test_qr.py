#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二维码内容测试脚本
"""

import qrcode
from PIL import Image
import json
import base64
import hashlib
import hmac
import os

def b64url(data: bytes) -> str:
    """Base64 URL安全编码"""
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def sign_payload(payload: dict, secret: str) -> str:
    """生成签名"""
    p = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sig = hmac.new(secret.encode(), p, hashlib.sha256).digest()
    return f"CM1.{b64url(p)}.{b64url(sig)}"

def test_qr_generation():
    """测试二维码生成"""
    print("=== 二维码内容测试 ===\n")
    
    # 模拟令牌数据
    payload = {
        "amount": 500,  # 5元，单位：分
        "one": 1,       # 单次使用
        "exp": 1734567890,  # 过期时间戳
        "nonce": hashlib.sha256(os.urandom(16)).hexdigest(),
        "desc": "课堂表现奖励"
    }
    
    secret = "change-me-secret"
    
    # 生成令牌
    token = sign_payload(payload, secret)
    print(f"生成的令牌: {token}")
    
    # 解析令牌
    try:
        parts = token.split(".")
        if len(parts) == 3 and parts[0] == "CM1":
            payload_b64 = parts[1]
            signature = parts[2]
            
            # 解码载荷
            payload_bytes = base64.urlsafe_b64decode(payload_b64 + "==")
            decoded_payload = json.loads(payload_bytes.decode())
            
            print(f"\n载荷数据:")
            print(f"  金额: {decoded_payload['amount']} 分 (¥{decoded_payload['amount']/100:.2f})")
            print(f"  单次使用: {'是' if decoded_payload['one'] else '否'}")
            print(f"  过期时间: {decoded_payload['exp']}")
            print(f"  随机数: {decoded_payload['nonce'][:16]}...")
            print(f"  说明: {decoded_payload.get('desc', '无')}")
            
            # 生成二维码内容
            qr_content = f"https://classmint.local/claim?token={token}"
            print(f"\n二维码内容:")
            print(f"  {qr_content}")
            
            # 生成二维码图片
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save("test_qr.png")
            print(f"\n二维码已保存为: test_qr.png")
            
        else:
            print("令牌格式错误")
            
    except Exception as e:
        print(f"解析令牌失败: {e}")

if __name__ == "__main__":
    test_qr_generation()
