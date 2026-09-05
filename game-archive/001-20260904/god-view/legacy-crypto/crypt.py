#!/usr/bin/env python3
"""
狼人殺遊戲狀態加解密工具（標準庫實作，無外部相依）。

信封格式:
    {"v":1, "nonce":"<32 hex>", "ct":"<base64>", "tag":"<64 hex>"}

演算法:
    nonce      = secrets.token_bytes(16)（每次加密重新產生）
    keystream  = HMAC-SHA256(key, nonce || i.to_bytes(8,'big')) for i = 0,1,2,...
    ct         = plaintext_utf8 XOR keystream
    tag        = HMAC-SHA256(key, nonce || ct).hexdigest()      (encrypt-then-MAC)

解密一律先驗 tag（hmac.compare_digest 常數時間比較），驗不過即中止。

金鑰路徑**不硬編**在本檔：由 --keyfile 參數或 WOLF_KEYFILE 環境變數提供。
"""

import sys
import os
import io
import json
import base64
import hmac
import hashlib
import secrets
import argparse

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


class IntegrityError(Exception):
    """完整性驗證失敗 —— 密文遭竄改或金鑰不符。"""


def load_key(keyfile: str | None) -> bytes:
    path = keyfile or os.environ.get('WOLF_KEYFILE')
    if not path:
        raise SystemExit('錯誤：未提供金鑰來源（--keyfile 或 WOLF_KEYFILE）')
    with open(path, 'rb') as f:
        key = f.read()
    if len(key) != 32:
        raise SystemExit('錯誤：金鑰長度不正確（應為 32 bytes）')
    return key


def fingerprint(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()[:8]


def keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    i = 0
    while len(out) < length:
        out += hmac.new(key, nonce + i.to_bytes(8, 'big'), hashlib.sha256).digest()
        i += 1
    return bytes(out[:length])


def encrypt(key: bytes, plaintext: str) -> dict:
    pt = plaintext.encode('utf-8')
    nonce = secrets.token_bytes(16)
    ct = bytes(a ^ b for a, b in zip(pt, keystream(key, nonce, len(pt))))
    tag = hmac.new(key, nonce + ct, hashlib.sha256).hexdigest()
    return {
        'v': 1,
        'nonce': nonce.hex(),
        'ct': base64.b64encode(ct).decode('ascii'),
        'tag': tag,
    }


def decrypt(key: bytes, envelope: dict) -> str:
    if envelope.get('v') != 1:
        raise IntegrityError('信封版本不支援')
    try:
        nonce = bytes.fromhex(envelope['nonce'])
        ct = base64.b64decode(envelope['ct'], validate=True)
        tag = envelope['tag']
    except (KeyError, ValueError) as exc:
        raise IntegrityError(f'信封格式損毀：{exc}') from exc
    if len(nonce) != 16:
        raise IntegrityError('nonce 長度不正確')
    expected = hmac.new(key, nonce + ct, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, tag):
        raise IntegrityError('完整性標籤驗證失敗：密文遭竄改或金鑰不符，已中止解密')
    pt = bytes(a ^ b for a, b in zip(ct, keystream(key, nonce, len(ct))))
    return pt.decode('utf-8')


def read_envelope(path: str) -> dict:
    with io.open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def cmd_enc(args, key):
    with io.open(args.src, 'r', encoding='utf-8') as f:
        plaintext = f.read()
    envelope = encrypt(key, plaintext)
    with io.open(args.dst, 'w', encoding='utf-8') as f:
        json.dump(envelope, f, ensure_ascii=False)
    print(f'ENC 完成｜來源 {len(plaintext.encode("utf-8"))} bytes'
          f'｜密文 {os.path.getsize(args.dst)} bytes｜指紋 {fingerprint(key)}')


def cmd_dec_field(args, key):
    plaintext = decrypt(key, read_envelope(args.path))
    try:
        data = json.loads(plaintext)
    except json.JSONDecodeError:
        raise SystemExit('錯誤：內容不是 JSON，無法取單一欄位')
    node = data
    for part in args.field.split('.'):
        if isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                raise SystemExit(f'錯誤：找不到欄位 {args.field}')
        elif isinstance(node, dict) and part in node:
            node = node[part]
        else:
            raise SystemExit(f'錯誤：找不到欄位 {args.field}')
    print(node if isinstance(node, str) else json.dumps(node, ensure_ascii=False))


def cmd_verify(args, key):
    try:
        decrypt(key, read_envelope(args.path))
    except IntegrityError as exc:
        print(f'VERIFY 不通過｜{exc}')
        raise SystemExit(1)
    print(f'VERIFY 通過｜{os.path.basename(args.path)}｜指紋 {fingerprint(key)}')


def cmd_fingerprint(args, key):
    print(fingerprint(key))


def main():
    p = argparse.ArgumentParser(description='狼人殺遊戲狀態加解密工具')
    p.add_argument('--keyfile', help='金鑰檔路徑（預設讀 WOLF_KEYFILE 環境變數）')
    sub = p.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('enc');  s.add_argument('src'); s.add_argument('dst'); s.set_defaults(fn=cmd_enc)
    s = sub.add_parser('dec-field'); s.add_argument('path'); s.add_argument('field'); s.set_defaults(fn=cmd_dec_field)
    s = sub.add_parser('verify'); s.add_argument('path'); s.set_defaults(fn=cmd_verify)
    s = sub.add_parser('fingerprint'); s.set_defaults(fn=cmd_fingerprint)

    args = p.parse_args()
    key = load_key(args.keyfile)
    try:
        args.fn(args, key)
    except IntegrityError as exc:
        raise SystemExit(f'錯誤：{exc}')


if __name__ == '__main__':
    main()
