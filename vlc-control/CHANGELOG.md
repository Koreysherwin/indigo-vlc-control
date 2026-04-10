# Changelog

## Version 2.1.0
- Reworked the plugin to favor HTTP mode for normal operation.
- Removed the Connection Method choice from the device UI so HTTP mode is the primary path.
- Changed the default polling interval to 5 seconds.
- Removed the 0.5-second and 1-second polling options from the UI.
- Enforced a 2-second minimum polling interval in code.
- Left the legacy AppleScript code in place as dormant fallback logic, but shifted normal control and polling to HTTP mode.
- Reduced the risk of GUI/session instability caused by repeated AppleScript polling.

## [1.0.1] - 2025-01-09

### Fixed
- Fixed XML format compatibility with Indigo 2025

## [1.0.0] - 2025-01-09

### Added
- Initial release
- Complete playback control (play, pause, stop, next, previous)
- Volume control with mute/unmute
- Precision seeking with multiple step sizes (3s, 10s, 1m, 5m)
- Fullscreen control for home theater automation
- Loop and random/shuffle modes
- Open local media files or streaming URLs
- Variable playback speed (0.25x - 2.0x)
- Universal format support (all video/audio formats VLC supports)
- Real-time playback information monitoring
- Variable integration for Control Pages
