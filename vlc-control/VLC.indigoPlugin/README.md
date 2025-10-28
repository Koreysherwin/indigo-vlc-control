# VLC Control Plugin for Indigo

A comprehensive Indigo plugin for controlling VLC media player and monitoring all playback data in real-time.

## Features

### Device States (Auto-Updated)
The plugin tracks and updates the following VLC information:

#### Playback Status
- **Player State**: playing, paused, or stopped
- **Is Playing**: Boolean indicator
- **Is Paused**: Boolean indicator  
- **Is Stopped**: Boolean indicator

#### Media Information
- **Media Name**: Current media file/stream name
- **Media Path**: Full path to current media file

#### Playback Position
- **Current Time**: Current position in seconds
- **Current Time (Formatted)**: Position as MM:SS or HH:MM:SS
- **Duration**: Media length in seconds
- **Duration (Formatted)**: Duration as MM:SS or HH:MM:SS
- **Progress Percentage**: Playback progress (0-100%)

#### Audio Settings
- **Audio Volume**: Current volume (0-100)
- **Muted**: Boolean mute status

#### Playback Options
- **Fullscreen**: Boolean fullscreen mode
- **Looping**: Boolean loop mode
- **Random**: Boolean random/shuffle mode

#### Display
- **Status**: Human-readable status (e.g., "▶ video.mp4")

### Actions

#### Playback Control
- **Play**: Start playback
- **Pause**: Pause playback
- **Play/Pause Toggle**: Toggle between play and pause
- **Stop**: Stop playback
- **Next**: Skip to next media in playlist
- **Previous**: Go to previous media in playlist

#### Volume Control
- **Set Volume**: Set specific volume level (0-100)
- **Volume Up**: Increase volume by specified amount
- **Volume Down**: Decrease volume by specified amount
- **Mute**: Mute audio
- **Unmute**: Unmute audio

#### Position Control
- **Step Forward**: Jump forward (extra short/short/medium/long)
  - Extra Short: 3 seconds
  - Short: 10 seconds
  - Medium: 1 minute
  - Long: 5 minutes
- **Step Backward**: Jump backward (extra short/short/medium/long)
- **Jump To Position**: Jump to specific second in media

#### Playback Options
- **Set Fullscreen**: Turn fullscreen on, off, or toggle
- **Set Loop**: Turn loop on, off, or toggle
- **Set Random**: Turn random/shuffle on, off, or toggle

#### Media Selection
- **Open Media File**: Open local media file by path
- **Open URL**: Open streaming URL (HTTP/HTTPS)

#### Playback Speed
- **Set Playback Rate**: Adjust playback speed
  - 0.25x (Very Slow)
  - 0.5x (Slow)
  - 1.0x (Normal)
  - 1.5x (Fast)
  - 2.0x (Very Fast)

#### Utility
- **Update Now**: Force immediate status update

## Installation

1. **Install VLC**: Ensure VLC media player is installed on your Mac
2. **Download** the `VLC.indigoPlugin` package
3. **Double-click** the plugin file to install in Indigo
4. **Restart** the Indigo server if prompted

## Setup

### Creating a VLC Device

1. In Indigo, go to **Devices** → **New...**
2. Set Type: **Plugin** → **VLC Control**
3. Select Model: **VLC Player**
4. Configure settings:
   - **Update Frequency**: How often to poll VLC (0.5-10 seconds)
   - **Update Indigo Variables**: Enable to create/update variables
   - **Variable Prefix**: Prefix for variable names (default: "VLC")

### Device Settings

#### Update Frequency
Choose how often the plugin checks VLC status:
- **0.5 seconds**: Smoothest updates, higher CPU usage
- **1 second**: Recommended for most uses
- **2-5 seconds**: Good for background monitoring
- **10 seconds**: Minimal CPU usage

#### Variable Updates
If enabled, the plugin will create and update Indigo variables with all VLC data:
- Variables are named: `{Prefix}{StateName}` (e.g., `VLCMediaName`)
- Useful for Control Pages and other integrations
- Variables are created automatically if they don't exist

## Usage Examples

