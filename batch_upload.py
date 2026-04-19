import os
import requests
import json

def upload_files(directory, notebook_id):
    url = "http://localhost:5055/api/sources"
    
    # 支援常見的 PDF 副檔名
    extensions = ('.pdf', '.txt', '.md')
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(extensions):
            file_path = os.path.join(directory, filename)
            
            print(f"正在上傳: {filename}...")
            
            # 準備 multipart 表單數據
            # 注意: API 需要 notebooks 參數為 JSON 字串
            files = {'file': (filename, open(file_path, 'rb'))}
            data = {
                'type': 'upload',
                'title': filename,
                'embed': 'true',
                'notebooks': json.dumps([notebook_id])
            }
            
            try:
                response = requests.post(url, data=data, files=files)
                if response.status_code == 200:
                    print(f"成功: {filename} 已上傳。")
                else:
                    print(f"失敗: {filename}，狀態碼: {response.status_code}，回應: {response.text}")
            except Exception as e:
                print(f"上傳發生錯誤 {filename}: {e}")

if __name__ == "__main__":
    # 設定目標目錄與筆記本 ID
    # 建議您修改為實際要批次上傳的目錄路徑
    TARGET_DIR = "./notebook_data/uploads" 
    TARGET_NOTEBOOK_ID = "notebook:uvdy8peo0tgi993zpmj1"
    
    upload_files(TARGET_DIR, TARGET_NOTEBOOK_ID)
