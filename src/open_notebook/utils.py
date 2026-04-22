import hashlib
import os
import requests

def calculate_sha256(file_path):
    """計算檔案的 SHA256 雜湊值"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"計算 SHA256 失敗 {file_path}: {e}")
        return None
