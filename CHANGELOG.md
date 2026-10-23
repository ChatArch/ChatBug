# Changelog

## Unreleased

## 0.1.0 - 2026-10-23

### Added

- Added the `chatbug php2shell web check <URL>` command for authorized ordinary-website PHP version exposure, benign multipart parser reachability, and fixed LFI marker controls.
- Added `chatbug php2shell lab local-list`, a dependency-free in-process positive/negative PHP session-inclusion reproduction for CI and documentation.
- Added `chatbug php2shell lab docker-list`, a data-free internal PHP-FPM/Nginx Docker lab that proves fixed allowlisted `ls/cat` actions only with an intentional lab-only include gadget.
- Added importable PHP2Shell HTTP, version-classification, payload, and lab-lifecycle Python APIs.
- Added bilingual documentation, a complete PHP2Shell reproduction guide, and CLI/Python interface trees.

### Changed

- Updated the package description from a reserved placeholder to an authorized website vulnerability-validation tool.
- Removed the unused `chatenv` dependency because ChatBug currently has no configuration provider.

### Security

- Production checks do not send OOM/UAF/crash payloads or execute commands.
- Docker reproduction uses an internal network, synthetic data only, no production volumes, no published host port, and automatic cleanup.
- Lab proof modes are restricted to a fixed allowlist; arbitrary remote command input is rejected.

## 0.0.2 - 2026-10-23

### Changed

- Release-only validation of the GitHub Trusted Publisher workflow; no package features were added.

## 0.0.1 - 2026-10-22

### Added

- Initial reserved package with the `chatbug` CLI version and tree surfaces.
