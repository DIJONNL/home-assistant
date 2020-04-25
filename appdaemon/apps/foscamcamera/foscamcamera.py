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
        self.log(dir(self))
        #self.log(">> {}".format(str(self.name)))
        self.ip = self.args['foscam_ip']
        self.usr = self.args['foscam_username']
        self.pwd = self.args['foscam_password'] 
        self.interval = self.args['interval'] if 'interval' in self.args else 5
        self.log("Foscam Camera {} settings: User {} and Pwd {} with interval {}".format(self.ip, self.usr, self.pwd, self.interval))
        self.current_satus = None
        self.run_in(self.cgi_controller, 0)
    
    async def cgi_controller(self, kwargs):
        try:
            url = "http://%s:88/cgi-bin/CGIProxy.fcgi?cmd=getDevState&usr=%s&pwd=%s" % (self.ip, self.usr, self.pwd)
            response = requests.get(url)
            doc = xmltodict.parse(response.content)['CGI_Result']
            if self.current_satus is not None:
                #search for the difference in keys
                differences = [i for i in list(doc) if self.current_satus.get(i) != doc.get(i)]
                if differences:
                    self.log("Difference in {}".format(str(differences)))
            self.current_satus = doc
        except Exception as ex:
            self.log(str(ex), level="ERROR")
        finally:
            self.run_in(self.cgi_controller, self.interval)