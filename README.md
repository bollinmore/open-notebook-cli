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

所有指令透過 `uv run notebook_cli.py` 執行。

### 1. 系統狀態與筆記本管理
- **列出所有筆記本**:
  ```bash
  uv run notebook_cli.py list
  ```
- **檢查系統狀態**:
  ```bash
  uv run notebook_cli.py status
  ```

### 2. 檔案管理 (批次上傳與清除)
- **批次上傳檔案**:
  將檔案放置於指定目錄（支援 `.pdf`, `.txt`, `.md`）。
  ```bash
  # 預設僅上傳與索引
  uv run notebook_cli.py upload ./path/to/files "notebook_id"
  
  # 上傳並自動執行 AI 分析 (Insights)
  uv run notebook_cli.py upload ./path/to/files "notebook_id" --enable-insights
  ```
- **清空筆記本**:
  刪除指定筆記本內的所有來源與實體檔案。
  ```bash
  uv run notebook_cli.py clear "notebook_id"
  ```

### 3. 知識庫搜尋與提問
- **搜尋知識庫**:
  ```bash
  # 全域搜尋
  uv run notebook_cli.py search "關鍵字"
  
  # 指定筆記本搜尋
  uv run notebook_cli.py search "關鍵字" --notebook "notebook_id"
  ```
- **直接提問 (Ask)**:
  ```bash
  # 全域提問
  uv run notebook_cli.py ask "您的問題"
  
  # 指定筆記本提問
  uv run notebook_cli.py ask "您的問題" --notebook "notebook_id"
  ```

### 4. 聊天互動
- **執行對話**:
  ```bash
  uv run notebook_cli.py chat "session_id" "訊息內容"
  ```

---
*註：若要取得筆記本 ID，請先使用 `list` 指令查詢。*
