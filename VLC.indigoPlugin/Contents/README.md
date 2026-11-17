# VLC Control for Indigo

Version **2.1.0** — control VLC playback and report media status through VLC's HTTP interface.

## Requirements

- Indigo 2022.1 or later (Server API 3.0), with Python 3.
- VLC with its HTTP web interface enabled and reachable from Indigo Server.
- Local files must be accessible on the computer running VLC.

## Install

1. Download [VLC-Control-v2.1.0.zip](VLC-Control-v2.1.0.zip) and unzip it.
2. Double-click **VLC.indigoPlugin** to install and enable it in Indigo.
3. Open VLC and configure its HTTP interface as below.

**Identifier change:** this build uses `com.sherwinsound.vlccontrol`, replacing `com.indigodomo.vlc`. Indigo treats these as different plugins. Disable the old plugin and recreate or reassign VLC devices and automation references as needed. Keep a backup of your Indigo database before migrating.

## Configure VLC

In VLC Preferences, select **Show All** to display advanced settings (wording varies by platform/version):

1. Under **Interface → Main interfaces**, enable **Web** / **HTTP**.
2. Under **Interface → Main interfaces → Lua**, set a **Lua HTTP password**.
3. Save preferences and restart VLC.
4. From the Indigo Server computer, open `http://localhost:8080/requests/status.json`. Use the VLC host address instead of localhost if VLC runs elsewhere.
5. When prompted, leave the username empty and enter the HTTP password. A successful connection displays JSON.

Use this interface on a trusted local network; it uses unencrypted HTTP. Do not forward its port to the internet.

## Create the Indigo device

Create a device using the **VLC Control** plugin and **VLC Player** model.

| Setting | Value |
| --- | --- |
| HTTP Host | `localhost` for VLC on the Indigo Mac; otherwise the VLC computer's hostname or IP |
| HTTP Port | `8080`, unless changed in VLC |
| HTTP Password | The Lua HTTP password set in VLC |
| Update Frequency | Default 5 seconds; code enforces a minimum of 2 seconds |
| Update Indigo Variables | Optional |
| Variable Prefix | Default `VLC` |

The menu still includes 0.5- and 1-second polling choices, but both run at the enforced 2-second minimum.

Save the device, load media in VLC, and execute **Update Now**. Each device can address a separately configured VLC HTTP endpoint.

## Use in Indigo

Choose a VLC Control action in an action group, trigger, schedule, or Control Page button and select your VLC device.

| Actions | Function |
| --- | --- |
| Play, Pause, Play/Pause Toggle, Stop | Playback control |
| Next, Previous | Navigate the playlist |
| Set Volume, Volume Up, Volume Down | Adjust the plugin's 0–100 volume scale |
| Mute, Unmute | Set volume to zero / restore remembered level (default 50 if unavailable) |
| Step Forward, Step Backward | Seek by 3, 10, 60, or 300 seconds |
| Jump To Position | Seek to a position in seconds |
| Set Fullscreen, Set Loop, Set Random | Toggle the corresponding option; see limitations |
| Open Media File | Play an absolute file path on the VLC computer |
| Open URL | Play a stream URL |
| Update Now | Refresh states immediately |

For example, create an action group with **Open Media File** and enter `/Users/yourname/Music/example.mp3`. For streams, use **Open URL** with the stream address.

For automation, trigger when `isPlaying` becomes true. For a Control Page, display `mediaName`, `currentTimeFormatted`, and `durationFormatted`, with buttons for Play/Pause Toggle and Stop.

## States and variables

States include `playerState`, `isPlaying`, `isPaused`, `isStopped`, `mediaName`, `mediaPath`, `currentTime`, `duration`, `currentTimeFormatted`, `durationFormatted`, `progressPercent`, `audioVolume`, `muted`, `fullscreen`, `looping`, `random`, and `status`.

Optional variables use an underscore: `VLC_mediaName`, `VLC_isPlaying`, etc. Values are strings. The code requests the **VLC Control** variable folder; if variable creation fails, check that folder and Indigo's Event Log.

## Current limitations

This repository preserves the supplied working 2.1.0 Python and XML files.

- Fullscreen, loop, and random actions toggle even when On or Off is selected.
- Set Playback Rate currently has a mismatch: the UI supplies named values such as `normal`, while the handler expects a numeric value. This action needs a code correction before use.
- Pause and stopped states are inferred from playback and media name, so a stopped loaded item can appear paused.
- `mediaPath` is taken from filename metadata and may not be a full path.
- Volume is mapped to VLC HTTP values 0–320; the plugin's percentage may differ from VLC's displayed percentage.
- Repeated Mute actions can replace the remembered volume with zero.
- HTTP failures are reported as VLC not running, including incorrect passwords or unreachable endpoints.
- End-of-media progress can be missed between polls; do not depend on reaching exactly 100%.

## Troubleshooting

- **VLC not running / no updates:** confirm VLC is open, Web/HTTP is enabled, the password matches, and the JSON URL works from Indigo Server.
- **HTTP 401:** check the Lua HTTP password and use an empty username.
- **Connection refused:** restart VLC after enabling Web and confirm its port.
- **Remote VLC:** check host address, firewall, and VLC HTTP access restrictions.
- **No variables:** enable variable updates, check the VLC Control variable folder, and review the Event Log.
- Enable debug logging in plugin configuration for HTTP error details. Remove credentials from logs before sharing.

## Support

[Report an issue](https://github.com/Koreysherwin/indigo-vlc-control/issues).

Plugin identifier: `com.sherwinsound.vlccontrol`. PluginVersion: `2.1.0`.

For Indigo Store releases, the release tag version must match PluginVersion in the source archive at that tag. Keep this README at repository root.

See [LICENSE](LICENSE).
