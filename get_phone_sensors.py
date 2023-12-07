# ---------------- TEMPLATE ---------------------------------------
# This is a template to help you start writing PythonBridge code  -
# -----------------------------------------------------------------

import rtmaps.core as rt
import rtmaps.reading_policy
import rtmaps.types
from rtmaps.base_component import BaseComponent  # base class

import websocket
import json
from functools import partial
import threading

# Python class that will be called from RTMaps.
class rtmaps_python(BaseComponent):
    
    # Constructor has to call the BaseComponent parent class
    def __init__(self):
        BaseComponent.__init__(self)  # call base class constructor
        
        # We have no inputs so we use Sampling to stay reactive to shutdown
        self.force_reading_policy(rtmaps.reading_policy.SAMPLING)
        

    def create_websocket_connection(self, url, callback):
        ws = websocket.WebSocketApp(url, on_message=callback)
        
        # Append this websocket to the list
        self.websockets.append(ws)

        # blocking call
        ws.run_forever() 
    
    # make connection and start recieving data on sperate thread
    def connect(self, url, callback):
        thread = threading.Thread(target=self.create_websocket_connection, args=(url, callback) )
        thread.start()
        
    def write_sensor(self, name, ws, message):
        values = json.loads(message)['values']
        self.write(name, values)
        
    def write_gps(self, ws, message):
        values = json.loads(message)
        self.write("gps", [values['longitude'], values['latitude'], values['altitude'] ])

    def Dynamic(self):          
        self.add_property("ip", "192.168.1.6")
        self.add_property("port", 8080)
        self.add_property("use_accelerometer", True)
        self.add_property("use_gyroscope", False)
        self.add_property("use_gps", False)
        
        if self.get_property("use_accelerometer"):
            self.add_output("accelerometer", rtmaps.types.FLOAT64)
            
        if self.get_property("use_gyroscope"):
            self.add_output("gyroscope", rtmaps.types.FLOAT64)
            
        if self.get_property("use_gps"):
            self.add_output("gps", rtmaps.types.FLOAT64)
            

# Birth() will be called once at diagram execution startup
    def Birth(self):
        # Storing websockets in a list
        self.websockets = []
        
        if self.get_property("use_accelerometer"):
            full_request = "ws://" + self.get_property("ip") + ":" + str(self.get_property("port")) +  "/sensor/connect?type=android.sensor." + "accelerometer"
            self.connect(full_request, partial(self.write_sensor, "accelerometer"))
            
        if self.get_property("use_gyroscope"):
            full_request = "ws://" + self.get_property("ip") + ":" + str(self.get_property("port")) +  "/sensor/connect?type=android.sensor." + "gyroscope"
            self.connect(full_request, partial(self.write_sensor, "gyroscope"))
            
        if self.get_property("use_gps"):
            full_request = "ws://" + self.get_property("ip") + ":" + str(self.get_property("port")) +  "/gps"
            self.connect(full_request, self.write_gps)
                    

# Core() is called every time you have a new inputs available, depending on your chosen reading policy
    def Core(self):
        pass
            
        
# Death() will be called once at diagram execution shutdown
    def Death(self):     
        for sockets in self.websockets:
            sockets.close()
            
