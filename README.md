# VLC Control for Indigo

Control and monitor VLC media player on the Mac running Indigo.

**Repository source version: 1.0.1.** The checked-in plugin uses AppleScript through macOS `osascript`. It does **not** contain the HTTP-based 2.1.0 implementation described in the existing changelog. If you use a newer HTTP-based build, these instructions do not apply to that build.

## Requirements

- A Mac running Indigo with Python 3 plugin support (the plugin declares Server API 3.0).
- VLC installed on the same Mac as Indigo Server.
- Permission for the Indigo server process to control VLC and System Events through macOS Automation.
- Media accessible to the account running VLC.

Compatibility with specific Indigo, macOS, and VLC releases must be verified on the target system; this repository review did not include a live playback test.

## Installation

1. Choose **Code → Download ZIP** on this repository and expand the download.
2. Open the `vlc-control` folder.
3. Double-click `VLC.indigoPlugin` and accept Indigo's installation prompts.
4. Enable the plugin in Indigo; restart it if prompted.

There are currently no published GitHub releases. The repository also contains `VLC-Control-v1.0.1.zip`, but its contents have not been checked against the expanded source. Use the expanded source bundle above for the version documented here.

## VLC and macOS setup

1. Open VLC on the Indigo Server Mac.
2. Load a local audio/video file and confirm it plays normally.
3. Leave VLC running while testing Indigo.
4. Accept macOS prompts allowing the Indigo server process to control VLC and System Events.
5. If permission was denied, review **System Settings → Privacy & Security → Automation**. Older macOS versions place these settings under System Preferences.

This source version requires no VLC web interface, HTTP password, IP address, or port. It controls the local VLC application only.

## Create an Indigo device

1. In Indigo, create a new device.
2. Select the **VLC Control** plugin and **VLC Player** model.
3. Configure:

| Setting | Function |
| --- | --- |
| Update Frequency | Poll every 0.5, 1, 2, 5, or 10 seconds; default 1 second. Start with 5 seconds to reduce repeated AppleScript calls. |
| Update Indigo Variables | Optionally copy device states into Indigo variables. |
| Variable Prefix | Default `VLC`; for example, `VLCMediaName` and `VLCIsPlaying`. |

4. Save the device and inspect its states.
5. Run **Update Now** to request a fresh status reading.

All devices created with this version address the same local VLC application. Creating additional Indigo devices does not provide separate zones or network VLC instances. Use distinct variable prefixes if enabling variables on multiple devices.

## Use actions

In an Indigo action group, schedule, trigger, or Control Page button, choose the VLC Control plugin action and select your VLC Player device. Exact menu wording varies by Indigo version.

| Actions | Purpose |
| --- | --- |
| Play, Pause, Play/Pause Toggle, Stop | Playback control |
| Next, Previous | Navigate VLC's loaded playlist |
| Set Volume, Volume Up, Volume Down | Adjust audio level; see limitations below |
| Mute, Unmute | Audio muting; see limitations below |
| Step Forward, Step Backward | Relative seeking; selectable step sizes are not implemented |
| Jump To Position | Seek to a position expressed in seconds |
| Set Fullscreen | On, off, or toggle |
| Set Loop, Set Random | On, off, or toggle |
| Open Media File | Open a path on the VLC Mac, such as `/Users/yourname/Movies/movie.mp4` |
| Open URL | Open a stream URL supported by VLC |
| Set Playback Rate | Choose 0.25, 0.5, 1, 1.5, or 2 times normal speed |
| Update Now | Refresh device states immediately |

Use plain numeric input for volume, amount, and position. These fields do not have comprehensive input validation.

### Example: play a local file

1. Create an action group in Indigo.
2. Add **Open Media File** for your VLC device.
3. Enter the file's absolute path.
4. Execute the action group and check playback in VLC.

Paths containing double quotes or backslashes can fail because the current code inserts paths directly into AppleScript strings.

### Example: Control Page

- Add buttons linked to action groups for Play/Pause Toggle, Stop, Next, and Previous.
- Display `mediaName` for the current title.
- Display `currentTimeFormatted` and `durationFormatted` for elapsed and total time.
- Use Set Volume for volume controls, accounting for the scaling limitation below.

### Example: trigger when playback starts

Create a device-state-change trigger for the VLC device's `isPlaying` state becoming true, then add your lighting or other actions.