### Basic Playback Control
```applescript
-- In Indigo Actions
Execute Action "VLC Player - Play"
Execute Action "VLC Player - Pause"
Execute Action "VLC Player - Next"
```

### Volume Control
```applescript
-- Set volume to 50%
Execute Action "VLC Player - Set Volume" with value "50"

-- Increase volume by 10
Execute Action "VLC Player - Volume Up" with value "10"

-- Mute/Unmute
Execute Action "VLC Player - Mute"
Execute Action "VLC Player - Unmute"
```

### Open Media
```applescript
-- Open a local file
Execute Action "VLC Player - Open Media File"
  File Path: "/Users/username/Movies/movie.mp4"

-- Open a streaming URL
Execute Action "VLC Player - Open URL"
  URL: "http://example.com/stream.m3u8"
```

### Position Control
```applescript
-- Jump forward 10 seconds
Execute Action "VLC Player - Step Forward"
  Step Size: "Short"

-- Jump to specific time (2 minutes = 120 seconds)
Execute Action "VLC Player - Jump To Position"
  Position: "120"
```

### Playback Options
```applescript
-- Toggle fullscreen
Execute Action "VLC Player - Set Fullscreen"
  Fullscreen State: "Toggle"

-- Enable looping
Execute Action "VLC Player - Set Loop"
  Loop State: "On"

-- Slow down playback
Execute Action "VLC Player - Set Playback Rate"
  Playback Rate: "0.5x (Slow)"
```

### Triggers Based on VLC State

Create triggers based on device state changes:
- Trigger when playback starts: `isPlaying` becomes `true`
- Trigger when media changes: `mediaName` changes
- Trigger when media finishes: `progressPercent` reaches 100
- Trigger when fullscreen enabled: `fullscreen` becomes `true`

### Control Page Examples

Add VLC controls to your Control Pages:
- Display current media: Use `status` state
- Display progress: Use `currentTimeFormatted` and `durationFormatted`
- Progress bar: Use `progressPercent` state
- Volume slider: Control via Set Volume action
- Play/Pause button: Use Play/Pause Toggle action

## Automation Ideas

### Home Theater Integration
```python
# When VLC starts playing, dim the lights and lower blinds
Trigger: Device State Changed
Device: VLC Player
State: "isPlaying" becomes true
Actions:
  - Dim living room lights to 10%
  - Close living room blinds
  - Turn on home theater mode

# When VLC enters fullscreen, turn off lights completely
Trigger: Device State Changed
Device: VLC Player  
State: "fullscreen" becomes true
Actions:
  - Turn off all living room lights
```

### Auto-Pause for Doorbell
```python
# Pause VLC when doorbell rings
Trigger: Doorbell pressed
Actions:
  - Execute Action "VLC Player - Pause"
  - Wait 30 seconds
  - Execute Action "VLC Player - Play" (auto-resume)
```

### Sleep Timer
```python
# Schedule to stop VLC at bedtime
Schedule: 11:00 PM every day
Conditions: If VLC is playing
Actions:
  - Execute Action "VLC Player - Stop"
  - Display notification "VLC stopped for bedtime"
```

### Media Progress Notifications
```python
# Notify when long video/movie is almost done
Trigger: Device State Changed
Device: VLC Player
State: "progressPercent" becomes greater than 95
Conditions: "duration" greater than 3600 (1 hour)
Actions:
  - Send notification "Movie almost finished!"
```

## Scripting Examples

### Python Script
```python
# Get current media info
vlc_dev = indigo.devices[12345]  # Your device ID
media = vlc_dev.states['mediaName']
progress = vlc_dev.states['progressPercent']
indigo.server.log(f"Now playing: {media} ({progress}% complete)")

# Control playback
indigo.device.execute("VLC Player", action="play")
indigo.device.execute("VLC Player", action="next")

# Open a file
indigo.device.execute("VLC Player", action="openMedia", 
                     props={"mediaPath": "/Users/me/Videos/movie.mp4"})
```

### AppleScript
```applescript
tell application "IndigoServer"
    -- Get current media
    set mediaName to value of state "mediaName" of device "VLC Player"
    
    -- Execute actions
    execute action "Play/Pause Toggle" of device "VLC Player"
    
    -- Check if playing
    set isPlaying to value of state "isPlaying" of device "VLC Player"
end tell
```

