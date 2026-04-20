# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
