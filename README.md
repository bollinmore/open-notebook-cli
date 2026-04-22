# Open Notebook CLI 工具

這是一個用於管理 [Open Notebook](https://github.com/lfnovo/open-notebook) 知識庫的自動化 CLI 工具。它支援批次上傳、知識庫查詢、系統狀態管理以及與 AI 對話。

## 環境設定

本專案使用 `uv` 進行套件管理。

1. **安裝依賴**:
   ```bash
   uv sync
   ```

2. **確認 Docker 服務**:
   確保 `docker-compose.yml` 已啟動：
   ```bash
   docker compose up -d
   ```

## 使用方式

建議直接透過 `uv run notebook-cli` 執行指令：

### 1. 系統狀態與清單指令
- **列出標的 (筆記本/模型/來源)**:
  ```bash
  # 列出筆記本
  uv run notebook-cli list --notebook
  
  # 列出所有模型
  uv run notebook-cli list --model
  
  # 列出所有來源 (或指定筆記本的來源)
  uv run notebook-cli list --source [notebook_id]
  ```
- **檢查系統狀態**:
  ```bash
  uv run notebook-cli status
  ```

### 2. 檔案管理 (批次上傳與清除)
- **批次上傳檔案**:
  ```bash
  # 上傳並自動執行 AI 分析 (Insights)
  uv run notebook-cli upload ./path/to/files "notebook_id" --enable-insights
  ```
- **清空筆記本**:
  ```bash
  uv run notebook-cli clear "notebook_id"
  ```

### 3. 知識庫搜尋與提問
- **搜尋知識庫**:
  ```bash
  uv run notebook-cli search "關鍵字" --notebook "notebook_id"
  ```
- **直接提問 (Ask)**:
  ```bash
  uv run notebook-cli ask "您的問題" --notebook "notebook_id"
  ```

### 4. 聊天互動
- **執行對話**:
  ```bash
  uv run notebook-cli chat "session_id" "訊息內容"
  ```

---
*註：若要取得筆記本或模型 ID，請使用 `list` 指令查詢。*