## Troubleshooting

### Plugin Not Updating
- Ensure VLC is installed and running
- Check that Update Frequency is set appropriately
- Try "Update Now" action to force refresh
- Check Indigo log for errors

### Actions Not Working
- Verify VLC is running and responsive
- Check that VLC has proper macOS permissions
- Try controlling VLC directly to verify it's working
- Some actions require media to be loaded

### Variables Not Created
- Enable "Update Indigo Variables" in device settings
- Check variable prefix doesn't conflict with existing variables
- Variables are created on first update after enabling

### VLC Not Responding
The plugin uses AppleScript to communicate with VLC:
- VLC must be installed on the Mac running Indigo
- macOS may prompt for accessibility permissions
- Grant permissions in System Preferences → Security & Privacy

### Media Won't Open
- Check that file path is correct and accessible
- Ensure file format is supported by VLC
- For URLs, verify network connectivity
- Check VLC logs for codec/format errors

## Technical Details

### Requirements
- Indigo 2022.1 or later
- macOS with VLC media player installed
- Python 3.7+ (included with Indigo)

### How It Works
- Uses AppleScript to communicate with VLC application
- Polls VLC at configurable intervals
- No network requests required (all local)
- Works with all media types VLC supports

### Performance
- Minimal CPU usage with 1-2 second update frequency
- No impact on VLC performance
- Updates only when device is active in Indigo

### Supported Media Types
VLC supports virtually all media formats:
- Video: MP4, AVI, MKV, MOV, WMV, FLV, etc.
- Audio: MP3, FLAC, AAC, OGG, WAV, etc.
- Streams: HTTP, HTTPS, RTSP, MMS, etc.
- Discs: DVD, Blu-ray, CD, VCD

## VLC-Specific Features

### Advantages Over Music Players
- **Universal format support**: Plays videos, audio, streams, everything
- **Playlist management**: Built-in playlist support
- **Streaming**: HTTP/HTTPS streaming URLs
- **Playback speed control**: 0.25x to 2.0x speed
- **Step controls**: Precise seeking with variable step sizes
- **Fullscreen control**: Automate theater mode

### Use Cases
- **Home theater automation**: Control movies/TV shows
- **Video surveillance**: Monitor security camera streams
- **Music videos**: Play music with video
- **Podcasts**: Play video podcasts
- **Presentations**: Automate video presentations
- **Background music**: Play audio files/streams

## Advanced Features

### Playlist Control
VLC's built-in playlist works seamlessly:
- Use "Next" and "Previous" to navigate playlist
- Enable "Random" for shuffle playback
- Enable "Loop" to repeat playlist

### Stream Monitoring
Monitor live streams and take actions:
- Trigger on stream start/stop
- Check stream status periodically
- Auto-restart failed streams

### Multi-Zone Audio/Video
Use with multiple VLC devices:
- One VLC instance per zone
- Coordinate playback across zones
- Synchronize multiple streams

## Version History

### 1.0.0
- Initial release
- Complete playback control
- Comprehensive state monitoring
- Variable integration
- Media file and URL support
- Playback speed control
- Fullscreen/Loop/Random support

## Support

For issues or feature requests:
1. Check Indigo plugin log for errors
2. Verify VLC is working properly
3. Test with different update frequencies
4. Report issues with log excerpts

## Comparison: VLC vs Music Players

| Feature | VLC | Spotify/Apple Music |
|---------|-----|---------------------|
| Video Support | ✓ | ✗ |
| Local Files | ✓ | Limited |
| Streaming URLs | ✓ | ✗ |
| All Audio Formats | ✓ | Limited |
| Playback Speed | ✓ | ✗ |
| Fullscreen Control | ✓ | ✗ |
| Library Integration | ✗ | ✓ |
| Cloud Service | ✗ | ✓ |

## License

This plugin is provided as-is for use with Indigo home automation.

---

**Note**: This plugin controls the VLC application on the Mac running Indigo. It works with any media that VLC can play, including local files, network streams, and more. VLC must be installed and running for the plugin to function.
