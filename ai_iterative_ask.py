import os
import subprocess
import sys
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

# NVIDIA NIM 標準端點
NIM_BASE_URL = config.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
# 如果 URL 結尾沒有 /v1，補上它 (視情況而定，但 integrate.api.nvidia.com/v1 是標準的)
NIM_API_ENDPOINT = f"{NIM_BASE_URL.rstrip('/')}/chat/completions"

# 預設模型改為 Meta Llama 3，這是 NVIDIA NIM 常見的預設模型
NIM_MODEL_ID = config.get("NIM_MODEL_ID", "meta/llama-3.1-405b-instruct") 

NIM_HEADERS = {
    "Authorization": f"Bearer {NIM_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_ai_next_step(history, turn, max_turns):
    """
    根據對話歷史，使用 NVIDIA NIM API 決定下一個問題或進行總結。
    """
    conversation_messages = []
    # 建立對話內容
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
        "max_tokens": 1024,
        "top_p": 1
    }

    try:
        # print(f"DEBUG: 正在請求 {NIM_API_ENDPOINT}")
        response = requests.post(NIM_API_ENDPOINT, headers=NIM_HEADERS, json=payload, timeout=60)
        response.raise_for_status()
        res_json = response.json()
        return res_json['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"AI 產生內容失敗: {str(e)}"

def call_notebook_cli(question):
    """
    執行 ./notebook-cli.sh ask "XXX"
    """
    print(f"\n[執行指令] ./notebook-cli.sh ask \"{question}\"")
    
    try:
        result = subprocess.run(
            ["./notebook-cli.sh", "ask", question],
            capture_output=True, text=True, check=True, timeout=120
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"錯誤：CLI 執行失敗\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
    except Exception as e:
        return f"錯誤：{str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python ai_iterative_ask.py \"初始問題\" 最大回合數")
        sys.exit(1)

    current_q = sys.argv[1]
    try:
        max_turns = int(sys.argv[2])
    except ValueError:
        print("錯誤：回合數必須是整數")
        sys.exit(1)

    history = []

    print(f"=== NVIDIA NIM 疊代任務開始 (上限 {max_turns} 回合) ===")

    for turn in range(1, max_turns + 1):
        print(f"\n>>> 回合 {turn}/{max_turns}")
        
        answer = call_notebook_cli(current_q)
        print(f"[回答]: {answer}")
        
        history.append({"q": current_q, "a": answer})
        
        if turn < max_turns:
            print("AI 正在思考下一個問題...")
            current_q = get_ai_next_step(history, turn, max_turns)
        else:
            print("\n>>> 正在產生最終總結...")
            summary = get_ai_next_step(history, turn, max_turns)
            print("\n--- 最終總結 ---")
            print(summary)
            break

    print("\n[任務完成]")
