import os
import argparse
import json
import requests
import sys

# 強制將 src 目錄加入 Python 路徑，解決 ModuleNotFoundError
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(script_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from dotenv import load_dotenv
from open_notebook.utils import calculate_sha256

# 載入 .env 檔案
load_dotenv()

# 基礎 API 設定
BASE_URL = "http://localhost:5055/api"
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# 讀取模型設定，設定預設值作為備援
DEFAULT_CHAT_MODEL = os.getenv("DEFAULT_CHAT_MODEL_ID", "model:jlozhpea95y964fq5tb0")
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL_ID", "")
DEFAULT_TTS_MODEL = os.getenv("DEFAULT_TTS_MODEL_ID", "")
DEFAULT_STT_MODEL = os.getenv("DEFAULT_STT_MODEL_ID", "")

# 讀取 System Prompt
DEFAULT_SYSTEM_PROMPT = os.getenv("DEFAULT_SYSTEM_PROMPT", "").strip()

def list_notebooks():
    """列出所有筆記本的 ID 與名稱"""
    try:
        response = requests.get(f"{BASE_URL}/notebooks")
        if response.status_code == 200:
            notebooks = response.json()
            print(f"{'ID':<30} | {'Name'}")
            print("-" * 60)
            for nb in notebooks:
                print(f"{nb['id']:<30} | {nb['name']}")
        else:
            print(f"無法取得筆記本列表，狀態碼: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器，請確認服務是否已啟動。(錯誤詳細資訊: {e})")

def list_models():
    """列出所有已註冊的模型"""
    try:
        response = requests.get(f"{BASE_URL}/models")
        if response.status_code == 200:
            models = response.json()
            print(f"{'ID':<35} | {'Provider':<10} | {'Type':<10} | {'Name'}")
            print("-" * 80)
            for m in models:
                print(f"{m['id']:<35} | {m['provider']:<10} | {m['type']:<10} | {m.get('name', 'N/A')}")
        else:
            print(f"無法取得模型列表，狀態碼: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器，請確認服務是否已啟動。(錯誤詳細資訊: {e})")

def get_model_name_by_id(model_id):
    """根據 Model ID 從 API 取得模型名稱，若失敗則回傳原 ID"""
    if not model_id:
        return "未知模型"
    try:
        response = requests.get(f"{BASE_URL}/models")
        if response.status_code == 200:
            models = response.json()
            for m in models:
                if m['id'] == model_id:
                    return m.get('name', model_id)
        return model_id
    except:
        return model_id

def list_sources(notebook_id=None):
    """列出來源，可指定筆記本 ID"""
    try:
        url = f"{BASE_URL}/sources"
        if notebook_id:
            url += f"?notebook_id={notebook_id}"
        
        response = requests.get(url)
        if response.status_code == 200:
            sources = response.json()
            print(f"{'ID':<30} | {'Title'}")
            print("-" * 60)
            for s in sources:
                print(f"{s['id']:<30} | {s.get('title', 'N/A')}")
        else:
            print(f"無法取得來源列表，狀態碼: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器，請確認服務是否已啟動。(錯誤詳細資訊: {e})")
    except Exception as e:
        print(f"連線錯誤: {e}")

def get_upload_dir():
    """動態偵測上傳目錄路徑"""
    # 1. 優先從環境變數讀取
    env_path = os.getenv("OPEN_NOTEBOOK_UPLOADS_DIR")
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. 嘗試透過 docker inspect 自動偵測 (適用於 Agent 與 Docker 同主機)
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "inspect", "open_notebook", "--format", "{{ range .Mounts }}{{ if eq .Destination \"/app/data\" }}{{ .Source }}{{ end }}{{ end }}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            docker_path = os.path.join(result.stdout.strip(), "uploads")
            if os.path.exists(docker_path):
                return docker_path
    except:
        pass

    # 3. 備案：相對於當前腳本的預設路徑
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 假設 cli.py 在 src/open_notebook/，專案根目錄在 ../../
    project_root = os.path.dirname(os.path.dirname(script_dir))
    default_path = os.path.join(project_root, "notebook_data", "uploads")
    
    return default_path if os.path.exists(default_path) else None

def upload_files(directory, notebook_id, enable_insights, dry_run=False):
    """上傳檔案，具備智能重複檢查與刪除更新功能"""
    url = f"{BASE_URL}/sources"
    extensions = ('.pdf', '.txt', '.md')
    
    if not os.path.exists(directory):
        print(f"錯誤: 來源目錄 {directory} 不存在")
        return

    # 1. 取得服務端現有的來源清單
    existing_sources = {}
    try:
        response = requests.get(f"{BASE_URL}/sources?notebook_id={notebook_id}")
        if response.status_code == 200:
            for s in response.json():
                # 使用標題(檔名)作為索引
                existing_sources[s.get('title')] = s['id']
    except Exception as e:
        print(f"警告: 無法取得現有來源列表，將跳過比對邏輯。({e})")

    # 2. 取得上傳目錄以進行雜湊比對
    uploads_dir = get_upload_dir()
    if uploads_dir:
        print(f"🔍 偵測到服務端上傳目錄: {uploads_dir}")
    else:
        print("⚠️ 無法定位服務端上傳目錄，將無法進行內容一致性檢查。")

    # 指定的 Transformation IDs
    TRANSFORMATION_IDS = [
        "transformation:r81jle14ok5pqhhaf9v9",
        "transformation:6xjan1bdex95n9qj8fg7",
        "transformation:i67qf0y3ctfnsuxfvzjn",
        "transformation:mtjxqc3zc4evy1ph73km",
        "transformation:zjc4edn6oxpq7xhr3752"
    ]
    transformations = TRANSFORMATION_IDS if enable_insights else []

    total_count = 0
    uploaded_count = 0
    skipped_count = 0
    updated_count = 0
    failed_count = 0

    for filename in os.listdir(directory):
        if filename.lower().endswith(extensions):
            total_count += 1
            file_path = os.path.join(directory, filename)
            local_hash = calculate_sha256(file_path)
            
            # --- 核心檢查邏輯 ---
            if filename in existing_sources:
                source_id = existing_sources[filename]
                
                # 如果能找到實體檔案，比對內容
                is_same = False
                if uploads_dir:
                    remote_file_path = os.path.join(uploads_dir, filename)
                    if os.path.exists(remote_file_path):
                        remote_hash = calculate_sha256(remote_file_path)
                        if local_hash == remote_hash:
                            is_same = True
                
                if is_same:
                    # print(f"  [跳過] {filename} (內容一致)")
                    skipped_count += 1
                    continue
                else:
                    # 內容不同或無法檢查內容，準備更新 (刪除舊的)
                    if not dry_run:
                        print(f"  [更新] {filename} (內容已變動)，正在刪除舊版本...")
                        delete_url = f"{BASE_URL}/sources/{source_id}?delete_exclusive_sources=true"
                        requests.delete(delete_url)
                    updated_count += 1
            
            # --- 執行上傳 ---
            if dry_run:
                print(f"  [模擬] 準備上傳: {filename}")
                uploaded_count += 1
                continue

            print(f"正在上傳: {filename}...")
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f)}
                    data = {
                        'type': 'upload', 'title': filename, 'embed': 'true',
                        'notebooks': json.dumps([notebook_id]),
                        'transformations': json.dumps(transformations)
                    }
                    response = requests.post(url, data=data, files=files)
                    if response.status_code == 200:
                        uploaded_count += 1
                    else:
                        print(f"失敗: {filename}，狀態碼: {response.status_code}")
                        failed_count += 1
            except Exception as e:
                print(f"上傳錯誤 {filename}: {e}")
                failed_count += 1
    
    print("-" * 30)
    print(f"上傳摘要:")
    print(f"  總處理: {total_count} | 上傳: {uploaded_count} | 更新: {updated_count} | 跳過: {skipped_count} | 失敗: {failed_count}")
    print("-" * 30)


