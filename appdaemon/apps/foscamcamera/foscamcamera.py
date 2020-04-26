# https://appdaemon.readthedocs.io/en/latest/APPGUIDE.html
# https://ryqiem.github.io/AppDaemon-API/

import appdaemon.plugins.mqtt.mqttapi as mqtt
import hassapi as hass
import requests, sys, xmltodict
import datetime

''' 
1. infrared light > switch
2. motion sensor  > binary_sensor
3. audio sensor  > binary_sensor
'''

class foscamcamera(hass.Hass):
    #initialize() function which will be called at startup and reload
    async def initialize(self):
        #self.log(dir(self))
        #self.log(">> {}".format(str(self.name)))
        self.ip = self.args['foscam_ip']
        self.usr = self.args['foscam_username']
        self.pwd = self.args['foscam_password'] 
        self.interval = self.args['interval'] if 'interval' in self.args else 5
        self.log("Foscam Camera {} settings: User {} and Pwd {} with interval {}".format(self.ip, self.usr, self.pwd, self.interval))
        self.current_status = None
        self.audio_status = [None, str(self.args['audio_entity'])]
        self.motion_status = [None, str(self.args['motion_entity'])]
        self.log("Audio Sensor Entity: {}".format(self.audio_status[1]))
        self.log("Motion Sensor Entity: {}".format(self.motion_status[1]))
        #initialize the CGI Controller
        await self.init_controller(None)
        self.run_in(self.cgi_controller, 0)
    
    async def init_controller(self, kwargs):
        url = "http://%s:88//cgi-bin/CGIProxy.fcgi?cmd=setMotionDetectConfig1&isEnable=1&snapInterval=1&schedule0=281474976710655&schedule1=281474976710655&schedule2=281474976710655&schedule3=281474976710655&schedule4=281474976710655&schedule5=281474976710655&schedule6=281474976710655&x1=0&y1=0&width1=10000&height1=10000&sensitivity1=1&valid1=1&linkage=6&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
        response = requests.get(url)

    async def cgi_controller(self, kwargs):
        try:
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=getDevState&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
            doc = xmltodict.parse(response.content)['CGI_Result']
            differences = []
            if self.current_status is not None:
                #search for the difference in keys
                differences = [i for i in list(doc) if self.current_status.get(i) != doc.get(i)]
            
            if differences or self.current_status is None:
                if self.current_status is not None:
                    self.log("Difference in {}".format(str(differences)))
                #process the current status
                if 'soundAlarm' in differences or self.current_status is None:
                    await self.setAudioStatus(doc['soundAlarm'][0])
                if 'motionDetectAlarm' in differences or self.current_status is None:
                    await self.setMotionDetectStatus(doc['motionDetectAlarm'][0])
            self.current_status = doc
        except Exception as ex:
            self.log(str(ex), level="ERROR")
        finally:
            self.run_in(self.cgi_controller, self.interval)
        
    async def setAudioStatus(self, new_audio_status):
        try:
            if self.audio_status[1] is not None and \
                (self.audio_status[0] is None or \
                (self.audio_status[0] is not None and self.audio_status[0] != new_audio_status)):
                if new_audio_status in ["0","1"]:
                    self.set_state(self.audio_status[1], state = "off")
                else:
                    self.set_state(self.audio_status[1], state = "on")  
            self.audio_status[0] = new_audio_status
        except Exception as ex:
            self.log("Exception while setting the audio status {}".format(ex))
    
    async def setMotionDetectStatus(self, new_motion_status):
        try:
            if self.motion_status[1] is not None and \
                (self.motion_status[0] is None or \
                (self.motion_status[0] is not None and self.motion_status[0] != new_motion_status)):
                if new_motion_status in ["0","1"]:
                    self.set_state(self.motion_status[1], state = "off")
                else:
                    self.set_state(self.motion_status[1], state = "on")  
            self.motion_status[0] = new_motion_status
        except Exception as ex:
            self.log("Exception when setting the motion detection status {}".format(ex))