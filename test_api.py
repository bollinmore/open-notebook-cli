import requests
import json

url = "http://localhost:5055/api/sources"
payload = {
    "type": "upload",
    "file_path": "/app/data/test.txt",
    "title": "Test Source",
    "embed": True,
    "async_processing": False
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
