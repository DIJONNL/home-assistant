# https://www.foscam.es/descarga/Foscam-IPCamera-CGI-User-Guide-AllPlatforms-2015.11.06.pdf


import appdaemon.plugins.mqtt.mqttapi as mqtt
import hassapi as hass
import requests, sys, xmltodict
from datetime import datetime
import time

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
        self.camera_entity = str(self.args['foscam_camera'])
        self.ip = self.args['foscam_ip']
        self.usr = self.args['foscam_username']
        self.pwd = self.args['foscam_password']
        self.prerecord = self.args['prerecord']
        self.prerecordtime = self.args['prerecordtime']
        self.interval = self.args['interval'] if 'interval' in self.args else 5
        self.log("Foscam Camera {} settings: User {} and Pwd {} with interval {}".format(self.ip, self.usr, self.pwd, self.interval))
        self.infrared_on = False
        self.audio_entity = self.args['audio_entity']
        self.motion_entity = self.args['motion_entity']
        self.listen_state(self.onInfraRedChange, str(self.args['infrared_entity']))
        self.log("Audio Sensor Entity: {}".format(self.audio_entity))
        self.log("Motion Sensor Entity: {}".format(self.motion_entity))
        #initialize the CGI Controller
        await self.init_controller(None)
        #start the app without IR.
        await self.setInfraRed("off")
        self.run_in(self.cgi_controller, 0)
    
    async def onInfraRedChange(self, entity, attribute, old, new, kwargs):
        await self.setInfraRed(new)
    
    async def init_controller(self, kwargs):
        try:
            #set Motion Detection to Enable
            url = "http://%s:88//cgi-bin/CGIProxy.fcgi?cmd=setMotionDetectConfig1&isEnable=1&snapInterval=1&schedule0=281474976710655&schedule1=281474976710655&schedule2=281474976710655&schedule3=281474976710655&schedule4=281474976710655&schedule5=281474976710655&schedule6=281474976710655&x1=0&y1=0&width1=10000&height1=10000&sensitivity1=1&valid1=1&linkage=6&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
            time.sleep(1)

            #set the prerecord
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=setAlarmRecordConfig&usr=%s&pwd=%s&isEnablePreRecord=%s&preRecordSecs=%s&alarmRecordSecs=10" % (self.ip, self.usr, self.pwd, self.prerecord, self.prerecordtime)
            response = requests.get(url)
            time.sleep(1)
            
            #set the autio volume to 100
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=setAudioVolume&volume=100&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
            time.sleep(1)

            #get the record path and free space
            #url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=getRecordPath&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            #response = requests.get(url)
            #time.sleep(1)

            #setInfraLedConfig to Manual Mode
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=setInfraLedConfig&mode=1&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
        except Exception as ex:
            self.log("Exception while setting the Foscam Controller %s " % ex)
        
    async def cgi_controller(self, kwargs):
        try:
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=getDevState&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
            doc = xmltodict.parse(response.content)['CGI_Result']
            #process the results
            if 'motionDetectAlarm' in doc:
                await self.setMotionDetectStatus(doc['motionDetectAlarm'][0])
            if 'soundAlarm' in doc:
                await self.setAudioStatus(doc['soundAlarm'][0])
        except Exception as ex:
            self.log(str(ex), level="ERROR")
        finally:
            self.run_in(self.cgi_controller, self.interval)

    async def setInfraRed(self, new_value):
        if new_value == "on" and not self.infrared_on:
            # set infrared to Automatic mode
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=setInfraLedConfig&mode=0&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
            self.infrared_on = True
        elif self.infrared_on:
            # set infrared back to Manual mode
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=setInfraLedConfig&mode=1&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
            #wait a second to adjust
            time.sleep(1)
            # Disable the infrared light
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=closeInfraLed&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
            self.infrared_on = False

    async def setAudioStatus(self, audio_status):
        try:
            if audio_status in ["0","1"]:
                self.set_state(self.audio_entity, state = "off")
            else:
                self.set_state(self.audio_entity, state = "on")  
        except Exception as ex:
            self.log("Exception while setting the audio status {}".format(ex))
    
    async def setMotionDetectStatus(self, motion_status):
        try:
            if motion_status in ["0","1"]:
                self.set_state(self.motion_entity, state = "off")
            else:
                self.set_state(self.motion_entity, state = "on")  
        except Exception as ex:
            self.log("Exception when setting the motion detection status {}".format(ex))