def clear_notebook(notebook_id):
    """清除指定筆記本內的所有 Source 並刪除實體檔案"""
    list_url = f"{BASE_URL}/sources?notebook_id={notebook_id}"
    try:
        # 1. 取得該筆記本內的所有來源
        response = requests.get(list_url)
        if response.status_code != 200:
            print(f"無法取得來源列表: {response.text}")
            return
        
        sources = response.json()
        if not sources:
            print("該筆記本內沒有任何來源。")
            return

        print(f"找到 {len(sources)} 個來源，準備開始刪除...")
        
        # 2. 逐一刪除
        for source in sources:
            source_id = source['id']
            title = source.get('title', '未命名')
            print(f"正在刪除: {title} ({source_id})...")
            
            # 使用 DELETE 端點，並設定 delete_exclusive_sources=true 以刪除實體檔案
            delete_url = f"{BASE_URL}/sources/{source_id}?delete_exclusive_sources=true"
            del_resp = requests.delete(delete_url)
            
            if del_resp.status_code == 200:
                print(f"成功刪除: {title}")
            else:
                print(f"刪除失敗: {title}，狀態碼: {del_resp.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器，請確認服務是否已啟動。(錯誤詳細資訊: {e})")
    except Exception as e:
        print(f"執行清除時發生錯誤: {e}")

