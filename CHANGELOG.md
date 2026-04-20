# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
