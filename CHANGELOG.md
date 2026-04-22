# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-alpha.4] - 2026-04-22

### Added
- **System Prompt 支援**: 新增 `DEFAULT_SYSTEM_PROMPT` 環境變數，可在 `ask` 與 `chat` 指令前自動附加系統提示詞。
- **穩定啟動入口**: 新增 `notebook-cli.sh` wrapper script，固定以 `uv run --no-editable notebook-cli` 啟動 CLI。
- **封裝回歸測試**: 新增 `tests/test_packaging.py`，驗證 build backend 與 `src` package layout 設定。

### Changed
- **封裝設定明確化**: 補上 `build-system` 與 `requires-python`，固定使用 `hatchling` 建置並標明 Python 版本需求。
- **macOS 執行說明更新**: README 改為建議使用 `uv sync --no-editable`，避免 editable install 在 macOS 上觸發 `ModuleNotFoundError: No module named 'open_notebook'`。

## [0.1.0-alpha.3] - 2026-04-22

### Added
- **清單指令強化**: `list` 指令現在支援 `--model`、`--notebook` 與 `--source` 參數，並強制至少選擇一個子參數。
- **動態模型名稱**: `ask`、`search`、`chat` 指令現在會自動透過 API 查詢並顯示友善的模型名稱。
- **環境變數擴充**: 新增 `.env.sample` 範本，支援分別設定 Chat、Embedding、TTS 與 STT 的預設模型 ID。
- **自動化測試**: 引入 `pytest` 測試框架，並達成 50%+ 的指令邏輯覆蓋率。
- **CLI 封裝**: 新增 `notebook-cli` EntryPoint，現在可直接透過 `uv run notebook-cli` 執行。

### Changed
- **架構重組**: 
    - 採用 `src-layout` 結構（`src/open_notebook/`）。
    - 提取共用工具至 `utils.py`。
    - 測試檔案遷移至 `tests/`。
- **配置優化**: 升級 `pyproject.toml` 設定，整合 `hatchling` 建置後端，並透過 `tool.uv.sources` 解決開發環境路徑問題。

## [0.1.0-alpha.2] - 2026-04-20

### Added
- SHA256 verification for file uploads to prevent duplicate content processing.
- `--dry-run` flag for the `upload` command to simulate upload process.
- Upload summary report (total, success, skipped, failed counts).
- Automatic absolute path detection for the backup directory.

### Changed
- Improved upload feedback by hiding repetitive "skipped" messages and using a cleaner summary format.

## [0.1.0-alpha.1] - 2026-04-20

### Added
- `raw-chat` command for direct streaming chat with LM Studio.
- `ask` command with SSE stream parsing for knowledge base queries.
- `upload` command for batch file uploading with optional insights.
- `list` command to show available notebooks.
- `status` command to check system authentication and environment status.
- `clear` command to empty a notebook's sources.
- Comprehensive `README.md` with setup and usage instructions.
- Docker Compose configuration for SurrealDB and Open Notebook.

### Fixed
- Fixed model selection logic in `ask` command.
- Optimized streaming UX for real-time interaction.
