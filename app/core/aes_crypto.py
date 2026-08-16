#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ruijie CDC AES 加密模块。

参考 commonlib.base_lib.utils.aes_pass.AESCipher
密钥固定为 16 字节，IV 固定为 "0000000000000955"，PKCS7 填充。
"""
import base64


_KEY_MAP = {
    "ADMINPASSWORDKEY": b"ADMINPASSWORDKEY"[0:16],
    "USERPASSWORD_KEY": b"USERPASSWORD_KEY"[0:16],
}

_IV = b"0000000000000955"  # 16 字节，固定 IV


def _pad(text: bytes) -> bytes:
    """PKCS7 填充，block=16"""
    block_size = 16
    pad_len = block_size - (len(text) % block_size)
    return text + bytes([pad_len] * pad_len)


def _unpad(text: bytes) -> bytes:
    """PKCS7 去填充"""
    pad_len = text[-1]
    return text[:-pad_len]


def encrypt(text: str, key_name: str = "ADMINPASSWORDKEY") -> str:
    """
    AES-CBC 加密，返回 Base64 字符串。

    格式：iv(16字节) + AES_encrypt(padded_text) → base64
    与 Ruijie CDC 平台一致的加密方式。
    """
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        from Crypto.Cipher import AES

    key = _KEY_MAP.get(key_name, key_name.encode("utf-8")[0:16])
    cipher = AES.new(key, AES.MODE_CBC, _IV)
    encrypted = cipher.encrypt(_pad(text.encode("utf-8")))
    return base64.b64encode(_IV + encrypted).decode("ascii")


def decrypt(encoded: str, key_name: str = "ADMINPASSWORDKEY") -> str:
    """
    Base64 解码 + AES-CBC 解密。

    格式：取前16字节为 iv，剩余部分为 AES 密文 → 去 PKCS7 填充。
    """
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        from Crypto.Cipher import AES

    key = _KEY_MAP.get(key_name, key_name.encode("utf-8")[0:16])
    raw = base64.b64decode(encoded)
    iv = raw[:16]
    encrypted = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    return _unpad(decrypted).decode("utf-8")


if __name__ == "__main__":
    # 验证：与 AESCipher 输出一致
    e = AESCipher = type("AESCipher", (), {
        "encrypt_main": lambda self, text: encrypt(text, "ADMINPASSWORDKEY"),
    })()
    print("encrypt:", e.encrypt_main("9q7DP0GUzDDkHyGsYijcku37wEA4cbgDjH03M6F2T/g="))
    print("decrypt:", decrypt("9q7DP0GUzDDkHyGsYijcku37wEA4cbgDjH03M6F2T/g=", "ADMINPASSWORDKEY"))