def get_status():
    """取得系統狀態"""
    try:
        auth = requests.get(f"{BASE_URL}/auth/status").json()
        env = requests.get(f"{BASE_URL}/credentials/env-status").json()
        print(f"Auth Status: {auth}")
        print(f"Env Status: {env}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器，請確認服務是否已啟動。(錯誤詳細資訊: {e})")
    except Exception as e:
        print(f"無法取得狀態: {e}")

def search_query(query, notebook_id=None, limit=5):
    """執行知識庫搜尋，支援筆記本篩選"""
    print(f"🔍 使用模型: {get_model_name_by_id(DEFAULT_EMBEDDING_MODEL)}")
    payload = {"query": query, "limit": limit}
    # 若有指定 notebook_id，傳遞 context 參數以進行限制
    if notebook_id:
        payload["context"] = {"notebook_id": notebook_id}
        
    try:
        response = requests.post(f"{BASE_URL}/search", json=payload)
        if response.status_code == 200:
            results = response.json().get('results', [])
            for i, res in enumerate(results):
                print(f"[{i+1}] {res.get('title', '無標題')}")
        else:
            print(f"搜尋失敗: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器，請確認服務是否已啟動。(錯誤詳細資訊: {e})")

def ask_query(query, notebook_id=None):
    """直接詢問知識庫問題，修正結構以符合 API 要求並處理串流回應"""
    # 使用系統註冊的語言模型 ID (優先使用環境變數設定的 DEFAULT_CHAT_MODEL)
    model_id = DEFAULT_CHAT_MODEL
    print(f"🤖 使用模型: {get_model_name_by_id(model_id)}")
    
    # 組合 System Prompt 與使用者的問題
    full_question = query
    if DEFAULT_SYSTEM_PROMPT:
        full_question = f"{DEFAULT_SYSTEM_PROMPT}\n\n使用者問題：{query}"

    payload = {
        "question": full_question,
        "strategy_model": model_id,
        "answer_model": model_id,
        "final_answer_model": model_id
    }
    if notebook_id:
        payload["notebook_id"] = notebook_id
        
    try:
        # 使用 stream=True 來處理串流
        response = requests.post(f"{BASE_URL}/search/ask", json=payload, stream=True)
        
        if response.status_code == 200:
            print("💡 系統思考中...", end="", flush=True)
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        try:
                            data = json.loads(line_str[6:])
                            # 顯示思考狀態
                            if data.get("type") == "strategy":
                                print(".", end="", flush=True)
                            # 處理最終回答內容，使用 flush=True 強制即時輸出
                            if data.get("type") == "answer":
                                print(data.get("content", ""), end="", flush=True)
                        except json.JSONDecodeError:
                            continue
            print() # 結束時換行
        else:
            print(f"提問失敗 (狀態碼 {response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器，請確認服務是否已啟動。(錯誤詳細資訊: {e})")

def raw_chat(message):
    """直接與 LM Studio 串流對話，繞過 Open Notebook 的 Orchestrator"""
    payload = {
        "model": "gemma-4-e4b-it",
        "messages": [{"role": "user", "content": message}],
        "stream": True
    }
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, stream=True)
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8').replace("data: ", "")
                    if line_str == "[DONE]": break
                    try:
                        data = json.loads(line_str)
                        content = data['choices'][0]['delta'].get('content', '')
                        print(content, end="", flush=True)
                    except: continue
            print()
        else:
            print(f"對話失敗: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器 (LM Studio)，請確認服務是否已啟動。(錯誤詳細資訊: {e})")

