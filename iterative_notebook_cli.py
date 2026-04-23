import subprocess
import sys

def generate_next_question(previous_response: str, turn_number: int, max_turns: int) -> str:
    """
    這是一個佔位函數。在純 Python 腳本中，若不串接 OpenAI/Gemini API，
    難以實現真正的「AI 思考」。目前僅作為邏輯示範。
    """
    if turn_number < max_turns:
        return f"請根據先前的回答進一步詳細說明。(第 {turn_number + 1}/{max_turns} 回合)"
    return ""

def call_notebook_cli(question: str) -> str:
    """
    執行 ./notebook-cli.sh ask "XXX" 並回傳結果。
    """
    command = ["./notebook-cli.sh", "ask", question]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"執行錯誤！\n指令: {' '.join(command)}\n結束代碼: {e.returncode}\n標準輸出: {e.stdout}\n錯誤輸出: {e.stderr}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("錯誤：找不到 ./notebook-cli.sh，請確認檔案存在且具備執行權限。", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python iterative_notebook_cli.py \"初始問題\" 最大回合數", file=sys.stderr)
        sys.exit(1)

    current_question = sys.argv[1]
    try:
        max_turns = int(sys.argv[2])
    except ValueError:
        print("錯誤：最大回合數必須是整數。", file=sys.stderr)
        sys.exit(1)

    history = []

    print(f"=== 開始執行 (上限 {max_turns} 回合) ===\n")

    for turn in range(1, max_turns + 1):
        print(f"--- 第 {turn} 回合 ---")
        print(f"提問: {current_question}")
        
        response = call_notebook_cli(current_question)
        print(f"回應: {response[:100]}...\n") # 僅列印前100字避免過長
        
        history.append({"q": current_question, "a": response})

        if turn < max_turns:
            # 這裡在實際應用中應由 AI 產生，腳本目前只能產生固定追問
            current_question = generate_next_question(response, turn, max_turns)
        else:
            print("=== 已達到回合上限，準備總結 ===")
            break

    print("\n--- 互動紀錄與總結建議 ---")
    for i, entry in enumerate(history, 1):
        print(f"Q{i}: {entry['q']}")
        print(f"A{i}: {entry['a']}\n")

    print("請將上述紀錄貼回給 AI，我將為您進行最終總結。")
