# Changelog

## 2.1.1

- Fix named playback-rate selections and accept numeric values.
- Honor On/Off/Toggle using live VLC state for fullscreen, loop, and random.
- Preserve exact volume across repeated Mute/Unmute actions.
- Report paused and stopped directly from VLC HTTP status.
- Include the VLC icon in the installable ZIP.


## 2.1.0

- Import the supplied working HTTP plugin, replacing the older repository source.
- Use HTTP for polling and actions, with a default 5-second polling interval and enforced 2-second minimum.
- Change the plugin identifier to com.sherwinsound.vlccontrol.
- Set the About/support URL to the repository Issues page.
- Add matching installation, configuration, migration, and usage instructions.
- Preserve existing playback code; known limitations are documented in README.md.

## 1.0.1

- Earlier AppleScript-based repository version.

