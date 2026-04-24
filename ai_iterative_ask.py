import os
import subprocess
import sys
import re
import requests
from dotenv import dotenv_values

# --- 1. 從 .env 或環境變數載入配置 ---
config = dotenv_values(".env")
if not config:
    config = os.environ

NIM_API_KEY = config.get("NVIDIA_NIM_API_KEY")
if not NIM_API_KEY:
    print("錯誤：請先在 .env 檔案或環境變數中設定 NVIDIA_NIM_API_KEY", file=sys.stderr)
    sys.exit(1)

NIM_BASE_URL = config.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_ENDPOINT = f"{NIM_BASE_URL.rstrip('/')}/chat/completions"
NIM_MODEL_ID = config.get("NIM_MODEL_ID", "meta/llama-3.1-405b-instruct") 

NIM_HEADERS = {
    "Authorization": f"Bearer {NIM_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_source_mapping():
    """
    抓取所有筆記本的來源，建立完整的 ID 與名稱對照表。
    """
    mapping = {}
    try:
        # 1. 取得所有筆記本 ID
        nb_result = subprocess.run(
            ["./notebook-cli.sh", "list", "--notebook"],
            capture_output=True, text=True, check=True
        )
        notebook_ids = [line.split('|')[0].strip() for line in nb_result.stdout.strip().split('\n') if '|' in line and 'ID' not in line and '---' not in line]

        # 2. 針對每個筆記本取得來源
        for nb_id in notebook_ids:
            src_result = subprocess.run(
                ["./notebook-cli.sh", "list", "--source", nb_id],
                capture_output=True, text=True, check=True
            )
            for line in src_result.stdout.strip().split('\n'):
                if '|' not in line or 'ID' in line or '---' in line: continue
                parts = line.split('|', 1)
                raw_id = parts[0].strip()
                title = parts[1].strip()
                
                clean_id = raw_id.replace("source:", "")
                mapping[raw_id] = title
                mapping[clean_id] = title
                mapping[f"source:{clean_id}"] = title
                
        return mapping
    except Exception:
        return {}

def replace_source_ids(text, mapping):
    """
    替換文本中的來源標記。若找不到名稱，則保留原始標記以確保準確性。
    """
    def replacer(match):
        full_match = match.group(0) # [source:ID] 或 [ID]
        content = match.group(1).strip() # source:ID 或 ID
        
        # 嘗試找出乾淨的 ID
        clean_id = content.replace("source:", "")
        
        # 從對照表中尋找（嘗試三種可能的 key 組合）
        name = mapping.get(content) or mapping.get(clean_id) or mapping.get(f"source:{clean_id}")
        
        if name:
            return f"[{name}]"
        # 找不到就維持原樣，不進行 AI 猜測
        return full_match

    # 寬鬆匹配中括號內的標記，涵蓋 15-35 位元的英數 ID (可能帶 source: 前綴)
    pattern = r'\[(source:[a-z0-9]+|[a-z0-9]{15,35})\]'
    return re.sub(pattern, replacer, text)

def get_ai_next_step(history, turn, max_turns):
    conversation_messages = []
    for h in history:
        conversation_messages.append({"role": "user", "content": h['q']})
        conversation_messages.append({"role": "assistant", "content": h['a']})

    if turn < max_turns:
        prompt_text = f"目前是第 {turn} 回合，總上限為 {max_turns} 回合。請根據上述對話內容，提出一個後續的、具備深度且相關的問題。只需要回傳問題字串，不要有任何其他解釋或前導詞。"
    else:
        prompt_text = "這是最後一輪。請針對以上所有回答內容做一個簡潔、清晰且有價值的總結。只需要回傳總結內容，不要有任何其他解釋或前導詞。"
    
    conversation_messages.append({"role": "user", "content": prompt_text})
    payload = {
        "model": NIM_MODEL_ID,
        "messages": conversation_messages,
        "temperature": 0.5,
        "max_tokens": 1024
    }

    try:
        response = requests.post(NIM_API_ENDPOINT, headers=NIM_HEADERS, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"AI 產生內容失敗: {str(e)}"

def call_notebook_cli(question, mapping):
    print(f"\n[執行指令] ./notebook-cli.sh ask \"{question}\"")
    try:
        result = subprocess.run(
            ["./notebook-cli.sh", "ask", question],
            capture_output=True, text=True, check=True, timeout=120
        )
        return replace_source_ids(result.stdout.strip(), mapping)
    except Exception as e:
        return f"錯誤：{str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python ai_iterative_ask.py \"初始問題\" 最大回合數")
        sys.exit(1)

    initial_q = sys.argv[1]
    max_turns = int(sys.argv[2])

    print("正在掃描所有筆記本來源...")
    source_mapping = get_source_mapping()
    
    history = []
    current_q = initial_q

    for turn in range(1, max_turns + 1):
        print(f"\n>>> 回合 {turn}/{max_turns}")
        answer = call_notebook_cli(current_q, source_mapping)
        print(f"[回答]: {answer}")
        
        history.append({"q": current_q, "a": answer})
        if turn < max_turns:
            print("AI 正在思考下一輪問題...")
            current_q = get_ai_next_step(history, turn, max_turns)
        else:
            print("\n>>> 正在產生最終總結...")
            summary = get_ai_next_step(history, turn, max_turns)
            print(f"\n--- 最終總結 ---\n{summary}")
            break
