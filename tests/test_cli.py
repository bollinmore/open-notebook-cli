import pytest
from unittest.mock import patch, MagicMock
from open_notebook.cli import (
    list_notebooks, list_models, list_sources, search_query, 
    ask_query, chat_execute, upload_files, clear_notebook
)

@patch('requests.post')
@patch('requests.get')
@patch('os.listdir')
@patch('os.path.exists')
@patch('builtins.open')
@patch('open_notebook.cli.calculate_sha256')
@patch('open_notebook.cli.get_upload_dir')
def test_upload_files_success(mock_get_upload_dir, mock_calc_sha, mock_open, mock_exists, mock_listdir, mock_get, mock_post, capsys):
    mock_exists.return_value = True
    mock_listdir.return_value = ["test.txt"]
    mock_calc_sha.return_value = "hash123"
    mock_get_upload_dir.return_value = None # 測試環境不模擬實體上傳目錄
    
    # Mock requests.get (取得現有來源)
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = [] # 假設目前無現有檔案
    mock_get.return_value = mock_get_resp

    # Mock requests.post (上傳)
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post.return_value = mock_post_resp

    upload_files("./dummy_dir", "nb1", enable_insights=False)
    
    captured = capsys.readouterr()
    assert "上傳: 1" in captured.out
    assert "失敗: 0" in captured.out


@patch('requests.delete')
@patch('requests.get')
def test_clear_notebook_success(mock_get, mock_delete, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": "s1", "title": "Source 1"}]
    mock_get.return_value = mock_response
    
    mock_del_response = MagicMock()
    mock_del_response.status_code = 200
    mock_delete.return_value = mock_del_response

    clear_notebook("nb1")
    
    captured = capsys.readouterr()
    assert "成功刪除" in captured.out

@patch('requests.get')
def test_list_notebooks_failure(mock_get, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    list_notebooks()
    
    captured = capsys.readouterr()
    assert "無法取得筆記本列表" in captured.out

@patch('requests.post')
@patch('requests.get')
@patch('os.listdir')
@patch('os.path.exists')
@patch('open_notebook.cli.calculate_sha256')
@patch('open_notebook.cli.get_upload_dir')
def test_upload_files_failure(mock_get_upload_dir, mock_calc_sha, mock_exists, mock_listdir, mock_get, mock_post, capsys):
    mock_exists.return_value = True
    mock_listdir.return_value = ["test.txt"]
    mock_calc_sha.return_value = "hash123"
    mock_get_upload_dir.return_value = None
    
    # Mock requests.get (取得現有來源)
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = []
    mock_get.return_value = mock_get_resp

    # Mock requests.post (失敗上傳)
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 500
    mock_post.return_value = mock_post_resp

    upload_files("./dummy_dir", "nb1", enable_insights=False)
    
    captured = capsys.readouterr()
    assert "失敗: 1" in captured.out


@patch('requests.get')
def test_clear_notebook_api_failure(mock_get, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    clear_notebook("nb1")
    
    captured = capsys.readouterr()
    assert "無法取得來源列表" in captured.out

@patch('requests.get')
def test_list_models_success(mock_get, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": "m1", "provider": "p1", "type": "lang", "name": "Model 1"}
    ]
    mock_get.return_value = mock_response

    list_models()
    
    captured = capsys.readouterr()
    assert "m1" in captured.out
    assert "Model 1" in captured.out

@patch('requests.post')
def test_search_query_success(mock_post, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [{"title": "Search Result 1"}]}
    mock_post.return_value = mock_response

    search_query("test query")
    
    captured = capsys.readouterr()
    assert "Search Result 1" in captured.out

@patch('requests.post')
def test_chat_execute_success(mock_post, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "chat response"}
    mock_post.return_value = mock_response

    chat_execute("session1", "hello")
    
    captured = capsys.readouterr()
    assert "chat response" in captured.out

@patch('requests.post')
def test_ask_query_success(mock_post, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # 模擬串流回應
    line1 = b"data: {\"type\": \"answer\", \"content\": \"answer content\"}\n"
    mock_response.iter_lines.return_value = [line1]
    mock_post.return_value = mock_response

    ask_query("test question")
    
    captured = capsys.readouterr()
    assert "answer content" in captured.out
