# Open Notebook CLI 工具

這是一個用於管理 [Open Notebook](https://github.com/lfnovo/open-notebook) 知識庫的自動化 CLI 工具。它支援批次上傳、知識庫查詢、系統狀態管理以及與 AI 對話。

## 環境設定

本專案使用 `uv` 進行套件管理。

1. **安裝依賴**:
   ```bash
   uv sync --no-editable
   ```

   在 macOS 上，`uv` 的 editable 安裝可能會產生帶有 `hidden` flag 的 `.pth` 檔，
   導致 `notebook-cli` 啟動時出現 `ModuleNotFoundError: No module named 'open_notebook'`。
   若要避免這個問題，請固定使用 `--no-editable`。

2. **確認 Docker 服務**:
   確保 `docker-compose.yml` 已啟動：
   ```bash
   docker compose up -d
   ```

## 使用方式

建議優先透過 repo 內的 wrapper script 執行：

```bash
./notebook-cli.sh --help
```

它會固定使用 `uv run --no-editable notebook-cli`，避免再次踩到 editable install 的匯入問題。

若需要，也可以直接使用：

### 1. 系統狀態與清單指令
- **列出標的 (筆記本/模型/來源)**:
  ```bash
  # 列出筆記本
  uv run --no-editable notebook-cli list --notebook
  
  # 列出所有模型
  uv run --no-editable notebook-cli list --model
  
  # 列出所有來源 (或指定筆記本的來源)
  uv run --no-editable notebook-cli list --source [notebook_id]
  ```
- **檢查系統狀態**:
  ```bash
  uv run --no-editable notebook-cli status
  ```

### 2. 檔案管理 (批次上傳與清除)
- **批次上傳檔案**:
  ```bash
  # 上傳並自動執行 AI 分析 (Insights)
  uv run --no-editable notebook-cli upload ./path/to/files "notebook_id" --enable-insights
  ```
- **清空筆記本**:
  ```bash
  uv run --no-editable notebook-cli clear "notebook_id"
  ```

### 3. 知識庫搜尋與提問
- **搜尋知識庫**:
  ```bash
  uv run --no-editable notebook-cli search "關鍵字" --notebook "notebook_id"
  ```
- **直接提問 (Ask)**:
  ```bash
  uv run --no-editable notebook-cli ask "您的問題" --notebook "notebook_id"
  ```

### 4. 聊天互動
- **執行對話**:
  ```bash
  uv run --no-editable notebook-cli chat "session_id" "訊息內容"
  ```

---
*註：若要取得筆記本或模型 ID，請使用 `list` 指令查詢。*

## AI 疊代提問工具

專案內包含一個自動化腳本 `ai_iterative_ask.py`，它能根據 `notebook-cli` 的回答，自動思考並產生後續問題，達成多輪深入探討。

### 設定方式

1. **安裝依賴**:
   ```bash
   pip install python-dotenv requests
   ```

2. **配置環境變數**:
   將 `.env.sample` 複製為 `.env` 並填入您的 NVIDIA NIM API Key：
   ```bash
   cp .env.sample .env
   # 編輯 .env 填入 NVIDIA_NIM_API_KEY
   ```

### 執行疊代提問

```bash
python ai_iterative_ask.py "您的初始問題" [最大回合數]
```

**範例**:
```bash
python ai_iterative_ask.py "請分析這個知識庫的主要內容" 3
```

該腳本會：
- 執行第一輪提問。
- 將回答傳給 NVIDIA NIM AI，產生下一個相關問題。
- 重複執行直到達到設定的回合上限。
- 最後一輪自動產生完整總結。