def chat_execute(session_id, message):
    """執行聊天"""
    print(f"💬 使用模型: {get_model_name_by_id(DEFAULT_CHAT_MODEL)}")

    # 組合 System Prompt 與使用者的訊息
    full_message = message
    if DEFAULT_SYSTEM_PROMPT:
        full_message = f"{DEFAULT_SYSTEM_PROMPT}\n\n使用者訊息：{message}"

    payload = {"session_id": session_id, "message": full_message, "context": {}}
    try:
        response = requests.post(f"{BASE_URL}/chat/execute", json=payload)
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"對話失敗: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"無法連線至後端伺服器，請確認服務是否已啟動。(錯誤詳細資訊: {e})")


def main():
    parser = argparse.ArgumentParser(description="Open Notebook CLI")
    subparsers = parser.add_subparsers(dest="command")

    # 列出指令
    list_parser = subparsers.add_parser("list", help="列出不同標的 (models, notebooks, sources)")
    list_parser.add_argument("--model", action="store_true", help="列出可用的模型")
    list_parser.add_argument("--notebook", action="store_true", help="列出所有筆記本")
    list_parser.add_argument("--source", help="指定筆記本 ID，列出其所有的 Source (若不指定則列出所有 Source)", nargs='?', const=True)

    # 系統狀態指令
    subparsers.add_parser("status", help="系統狀態")
    
    # 上傳指令
    upload_parser = subparsers.add_parser("upload", help="批次上傳檔案")
    upload_parser.add_argument("dir", help="包含檔案的目錄路徑")
    upload_parser.add_argument("notebook_id", help="目標筆記本 ID")
    upload_parser.add_argument("--enable-insights", action="store_true", help="啟用自動產生 Insights (分析時間較長)")
    upload_parser.add_argument("--dry-run", action="store_true", help="模擬上傳過程，不實際發送請求")

    # 清除指令
    clear_parser = subparsers.add_parser("clear", help="清除指定筆記本內的所有 Source")
    clear_parser.add_argument("notebook_id", help="要清空的筆記本 ID")

    # 搜尋指令
    search_parser = subparsers.add_parser("search", help="搜尋知識庫")
    search_parser.add_argument("query", help="搜尋關鍵字")
    search_parser.add_argument("--notebook", help="指定筆記本 ID", required=False)

    # 詢問指令
    ask_parser = subparsers.add_parser("ask", help="詢問知識庫問題")
    ask_parser.add_argument("query", help="問題內容")
    ask_parser.add_argument("--notebook", help="指定筆記本 ID", required=False)
    
    # 對話指令
    chat_parser = subparsers.add_parser("chat", help="進行對話")
    chat_parser.add_argument("session_id", help="會話 ID")
    chat_parser.add_argument("message", help="對話內容")
    
    # 直接串流聊天指令
    raw_chat_parser = subparsers.add_parser("raw-chat", help="直接與 LM Studio 串流對話")
    raw_chat_parser.add_argument("message", help="對話內容")

    args = parser.parse_args()

    if args.command == "list":
        if args.model:
            list_models()
        elif args.notebook:
            list_notebooks()
        elif args.source:
            # 如果 args.source 是 True (即使用者只帶了 --source 沒給 ID)
            nb_id = args.source if isinstance(args.source, str) else None
            list_sources(nb_id)
        else:
            list_parser.print_help()
            sys.exit(1)
    elif args.command == "status":
        get_status()
    elif args.command == "upload":
        upload_files(args.dir, args.notebook_id, args.enable_insights, args.dry_run)
    elif args.command == "clear":
        confirm = input(f"確定要清空筆記本 {args.notebook_id} 內的所有檔案嗎？(y/N): ")
        if confirm.lower() == 'y':
            clear_notebook(args.notebook_id)
        else:
            print("已取消操作。")
    elif args.command == "search":
        search_query(args.query, notebook_id=args.notebook)
    elif args.command == "ask":
        ask_query(args.query, notebook_id=args.notebook)
    elif args.command == "chat":
        chat_execute(args.session_id, args.message)
    elif args.command == "raw-chat":
        raw_chat(args.message)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
