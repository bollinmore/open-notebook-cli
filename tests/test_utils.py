import pytest
from open_notebook.utils import calculate_sha256
import os

def test_calculate_sha256_file_exists(tmp_path):
    # 建立一個測試檔案
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("hello world")
    
    # 驗證雜湊值是否產生
    sha = calculate_sha256(str(p))
    assert sha is not None
    assert len(sha) == 64  # SHA256 長度應為 64

def test_calculate_sha256_file_not_exists():
    sha = calculate_sha256("non_existent_file.txt")
    assert sha is None
