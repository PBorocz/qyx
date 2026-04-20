# Changelog

All notable changes to this project will be documented in this file.

Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and we try to adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-04-20

### Added
- Screenshots obo both CLI and web interfaces.

### Changed
- Removed right-nav hamburger until we have something real to put there!

### Fixed
- Ordering of report levels on respective CLI prompt.

## [0.2.7] - 2026-04-20

### Added
- Implemented `--version` flag using importlib.metadata.
- Created default config.yaml shipped with package to be installed in platformdirs user\_config\_dir on first run.
- Added nicer home icon to navbar.

### Changed
- Updated subprocess error logging to use platformdirs user\_log\_dir.
- Improved package distribution workflow with automated tasks.

### Fixed
- Fixed package installation paths using importlib.resources.
- Resolved uv.lock not being committed during push.
