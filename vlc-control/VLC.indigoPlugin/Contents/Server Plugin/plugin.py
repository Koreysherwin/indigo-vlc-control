#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLC Control Plugin for Indigo
Provides comprehensive control and monitoring of VLC media player
"""

import indigo
import time
import subprocess
import os

# Constants
kUpdateFrequencyKey = "updateFrequency"


class Plugin(indigo.PluginBase):
    """Main plugin class for VLC control"""
    
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = pluginPrefs.get("showDebugInfo", False)
        self.deviceDict = {}
        
    def startup(self):
        """Called when plugin starts"""
        self.debugLog(u"VLC Plugin startup called")
        
    def shutdown(self):
        """Called when plugin shuts down"""
        self.debugLog(u"VLC Plugin shutdown called")
        
    def deviceStartComm(self, dev):
        """Called when device communication starts"""
        self.debugLog(u"Starting device: " + dev.name)
        
        # Initialize the device's update frequency
        updateFreq = float(dev.pluginProps.get(kUpdateFrequencyKey, 1))
        
        # Store device info
        self.deviceDict[dev.id] = {
            'device': dev,
            'updateFrequency': updateFreq,
            'lastUpdate': 0,
            'previousVolume': None  # For mute/unmute
        }
        
        # Do initial update
        self.updateVLCStatus(dev)
        
    def deviceStopComm(self, dev):
        """Called when device communication stops"""
        self.debugLog(u"Stopping device: " + dev.name)
        if dev.id in self.deviceDict:
            del self.deviceDict[dev.id]
            
    def runConcurrentThread(self):
        """Main plugin loop - updates device states"""
        try:
            while True:
                currentTime = time.time()
                
                for devId, devInfo in list(self.deviceDict.items()):
                    dev = devInfo['device']
                    updateFreq = devInfo['updateFrequency']
                    lastUpdate = devInfo['lastUpdate']
                    
                    # Check if it's time to update this device
                    if currentTime - lastUpdate >= updateFreq:
                        self.updateVLCStatus(dev)
                        devInfo['lastUpdate'] = currentTime
                
                self.sleep(0.1)  # Short sleep to prevent CPU spinning
                
        except self.StopThread:
            pass
            
    def updateVLCStatus(self, dev):
        """Update all VLC status information"""
        try:
            # Build comprehensive AppleScript to get all VLC data
            script = '''
            tell application "System Events"
                set vlcRunning to (name of processes) contains "VLC"
            end tell
            
            if vlcRunning then
                tell application "VLC"
                    try
                        set isPlaying to playing
                        set currentPos to current time
                        set totalDuration to duration of current item
                        set mediaName to name of current item
                        set mediaPath to path of current item
                        set volLevel to audio volume
                        set isMuted to muted
                        set isFullscreen to fullscreen
                        set isLooping to looping
                        set isRandom to random
                        
                        return {playing:isPlaying, currentTime:currentPos, duration:totalDuration, mediaName:mediaName, mediaPath:mediaPath, audioVolume:volLevel, muted:isMuted, fullscreen:isFullscreen, looping:isLooping, randomMode:isRandom}
                    on error errMsg
                        return {errorMsg:errMsg}
                    end try
                end tell
            else
                return {playing:false, currentTime:0, duration:0, mediaName:"", mediaPath:"", audioVolume:50, muted:false, fullscreen:false, looping:false, randomMode:false, notRunning:true}
            end if
            '''
            
            # Execute AppleScript
            result = self.executeAppleScript(script)
            
            if result and 'errorMsg' not in result:
                stateList = []
                
                # Check if VLC is not running
                if result.get('notRunning', False):
                    stateList.append({'key': 'playerState', 'value': 'stopped'})
                    stateList.append({'key': 'isPlaying', 'value': False})
                    stateList.append({'key': 'isPaused', 'value': False})
                    stateList.append({'key': 'isStopped', 'value': True})
                    stateList.append({'key': 'mediaName', 'value': ''})
                    stateList.append({'key': 'mediaPath', 'value': ''})
                    stateList.append({'key': 'currentTime', 'value': 0})
                    stateList.append({'key': 'currentTimeFormatted', 'value': '0:00'})
                    stateList.append({'key': 'duration', 'value': 0})
                    stateList.append({'key': 'durationFormatted', 'value': '0:00'})
                    stateList.append({'key': 'progressPercent', 'value': 0})
                    stateList.append({'key': 'audioVolume', 'value': 50})
                    stateList.append({'key': 'muted', 'value': False})
                    stateList.append({'key': 'fullscreen', 'value': False})
                    stateList.append({'key': 'looping', 'value': False})
                    stateList.append({'key': 'random', 'value': False})
                    stateList.append({'key': 'status', 'value': u'⏹ VLC Not Running'})
                else:
                    # Player state
                    isPlaying = result.get('playing', False)
                    
                    if isPlaying:
                        playerState = 'playing'
                        isPaused = False
                        isStopped = False
                    else:
                        # VLC doesn't distinguish between paused and stopped well
                        # If there's media loaded, it's paused; otherwise stopped
                        mediaName = result.get('mediaName', '')
                        if mediaName:
                            playerState = 'paused'
                            isPaused = True
                            isStopped = False
                        else:
                            playerState = 'stopped'
                            isPaused = False
                            isStopped = True
                    
                    stateList.append({'key': 'playerState', 'value': playerState})
                    stateList.append({'key': 'isPlaying', 'value': isPlaying})
                    stateList.append({'key': 'isPaused', 'value': isPaused})
                    stateList.append({'key': 'isStopped', 'value': isStopped})
                    
                    # Media information
                    mediaName = result.get('mediaName', '')
                    mediaPath = result.get('mediaPath', '')
                    
                    stateList.append({'key': 'mediaName', 'value': mediaName})
                    stateList.append({'key': 'mediaPath', 'value': mediaPath})
                    
                    # Duration and position
                    duration = int(result.get('duration', 0))
                    currentTime = int(result.get('currentTime', 0))
                    
                    stateList.append({'key': 'duration', 'value': duration})
                    stateList.append({'key': 'durationFormatted', 'value': self.formatTime(duration)})
                    stateList.append({'key': 'currentTime', 'value': currentTime})
                    stateList.append({'key': 'currentTimeFormatted', 'value': self.formatTime(currentTime)})
                    
                    # Progress percentage
                    progressPercent = 0
                    if duration > 0:
                        progressPercent = int((float(currentTime) / float(duration)) * 100)
                    stateList.append({'key': 'progressPercent', 'value': progressPercent})
                    
                    # Volume
                    volume = int(result.get('audioVolume', 50))
                    muted = result.get('muted', False)
                    stateList.append({'key': 'audioVolume', 'value': volume})
                    stateList.append({'key': 'muted', 'value': muted})
                    
                    # Playback options
                    stateList.append({'key': 'fullscreen', 'value': result.get('fullscreen', False)})
                    stateList.append({'key': 'looping', 'value': result.get('looping', False)})
                    stateList.append({'key': 'random', 'value': result.get('randomMode', False)})
                    
                    # Status display
                    if playerState == 'playing':
                        statusIcon = u"▶"
                    elif playerState == 'paused':
                        statusIcon = u"⏸"
                    else:
                        statusIcon = u"⏹"
                    
                    if mediaName:
                        # Extract just the filename if it's a path
                        displayName = os.path.basename(mediaName) if '/' in mediaName else mediaName
                        status = u"{} {}".format(statusIcon, displayName)
                    else:
                        status = u"{} No Media".format(statusIcon)
                    
                    stateList.append({'key': 'status', 'value': status})
                
                # Update all states at once
                dev.updateStatesOnServer(stateList)
                
                # Update variables if enabled
                if dev.pluginProps.get('updateVariables', False):
                    self.updateVariables(dev, stateList)
                
            else:
                # Error getting VLC status
                if result and 'errorMsg' in result:
                    self.errorLog(u"Error getting VLC status: {}".format(result['errorMsg']))
                
        except Exception as e:
            self.errorLog(u"Exception in updateVLCStatus: {}".format(str(e)))
            
    def updateVariables(self, dev, stateList):
        """Update Indigo variables with current states"""
        try:
            prefix = dev.pluginProps.get('variablePrefix', 'VLC')
            
            for state in stateList:
                varName = prefix + state['key'][0].upper() + state['key'][1:]
                
                # Create variable if it doesn't exist
                if varName not in indigo.variables:
                    indigo.variable.create(varName, value=str(state['value']), folder=0)
                else:
                    indigo.variable.updateValue(varName, value=str(state['value']))
                    
        except Exception as e:
            self.errorLog(u"Exception in updateVariables: {}".format(str(e)))
            
    def formatTime(self, seconds):
        """Format seconds as HH:MM:SS or MM:SS"""
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            
            if hours > 0:
                return u"{}:{:02d}:{:02d}".format(hours, minutes, secs)
            else:
                return u"{}:{:02d}".format(minutes, secs)
        except:
            return "0:00"
            
    def executeAppleScript(self, script):
        """Execute AppleScript and return result"""
        try:
            process = subprocess.Popen(['osascript', '-e', script],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            if error:
                self.debugLog(u"AppleScript error: {}".format(error.decode('utf-8')))
                return None
            
            # Parse the output
            result_str = output.decode('utf-8').strip()
            
            if not result_str:
                return {}
            
            # Parse AppleScript record format
            result = {}
            
            # Remove outer braces
            if result_str.startswith('{') and result_str.endswith('}'):
                result_str = result_str[1:-1]
            
            # Split by comma, but be careful with nested content
            parts = []
            current = ""
            depth = 0
            for char in result_str:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                elif char == ',' and depth == 0:
                    parts.append(current.strip())
                    current = ""
                    continue
                current += char
            if current:
                parts.append(current.strip())
            
            # Parse each key:value pair
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes from strings
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    
                    # Convert to appropriate type
                    if value == 'true':
                        value = True
                    elif value == 'false':
                        value = False
                    elif value.replace('.', '', 1).replace('-', '', 1).isdigit():
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    
                    result[key] = value
            
            return result
            
        except Exception as e:
            self.errorLog(u"Exception in executeAppleScript: {}".format(str(e)))
            return None
            
    ########################################
    # Action Handlers
    ########################################
    
    def actionPlay(self, pluginAction, dev):
        """Play action"""
        script = 'tell application "VLC" to play'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionPause(self, pluginAction, dev):
        """Pause action"""
        script = 'tell application "VLC" to pause'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionPlayPause(self, pluginAction, dev):
        """Play/Pause toggle action"""
        script = 'tell application "VLC" to play pause'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionStop(self, pluginAction, dev):
        """Stop action"""
        script = 'tell application "VLC" to stop'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionNext(self, pluginAction, dev):
        """Next action"""
        script = 'tell application "VLC" to next'
        self.executeAppleScript(script)
        time.sleep(0.5)
        self.updateVLCStatus(dev)
        
    def actionPrevious(self, pluginAction, dev):
        """Previous action"""
        script = 'tell application "VLC" to previous'
        self.executeAppleScript(script)
        time.sleep(0.5)
        self.updateVLCStatus(dev)
        
    def actionSetVolume(self, pluginAction, dev):
        """Set volume action"""
        volume = int(pluginAction.props.get('volume', 50))
        volume = max(0, min(100, volume))
        # VLC volume is 0-256, so convert from 0-100
        vlcVolume = int((volume / 100.0) * 256)
        script = f'tell application "VLC" to set audio volume to {vlcVolume}'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionVolumeUp(self, pluginAction, dev):
        """Volume up action"""
        amount = int(pluginAction.props.get('amount', 10))
        script = 'tell application "VLC" to volumeUp'
        # Execute multiple times for larger increases
        times = amount // 10
        for _ in range(max(1, times)):
            self.executeAppleScript(script)
            time.sleep(0.1)
        self.updateVLCStatus(dev)
        
    def actionVolumeDown(self, pluginAction, dev):
        """Volume down action"""
        amount = int(pluginAction.props.get('amount', 10))
        script = 'tell application "VLC" to volumeDown'
        # Execute multiple times for larger decreases
        times = amount // 10
        for _ in range(max(1, times)):
            self.executeAppleScript(script)
            time.sleep(0.1)
        self.updateVLCStatus(dev)
        
    def actionMute(self, pluginAction, dev):
        """Mute action"""
        devInfo = self.deviceDict.get(dev.id)
        if devInfo:
            currentVolume = int(dev.states.get('audioVolume', 50))
            devInfo['previousVolume'] = currentVolume
        script = 'tell application "VLC" to mute'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionUnmute(self, pluginAction, dev):
        """Unmute action"""
        script = 'tell application "VLC" to mute'  # VLC toggles mute
        # Check if currently muted
        if dev.states.get('muted', False):
            self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionStepForward(self, pluginAction, dev):
        """Step forward action"""
        step = pluginAction.props.get('step', 'short')
        
        if step == 'extrashort':
            script = 'tell application "VLC" to step forward'
        elif step == 'short':
            script = 'tell application "VLC" to step forward'
        elif step == 'medium':
            script = 'tell application "VLC" to step forward'
        elif step == 'long':
            script = 'tell application "VLC" to step forward'
        
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionStepBackward(self, pluginAction, dev):
        """Step backward action"""
        step = pluginAction.props.get('step', 'short')
        
        script = 'tell application "VLC" to step backward'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionJumpTo(self, pluginAction, dev):
        """Jump to position action"""
        position = int(pluginAction.props.get('position', 0))
        script = f'tell application "VLC" to set current time to {position}'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionSetFullscreen(self, pluginAction, dev):
        """Set fullscreen action"""
        fullscreenState = pluginAction.props.get('fullscreenState', 'toggle')
        
        if fullscreenState == 'toggle':
            script = 'tell application "VLC" to set fullscreen to (not fullscreen)'
        elif fullscreenState == 'on':
            script = 'tell application "VLC" to set fullscreen to true'
        else:
            script = 'tell application "VLC" to set fullscreen to false'
        
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionSetLoop(self, pluginAction, dev):
        """Set loop action"""
        loopState = pluginAction.props.get('loopState', 'toggle')
        
        if loopState == 'toggle':
            currentLoop = dev.states.get('looping', False)
            loopState = 'off' if currentLoop else 'on'
        
        loopBool = 'true' if loopState == 'on' else 'false'
        script = f'tell application "VLC" to set looping to {loopBool}'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionSetRandom(self, pluginAction, dev):
        """Set random action"""
        randomState = pluginAction.props.get('randomState', 'toggle')
        
        if randomState == 'toggle':
            currentRandom = dev.states.get('random', False)
            randomState = 'off' if currentRandom else 'on'
        
        randomBool = 'true' if randomState == 'on' else 'false'
        script = f'tell application "VLC" to set random to {randomBool}'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionOpenMedia(self, pluginAction, dev):
        """Open media file action"""
        mediaPath = pluginAction.props.get('mediaPath', '')
        if mediaPath:
            # Expand home directory if needed
            mediaPath = os.path.expanduser(mediaPath)
            script = f'tell application "VLC" to open POSIX file "{mediaPath}"'
            self.executeAppleScript(script)
            time.sleep(0.5)
            self.updateVLCStatus(dev)
        
    def actionOpenURL(self, pluginAction, dev):
        """Open URL action"""
        url = pluginAction.props.get('url', '')
        if url:
            script = f'tell application "VLC" to open location "{url}"'
            self.executeAppleScript(script)
            time.sleep(0.5)
            self.updateVLCStatus(dev)
        
    def actionSetPlaybackRate(self, pluginAction, dev):
        """Set playback rate action"""
        rate = pluginAction.props.get('rate', 'normal')
        
        rate_map = {
            'veryslow': 0.25,
            'slow': 0.5,
            'normal': 1.0,
            'fast': 1.5,
            'veryfast': 2.0
        }
        
        playback_rate = rate_map.get(rate, 1.0)
        script = f'tell application "VLC" to set playback rate to {playback_rate}'
        self.executeAppleScript(script)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionUpdateNow(self, pluginAction, dev):
        """Force immediate update"""
        self.updateVLCStatus(dev)