State changes are detected by polling. Do not rely on `progressPercent = 100` as an end-of-media trigger: polling can miss the final position, and live streams may have no known duration.

## Device states

| State | Meaning |
| --- | --- |
| `playerState` | `playing`, `paused`, or `stopped`; pause/stop is inferred |
| `isPlaying`, `isPaused`, `isStopped` | Boolean playback indicators |
| `mediaName`, `mediaPath` | Current media title and path |
| `currentTime`, `duration` | Position and length in seconds |
| `currentTimeFormatted`, `durationFormatted` | Readable time values |
| `progressPercent` | Calculated percentage when duration is known |
| `audioVolume` | Raw value returned by VLC's AppleScript interface |
| `muted` | Reported mute status |
| `fullscreen`, `looping`, `random` | Reported playback options |
| `status` | Summary text shown on the Indigo device |

Optional Indigo variables capitalize the first letter of the state name and add the prefix: `mediaName` becomes `VLCMediaName`. Values are stored as strings; boolean values become `True` or `False`. Variables are created or updated after a successful status read.

## Known limitations in the checked-in source

- **HTTP version missing:** the changelog's 2.1.0 entry does not match `Info.plist`, device settings, or Python code.
- **Step-size selection is ignored:** every forward option issues the same AppleScript command, as do all backward options. The advertised 3-second, 10-second, 1-minute, and 5-minute choices are not implemented.
- **Mute acts as a toggle:** invoking Mute again can unmute VLC. Unmute relies on the last polled mute state.
- **Volume scales are inconsistent:** Set Volume converts 0–100 to 0–256, while the reported state is not converted back. Volume Up/Down repeat VLC commands rather than applying an exact percentage change.
- **Paused versus stopped is inferred:** nonplaying media with a nonempty name is classified as paused, which can misidentify a stopped item.
- **Metadata parsing is fragile:** AppleScript records are split on commas without accounting for quoted text. Media names or paths containing commas can be misread.
- **Failed polls can leave stale states:** status failures are logged rather than consistently marking the device offline.
- **AppleScript calls have no timeout:** an unresponsive macOS automation request can delay polling or actions.
- **Local control only:** no remote-host settings or independent multi-zone control are present.

These are source-review findings, not results of a live test on a Mac.

## Troubleshooting

### No updates or controls

- Confirm VLC is running on the same Mac as Indigo Server.
- Load a simple local file and verify VLC plays it directly.
- Review macOS Automation permissions for VLC and System Events.
- Execute Update Now and inspect Indigo's Event Log.
- Try a 5- or 10-second polling interval.

### Media information does not update

A VLC AppleScript property error can make the entire status request fail. Check the Indigo log, try a different local file, and avoid commas in the test filename to isolate record-parsing problems.

### Variables do not appear

Enable Update Indigo Variables and run Update Now. Variables are created only after a successful status read. Check the prefix and Indigo log for naming errors.

### File or stream will not open

Confirm the file exists and is readable by the VLC account, or test the stream URL directly in VLC. Avoid embedded double quotes and backslashes in action input until string escaping is fixed.

## Repository and release notes

The current plugin is located at:

`vlc-control/VLC.indigoPlugin`

Both `PluginVersion` and `CFBundleVersion` in its `Contents/Info.plist` are `1.0.1`. The identifier is currently `com.indigodomo.vlc`; preserve it for existing installations unless planning a deliberate identifier migration.

Before submitting a GitHub release to the Indigo Plugin Store:

1. Confirm the repository contains the intended working plugin source.
2. Align the changelog, README, and plist versions.
3. Create the release from the commit containing that version; for example, tag `v1.0.1` for `PluginVersion` `1.0.1`.
4. Check the **source archive at the release tag**, because replacing an attached plugin ZIP does not change the source archive.
5. Keep a README at repository root so it is present at the top level of GitHub's source archive.
6. Attach an installable plugin ZIP built from the same source.

No release was created as part of this documentation update.

## Support and license

Report problems through [GitHub Issues](https://github.com/Koreysherwin/indigo-vlc-control/issues). Include Indigo/macOS/VLC versions, the failing action, and relevant Indigo log entries. Remove private paths or stream credentials before posting.

See [LICENSE](vlc-control/LICENSE) and the [existing changelog](vlc-control/CHANGELOG.md). The nested README files are older documentation; use this root README for the checked-in 1.0.1 source.
