import os
import argparse
import json
import requests
import sys

# 基礎 API 設定
BASE_URL = "http://localhost:5055/api"
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

def list_notebooks():
    """列出所有筆記本的 ID 與名稱"""
    try:
        response = requests.get(f"{BASE_URL}/notebooks")
        if response.status_code == 200:
            notebooks = response.json()
            print(f"{'ID':<30} | {'Name'}")
            print("-" * 50)
            for nb in notebooks:
                print(f"{nb['id']:<30} | {nb['name']}")
        else:
            print(f"無法取得筆記本列表，狀態碼: {response.status_code}")
    except Exception as e:
        print(f"連線錯誤: {e}")

def upload_files(directory, notebook_id, enable_insights):
    """上傳目錄下的檔案到指定筆記本"""
    url = f"{BASE_URL}/sources"
    extensions = ('.pdf', '.txt', '.md')
    
    if not os.path.exists(directory):
        print(f"錯誤: 目錄 {directory} 不存在")
        return

    # 指定的 Transformation IDs
    TRANSFORMATION_IDS = [
        "transformation:r81jle14ok5pqhhaf9v9",
        "transformation:6xjan1bdex95n9qj8fg7",
        "transformation:i67qf0y3ctfnsuxfvzjn",
        "transformation:mtjxqc3zc4evy1ph73km",
        "transformation:zjc4edn6oxpq7xhr3752"
    ]
    # 預設不執行，除非 enable_insights 為 True
    transformations = TRANSFORMATION_IDS if enable_insights else []

    for filename in os.listdir(directory):
        if filename.lower().endswith(extensions):
            file_path = os.path.join(directory, filename)
            
            print(f"正在上傳: {filename} (Insights: {'啟用' if enable_insights else '關閉'})...")
            
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f)}
                    data = {
                        'type': 'upload',
                        'title': filename,
                        'embed': 'true',
                        'notebooks': json.dumps([notebook_id]),
                        'transformations': json.dumps(transformations)
                    }
                    
                    response = requests.post(url, data=data, files=files)
                    if response.status_code == 200:
                        print(f"成功: {filename} 已上傳。")
                    else:
                        print(f"失敗: {filename}，狀態碼: {response.status_code}，回應: {response.text}")
            except Exception as e:
                print(f"上傳發生錯誤 {filename}: {e}")

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
    except Exception as e:
        print(f"執行清除時發生錯誤: {e}")

def get_status():
    """取得系統狀態"""
    try:
        auth = requests.get(f"{BASE_URL}/auth/status").json()
        env = requests.get(f"{BASE_URL}/credentials/env-status").json()
        print(f"Auth Status: {auth}")
        print(f"Env Status: {env}")
    except Exception as e:
        print(f"無法取得狀態: {e}")

def search_query(query, notebook_id=None, limit=5):
    """執行知識庫搜尋，支援筆記本篩選"""
    payload = {"query": query, "limit": limit}
    # 若有指定 notebook_id，傳遞 context 參數以進行限制
    if notebook_id:
        payload["context"] = {"notebook_id": notebook_id}
        
    response = requests.post(f"{BASE_URL}/search", json=payload)
    if response.status_code == 200:
        results = response.json().get('results', [])
        for i, res in enumerate(results):
            print(f"[{i+1}] {res.get('title', '無標題')}")
    else:
        print(f"搜尋失敗: {response.text}")

def ask_query(query, notebook_id=None):
    """直接詢問知識庫問題，修正結構以符合 API 要求並處理串流回應"""
    # 使用系統註冊的語言模型 ID
    model_id = "model:jlozhpea95y964fq5tb0"
    payload = {
        "question": query,
        "strategy_model": model_id,
        "answer_model": model_id,
        "final_answer_model": model_id
    }
    if notebook_id:
        payload["notebook_id"] = notebook_id
        
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

def raw_chat(message):
    """直接與 LM Studio 串流對話，繞過 Open Notebook 的 Orchestrator"""
    payload = {
        "model": "gemma-4-e4b-it",
        "messages": [{"role": "user", "content": message}],
        "stream": True
    }
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

def chat_execute(session_id, message):
    """執行聊天"""
    payload = {"session_id": session_id, "message": message, "context": {}}
    response = requests.post(f"{BASE_URL}/chat/execute", json=payload)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"對話失敗: {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Open Notebook CLI")
    subparsers = parser.add_subparsers(dest="command")

    # 列出筆記本指令
    subparsers.add_parser("list", help="列出所有筆記本 ID")

    # 系統狀態指令
    subparsers.add_parser("status", help="系統狀態")
    
    # 上傳指令
    upload_parser = subparsers.add_parser("upload", help="批次上傳檔案")
    upload_parser.add_argument("dir", help="包含檔案的目錄路徑")
    upload_parser.add_argument("notebook_id", help="目標筆記本 ID")
    upload_parser.add_argument("--enable-insights", action="store_true", help="啟用自動產生 Insights (分析時間較長)")

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
        list_notebooks()
    elif args.command == "status":
        get_status()
    elif args.command == "upload":
        upload_files(args.dir, args.notebook_id, args.enable_insights)
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
