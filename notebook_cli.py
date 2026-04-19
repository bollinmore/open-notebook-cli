import os
import argparse
import json
import requests
import sys

def list_notebooks():
    """列出所有筆記本的 ID 與名稱"""
    try:
        response = requests.get("http://localhost:5055/api/notebooks")
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
    url = "http://localhost:5055/api/sources"
    extensions = ('.pdf', '.txt', '.md')
    
    if not os.path.exists(directory):
        print(f"錯誤: 目錄 {directory} 不存在")
        return

    TRANSFORMATION_IDS = [
        "transformation:r81jle14ok5pqhhaf9v9",
        "transformation:6xjan1bdex95n9qj8fg7",
        "transformation:i67qf0y3ctfnsuxfvzjn",
        "transformation:mtjxqc3zc4evy1ph73km",
        "transformation:zjc4edn6oxpq7xhr3752"
    ]
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
    list_url = f"http://localhost:5055/api/sources?notebook_id={notebook_id}"
    
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
            delete_url = f"http://localhost:5055/api/sources/{source_id}?delete_exclusive_sources=true"
            del_resp = requests.delete(delete_url)
            
            if del_resp.status_code == 200:
                print(f"成功刪除: {title}")
            else:
                print(f"刪除失敗: {title}，狀態碼: {del_resp.status_code}")

    except Exception as e:
        print(f"執行清除時發生錯誤: {e}")

def main():
    parser = argparse.ArgumentParser(description="Open Notebook 批次管理工具")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="列出所有筆記本 ID")

    upload_parser = subparsers.add_parser("upload", help="批次上傳檔案")
    upload_parser.add_argument("dir", help="包含檔案的目錄路徑")
    upload_parser.add_argument("notebook_id", help="目標筆記本 ID")
    upload_parser.add_argument("--enable-insights", action="store_true", help="啟用自動產生 Insights")

    clear_parser = subparsers.add_parser("clear", help="清除指定筆記本內的所有 Source")
    clear_parser.add_argument("notebook_id", help="要清空的筆記本 ID")

    args = parser.parse_args()

    if args.command == "list":
        list_notebooks()
    elif args.command == "upload":
        upload_files(args.dir, args.notebook_id, args.enable_insights)
    elif args.command == "clear":
        confirm = input(f"確定要清空筆記本 {args.notebook_id} 內的所有檔案嗎？(y/N): ")
        if confirm.lower() == 'y':
            clear_notebook(args.notebook_id)
        else:
            print("已取消操作。")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
