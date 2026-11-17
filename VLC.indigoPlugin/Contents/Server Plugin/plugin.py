#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLC Control Plugin for Indigo
Version 2.1.1 - HTTP REST API preferred mode
"""

import indigo
import time
import subprocess
import os
import json
import base64

try:
    import urllib2
    from urllib import urlencode
except ImportError:
    import urllib.request as urllib2
    from urllib.parse import urlencode

kUpdateFrequencyKey = "updateFrequency"
kConnectionMethodKey = "connectionMethod"
kHttpHostKey = "httpHost"
kHttpPortKey = "httpPort"
kHttpPasswordKey = "httpPassword"


class Plugin(indigo.PluginBase):
    
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = pluginPrefs.get("showDebugInfo", False)
        self.deviceDict = {}

    def getUpdateFrequency(self, dev):
        try:
            freq = float(dev.pluginProps.get(kUpdateFrequencyKey, 5))
        except Exception:
            freq = 5.0
        return max(2.0, freq)

    def useHttpMode(self, dev):
        return True
        
    def startup(self):
        self.debugLog(u"VLC Plugin v2.1.1 startup")
        self.debugLog(u"HTTP REST API is now enforced for polling and actions")
        
    def shutdown(self):
        self.debugLog(u"VLC Plugin shutdown")
        
    def deviceStartComm(self, dev):
        self.debugLog(u"Starting device: " + dev.name)
        updateFreq = self.getUpdateFrequency(dev)
        connectionMethod = "http"
        
        self.deviceDict[dev.id] = {
            'device': dev,
            'updateFrequency': updateFreq,
            'lastUpdate': 0,
            'previousVolume': None,
            'connectionMethod': connectionMethod
        }
        
        if connectionMethod == "http":
            host = dev.pluginProps.get(kHttpHostKey, "localhost")
            port = dev.pluginProps.get(kHttpPortKey, "8080")
            password = dev.pluginProps.get(kHttpPasswordKey, "")
            self.debugLog(u"Using HTTP REST API at {}:{}".format(host, port))
        else:
            self.debugLog(u"Using AppleScript method")
        
        self.updateVLCStatus(dev)
        
    def deviceStopComm(self, dev):
        self.debugLog(u"Stopping device: " + dev.name)
        if dev.id in self.deviceDict:
            del self.deviceDict[dev.id]
            
    def runConcurrentThread(self):
        try:
            while True:
                currentTime = time.time()
                for devId, devInfo in list(self.deviceDict.items()):
                    dev = devInfo['device']
                    updateFreq = devInfo['updateFrequency']
                    lastUpdate = devInfo['lastUpdate']
                    if currentTime - lastUpdate >= updateFreq:
                        self.updateVLCStatus(dev)
                        devInfo['lastUpdate'] = currentTime
                self.sleep(0.1)
        except self.StopThread:
            pass
    
    ################################################################################
    # HTTP REST API Methods
    ################################################################################
    
    def makeHttpRequest(self, dev, endpoint, command=None):
        """Make HTTP request to VLC REST API"""
        try:
            host = dev.pluginProps.get(kHttpHostKey, "localhost")
            port = dev.pluginProps.get(kHttpPortKey, "8080")
            password = dev.pluginProps.get(kHttpPasswordKey, "")
            
            url = "http://{}:{}/requests/{}".format(host, port, endpoint)
            
            if command:
                url += "?" + urlencode(command)
            
            request = urllib2.Request(url)
            
            if password:
                # Add basic authentication
                auth_str = ":{}".format(password)
                base64_str = base64.b64encode(auth_str.encode()).decode()
                request.add_header("Authorization", "Basic {}".format(base64_str))
            
            response = urllib2.urlopen(request, timeout=5)
            data = response.read().decode('utf-8')
            
            if endpoint == "status.json":
                return json.loads(data)
            else:
                return {'success': True}
                
        except Exception as e:
            self.debugLog(u"HTTP request error: {}".format(str(e)))
            return None
    
    def updateVLCStatusHTTP(self, dev):
        """Update VLC status using HTTP REST API"""
        try:
            status = self.makeHttpRequest(dev, "status.json")
            
            if status is None:
                # VLC not responding
                self.setNotRunningState(dev)
                return
            
            # Parse status response
            result = {}
            result['notRunning'] = False
            
            # Playing state
            state = status.get('state', 'stopped')
            result['playing'] = 1 if state == 'playing' else 0
            result['playerState'] = state
            
            # Current item info
            info = status.get('information', {})
            category = info.get('category', {})
            meta = category.get('meta', {}) if isinstance(category, dict) else {}
            
            result['mediaName'] = meta.get('filename', meta.get('title', ''))
            result['mediaPath'] = meta.get('filename', '')
            
            # Time and duration
            result['currentTime'] = int(status.get('time', 0))
            result['duration'] = int(status.get('length', 0))
            
            # Volume (VLC HTTP returns 0-320, normalize to 0-100)
            vlc_volume = int(status.get('volume', 256))
            result['audioVolume'] = min(100, int((vlc_volume / 320.0) * 100))
            
            # Fullscreen
            result['fullscreen'] = status.get('fullscreen', False)
            
            # Loop and random
            result['looping'] = status.get('loop', False)
            result['random'] = status.get('random', False)
            
            self.updateDeviceStates(dev, result)
            
        except Exception as e:
            self.errorLog(u"Error updating VLC status via HTTP: {}".format(str(e)))
            self.setNotRunningState(dev)
    
    ################################################################################
    # AppleScript Methods
    ################################################################################
    
    def executeAppleScriptSimple(self, script):
        """Execute simple AppleScript and return result"""
        try:
            process = subprocess.Popen(['osascript', '-e', script],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            if error:
                error_str = error.decode('utf-8')
                self.debugLog(u"AppleScript error: {}".format(error_str))
                return {'error': error_str}
            
            result_str = output.decode('utf-8').strip()
            
            # Handle different return types
            if result_str == "NOTRUNNING":
                return {'notRunning': True}
            elif result_str == "RUNNING":
                return {'value': result_str}
            elif not result_str:
                return {'value': ''}
            else:
                # Try to convert to integer if possible
                try:
                    int_val = int(result_str)
                    return {'value': int_val}
                except ValueError:
                    # Return as string
                    return {'value': result_str}
            
        except Exception as e:
            self.errorLog(u"Exception in executeAppleScript: {}".format(str(e)))
            return {'error': str(e)}
    
    def updateVLCStatusAppleScript(self, dev):
        """Update VLC status using AppleScript (individual calls per property)"""
        try:
            # First check if VLC is running
            checkScript = '''
tell application "System Events"
    if (name of processes) contains "VLC" then
        return "RUNNING"
    else
        return "NOTRUNNING"
    end if
end tell
'''
            checkResult = self.executeAppleScriptSimple(checkScript)
            
            if checkResult is None or checkResult.get('notRunning', True):
                self.setNotRunningState(dev)
                return
            
            # VLC is running - get each property individually
            result = {}
            
            # Get playing state
            script = 'tell application "VLC" to return (playing as integer)'
            playingResult = self.executeAppleScriptSimple(script)
            if playingResult and not playingResult.get('error'):
                result['playing'] = playingResult.get('value', 0)
            else:
                result['playing'] = 0
            
            # Get current item name
            script = '''
tell application "VLC"
    try
        return name of current item
    on error
        return ""
    end try
end tell
'''
            nameResult = self.executeAppleScriptSimple(script)
            if nameResult and not nameResult.get('error'):
                result['mediaName'] = nameResult.get('value', '')
            else:
                result['mediaName'] = ''
            
            # Get current item path
            script = '''
tell application "VLC"
    try
        return path of current item
    on error
        return ""
    end try
end tell
'''
            pathResult = self.executeAppleScriptSimple(script)
            if pathResult and not pathResult.get('error'):
                result['mediaPath'] = pathResult.get('value', '')
            else:
                result['mediaPath'] = ''
            
            # Get duration
            script = '''
tell application "VLC"
    try
        return (duration of current item) as integer
    on error
        return 0
    end try
end tell
'''
            durationResult = self.executeAppleScriptSimple(script)
            if durationResult and not durationResult.get('error'):
                result['duration'] = durationResult.get('value', 0)
            else:
                result['duration'] = 0
            
            # Get current time
            script = '''
tell application "VLC"
    try
        return (current time) as integer
    on error
        return 0
    end try
end tell
'''
            timeResult = self.executeAppleScriptSimple(script)
            if timeResult and not timeResult.get('error'):
                result['currentTime'] = timeResult.get('value', 0)
            else:
                result['currentTime'] = 0
            
            # Get volume
            script = '''
tell application "VLC"
    try
        return audio volume as integer
    on error
        return 128
    end try
end tell
'''
            volumeResult = self.executeAppleScriptSimple(script)
            if volumeResult and not volumeResult.get('error'):
                vlc_volume = volumeResult.get('value', 128)
                result['audioVolume'] = int((vlc_volume * 100) / 256)
            else:
                result['audioVolume'] = 50
            
            # Get fullscreen
            script = '''
tell application "VLC"
    try
        return (fullscreen as integer)
    on error
        return 0
    end try
end tell
'''
            fullscreenResult = self.executeAppleScriptSimple(script)
            if fullscreenResult and not fullscreenResult.get('error'):
                result['fullscreen'] = fullscreenResult.get('value', 0) == 1
            else:
                result['fullscreen'] = False
            
            result['notRunning'] = False
            result['looping'] = False  # Not available via AppleScript
            result['random'] = False   # Not available via AppleScript
            
            self.updateDeviceStates(dev, result)
            
        except Exception as e:
            self.errorLog(u"Error updating VLC status via AppleScript: {}".format(str(e)))
            self.setNotRunningState(dev)
    
    ################################################################################
    # Common Status Update Methods
    ################################################################################
    
    def updateVLCStatus(self, dev):
        """Main status update dispatcher"""
        self.updateVLCStatusHTTP(dev)
    
    def setNotRunningState(self, dev):
        """Set device states when VLC is not running"""
        stateList = []
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
        dev.updateStatesOnServer(stateList)
    
    def updateDeviceStates(self, dev, result):
        """Update device states from result dictionary"""
        stateList = []
        
        playingState = result.get('playing', 0)
        isPlaying = playingState == 1
        mediaName = result.get('mediaName', '')
        
        playerState = result.get('playerState')
        if playerState not in ('playing', 'paused', 'stopped'):
            playerState = 'playing' if isPlaying else ('paused' if mediaName else 'stopped')
        isPlaying = playerState == 'playing'
        isPaused = playerState == 'paused'
        isStopped = playerState == 'stopped'

        stateList.append({'key': 'playerState', 'value': playerState})
        stateList.append({'key': 'isPlaying', 'value': isPlaying})
        stateList.append({'key': 'isPaused', 'value': isPaused})
        stateList.append({'key': 'isStopped', 'value': isStopped})
        
        mediaPath = result.get('mediaPath', '')
        stateList.append({'key': 'mediaName', 'value': mediaName})
        stateList.append({'key': 'mediaPath', 'value': mediaPath})
        
        duration = int(result.get('duration', 0))
        currentTime = int(result.get('currentTime', 0))
        
        stateList.append({'key': 'duration', 'value': duration})
        stateList.append({'key': 'durationFormatted', 'value': self.formatTime(duration)})
        stateList.append({'key': 'currentTime', 'value': currentTime})
        stateList.append({'key': 'currentTimeFormatted', 'value': self.formatTime(currentTime)})
        
        progressPercent = 0
        if duration > 0:
            progressPercent = int((float(currentTime) / float(duration)) * 100)
        stateList.append({'key': 'progressPercent', 'value': progressPercent})
        
        volume = int(result.get('audioVolume', 50))
        muted = (volume == 0)
        stateList.append({'key': 'audioVolume', 'value': volume})
        stateList.append({'key': 'muted', 'value': muted})
        
        stateList.append({'key': 'fullscreen', 'value': result.get('fullscreen', False)})
        stateList.append({'key': 'looping', 'value': result.get('looping', False)})
        stateList.append({'key': 'random', 'value': result.get('random', False)})
        
        # Create status string
        if isPlaying:
            icon = u'▶'
        elif isPaused:
            icon = u'⏸'
        else:
            icon = u'⏹'
        
        if mediaName:
            statusStr = u'{} {} - {}% - {}%'.format(
                icon, 
                mediaName[:30],
                progressPercent,
                volume
            )
        else:
            statusStr = u'{} Ready'.format(icon)
        
        stateList.append({'key': 'status', 'value': statusStr})
        
        dev.updateStatesOnServer(stateList)
        
        # Update variables if enabled
        if dev.pluginProps.get('updateVariables', False):
            self.updateVariables(dev, stateList)
    
    def updateVariables(self, dev, stateList):
        """Update Indigo variables with VLC data"""
        try:
            prefix = dev.pluginProps.get('variablePrefix', 'VLC')
            
            for state in stateList:
                varName = "{}_{}".format(prefix, state['key'])
                varValue = str(state['value'])
                
                # Create variable if it doesn't exist
                if varName not in indigo.variables:
                    indigo.variable.create(varName, value=varValue, folder="VLC Control")
                else:
                    indigo.variable.updateValue(varName, varValue)
        except Exception as e:
            self.errorLog(u"Error updating variables: {}".format(str(e)))
    
    def formatTime(self, seconds):
        """Format seconds to H:MM:SS or M:SS"""
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
    
    ################################################################################
    # Action Methods - HTTP
    ################################################################################
    
    def sendCommandHTTP(self, dev, command):
        """Send command via HTTP API"""
        return self.makeHttpRequest(dev, "status.json", {'command': command})
    
    def actionPlayHTTP(self, dev):
        self.sendCommandHTTP(dev, 'pl_play')
    
    def actionPauseHTTP(self, dev):
        self.sendCommandHTTP(dev, 'pl_pause')
    
    def actionStopHTTP(self, dev):
        self.sendCommandHTTP(dev, 'pl_stop')
    
    def actionNextHTTP(self, dev):
        self.sendCommandHTTP(dev, 'pl_next')
    
    def actionPreviousHTTP(self, dev):
        self.sendCommandHTTP(dev, 'pl_previous')
    
    def actionSetVolumeHTTP(self, dev, volume):
        # HTTP volume range is 0-320
        vlcVolume = int((volume / 100.0) * 320)
        self.makeHttpRequest(dev, "status.json", {'command': 'volume', 'val': vlcVolume})
    
    def actionSetFullscreenHTTP(self, dev, fullscreen):
        self.setOptionHTTP(dev, 'fullscreen', 'fullscreen', 'on' if fullscreen else 'off')
    
    def setOptionHTTP(self, dev, key, command, desired):
        """Read live VLC state before sending a toggle for an explicit On/Off."""
        if desired not in ('on', 'off', 'toggle'):
            self.errorLog('Invalid option state: {}'.format(desired))
            return
        if desired == 'toggle':
            self.sendCommandHTTP(dev, command)
            return
        status = self.makeHttpRequest(dev, 'status.json')
        if status is None or key not in status:
            self.errorLog('Cannot read VLC {} state; command not sent'.format(key))
            return
        if bool(status[key]) != (desired == 'on'):
            self.sendCommandHTTP(dev, command)

    def actionSeekHTTP(self, dev, position):
        self.makeHttpRequest(dev, "status.json", {'command': 'seek', 'val': position})
    
    ################################################################################
    # Action Methods - AppleScript
    ################################################################################
    
    def executeAppleScript(self, script):
        """Execute AppleScript command (for actions)"""
        try:
            process = subprocess.Popen(['osascript', '-e', script],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            output, error = process.communicate()
            if error:
                self.debugLog(u"AppleScript error: {}".format(error.decode('utf-8')))
                return False
            return True
        except Exception as e:
            self.errorLog(u"Exception in executeAppleScript: {}".format(str(e)))
            return False
    
    def actionPlayAppleScript(self, dev):
        self.executeAppleScript('tell application "VLC" to play')
    
    def actionPauseAppleScript(self, dev):
        self.executeAppleScript('tell application "VLC" to pause')
    
    def actionStopAppleScript(self, dev):
        self.executeAppleScript('tell application "VLC" to stop')
    
    def actionNextAppleScript(self, dev):
        self.executeAppleScript('tell application "VLC" to next')
    
    def actionPreviousAppleScript(self, dev):
        self.executeAppleScript('tell application "VLC" to previous')
    
    def actionSetVolumeAppleScript(self, dev, volume):
        vlcVolume = int((volume / 100.0) * 256)
        self.executeAppleScript('tell application "VLC" to set audio volume to {}'.format(vlcVolume))
    
    def actionSetFullscreenAppleScript(self, dev, fullscreen):
        fullscreenBool = 'true' if fullscreen else 'false'
        self.executeAppleScript('tell application "VLC" to set fullscreen to {}'.format(fullscreenBool))
    
    def actionSeekAppleScript(self, dev, position):
        self.executeAppleScript('tell application "VLC" to set current time to {}'.format(position))
    
    ################################################################################
    # Public Action Methods (dispatchers)
    ################################################################################
    
    def actionPlay(self, pluginAction, dev):
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionPlayHTTP(dev)
        else:
            self.actionPlayAppleScript(dev)
        time.sleep(0.3)
        self.updateVLCStatus(dev)
        
    def actionPause(self, pluginAction, dev):
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionPauseHTTP(dev)
        else:
            self.actionPauseAppleScript(dev)
        time.sleep(0.3)
        self.updateVLCStatus(dev)
        
    def actionPlayPause(self, pluginAction, dev):
        if dev.states.get('isPlaying', False):
            self.actionPause(pluginAction, dev)
        else:
            self.actionPlay(pluginAction, dev)
        
    def actionStop(self, pluginAction, dev):
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionStopHTTP(dev)
        else:
            self.actionStopAppleScript(dev)
        time.sleep(0.3)
        self.updateVLCStatus(dev)
        
    def actionNext(self, pluginAction, dev):
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionNextHTTP(dev)
        else:
            self.actionNextAppleScript(dev)
        time.sleep(0.5)
        self.updateVLCStatus(dev)
        
    def actionPrevious(self, pluginAction, dev):
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionPreviousHTTP(dev)
        else:
            self.actionPreviousAppleScript(dev)
        time.sleep(0.5)
        self.updateVLCStatus(dev)
        
    def actionSetVolume(self, pluginAction, dev):
        volume = int(pluginAction.props.get('volume', 50))
        volume = max(0, min(100, volume))
        
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionSetVolumeHTTP(dev, volume)
        else:
            self.actionSetVolumeAppleScript(dev, volume)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionVolumeUp(self, pluginAction, dev):
        amount = int(pluginAction.props.get('amount', 10))
        currentVolume = int(dev.states.get('audioVolume', 50))
        newVolume = min(100, currentVolume + amount)
        
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionSetVolumeHTTP(dev, newVolume)
        else:
            self.actionSetVolumeAppleScript(dev, newVolume)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionVolumeDown(self, pluginAction, dev):
        amount = int(pluginAction.props.get('amount', 10))
        currentVolume = int(dev.states.get('audioVolume', 50))
        newVolume = max(0, currentVolume - amount)
        
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionSetVolumeHTTP(dev, newVolume)
        else:
            self.actionSetVolumeAppleScript(dev, newVolume)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionMute(self, pluginAction, dev):
        status = self.makeHttpRequest(dev, 'status.json')
        if status is None:
            self.errorLog('Cannot read VLC volume; mute not sent')
            return
        volume = int(status.get('volume', 0))
        devInfo = self.deviceDict.get(dev.id)
        if volume > 0:
            if devInfo is not None:
                devInfo['previousVolume'] = volume
            self.makeHttpRequest(dev, 'status.json', {'command': 'volume', 'val': 0})
        self.updateVLCStatus(dev)

    def actionUnmute(self, pluginAction, dev):
        status = self.makeHttpRequest(dev, 'status.json')
        if status is None:
            self.errorLog('Cannot read VLC volume; unmute not sent')
            return
        if int(status.get('volume', 0)) == 0:
            devInfo = self.deviceDict.get(dev.id, {})
            volume = devInfo.get('previousVolume')
            if volume is None or volume <= 0:
                volume = 160  # Existing default of 50% on the plugin scale.
            self.makeHttpRequest(dev, 'status.json', {'command': 'volume', 'val': volume})
        self.updateVLCStatus(dev)

    def actionStepForward(self, pluginAction, dev):
        step = pluginAction.props.get('step', 'short')
        currentTime = int(dev.states.get('currentTime', 0))
        step_seconds = {'extrashort': 3, 'short': 10, 'medium': 60, 'long': 300}
        newTime = currentTime + step_seconds.get(step, 10)
        
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionSeekHTTP(dev, newTime)
        else:
            self.actionSeekAppleScript(dev, newTime)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionStepBackward(self, pluginAction, dev):
        step = pluginAction.props.get('step', 'short')
        currentTime = int(dev.states.get('currentTime', 0))
        step_seconds = {'extrashort': 3, 'short': 10, 'medium': 60, 'long': 300}
        newTime = max(0, currentTime - step_seconds.get(step, 10))
        
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionSeekHTTP(dev, newTime)
        else:
            self.actionSeekAppleScript(dev, newTime)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionJumpTo(self, pluginAction, dev):
        position = int(pluginAction.props.get('position', 0))
        
        connectionMethod = "http"
        if connectionMethod == "http":
            self.actionSeekHTTP(dev, position)
        else:
            self.actionSeekAppleScript(dev, position)
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionSetFullscreen(self, pluginAction, dev):
        self.setOptionHTTP(dev, 'fullscreen', 'fullscreen', pluginAction.props.get('fullscreenState', 'toggle'))
        self.updateVLCStatus(dev)

    def actionSetLoop(self, pluginAction, dev):
        self.setOptionHTTP(dev, 'loop', 'pl_loop', pluginAction.props.get('loopState', 'toggle'))
        self.updateVLCStatus(dev)

    def actionSetRandom(self, pluginAction, dev):
        self.setOptionHTTP(dev, 'random', 'pl_random', pluginAction.props.get('randomState', 'toggle'))
        self.updateVLCStatus(dev)

    def actionOpenMedia(self, pluginAction, dev):
        mediaPath = pluginAction.props.get('mediaPath', '')
        if mediaPath:
            mediaPath = os.path.expanduser(mediaPath)
            connectionMethod = "http"
            if connectionMethod == "http":
                # Use HTTP to add to playlist and play
                self.makeHttpRequest(dev, "status.json", {
                    'command': 'in_play',
                    'input': 'file://' + mediaPath
                })
            else:
                self.executeAppleScript('tell application "VLC" to open POSIX file "{}"'.format(mediaPath))
            time.sleep(0.5)
            self.updateVLCStatus(dev)
        
    def actionOpenURL(self, pluginAction, dev):
        url = pluginAction.props.get('url', '')
        if url:
            connectionMethod = "http"
            if connectionMethod == "http":
                self.makeHttpRequest(dev, "status.json", {
                    'command': 'in_play',
                    'input': url
                })
            else:
                self.executeAppleScript('tell application "VLC" to OpenURL "{}"'.format(url))
            time.sleep(0.5)
            self.updateVLCStatus(dev)
        
    def actionSetPlaybackRate(self, pluginAction, dev):
        raw = pluginAction.props.get('rate', 'normal')
        named_rates = {'veryslow': 0.25, 'slow': 0.5, 'normal': 1.0, 'fast': 1.5, 'veryfast': 2.0}
        try:
            rate = named_rates[raw] if raw in named_rates else float(raw)
            if not 0.25 <= rate <= 2.0:
                raise ValueError('rate out of range')
        except (ValueError, TypeError):
            self.errorLog('Invalid playback rate: {}'.format(raw))
            return
        connectionMethod = "http"
        if connectionMethod == "http":
            self.makeHttpRequest(dev, "status.json", {'command': 'rate', 'val': rate})
        else:
            self.logger.info(u"Playback rate not supported by VLC AppleScript")
        time.sleep(0.2)
        self.updateVLCStatus(dev)
        
    def actionUpdateNow(self, pluginAction, dev):
        self.updateVLCStatus(dev)

