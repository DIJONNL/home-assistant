
import hassapi as hass
import requests, sys
from datetime import datetime
import time

class tradfristate(hass.Hass):
    def initialize(self):
        # Maybe access an async library to initialize something
        self.log(">> {}".format(str(self.name)))
        self.run_in(self.hass_cb, 1)

    def hass_cb(self, kwargs):
        # do some async stuff
        self.log("test1")
        for light in self.entities.light.items():
            self.log("")
            self.log(light[0]['entity_id'])
            self.log(dir(light))
            #self.log(self.get_state(light, attribute="state"))
        #self.log(dir(self))
        self.log("test2")
        

