#!/usr/bin/env python3
"""
Scripts for storing data into Influxdb with the Donkeycar

author: Rainer Bareiß, 2020
many thanks to the Parking Lot Nerds team & 
especially Paul for valuable hints how to code this
many thank to Ed Murphy for helping to make this code thread-safe & refactoring

specify your user credentials for InfluxDB in ./bashrc
export INFLUXDB_MYUSER='<user>'
export INFLUXDB_MYPASSWORD='<password>'

sample dataset

{'measurement': 'DonkeySimulator', 'tags': 
    {'car': 'PLN_8', 'race': 'training'}, 
    'time': 1642313981321035845, 
    'fields': {
        'user/angle': 0.048982207708975496, 
        'user/throttle': -0.0, 
        'pos/pos_x': 9.400879, 
        'pos/pos_y': 4.396799, 
        'pos/pos_z': 39.22294, 
        'pos/speed': 22.31289, 
        'pos/cte': -6.098797, 
        'gyro/gyro_x': -0.002858781, 
        'gyro/gyro_y': 0.001344273, 
        'gyro/gyro_z': -0.0006103102, 
        'accel/accel_x': -1.828861, 
        'accel/accel_y': -1.58003, 
        'accel/accel_z': 0.4892349, 
        'vel/vel_x': -0.497963, 
        'vel/vel_y': -0.04933339, 
        'vel/vel_z': 22.30728, 
        'pilot/angle': -0.42171603441238403, 
        'pilot/throttle': 0.7117862701416016, 
        'istep': 152
        }
    }


"""

import os
import threading
import time
import donkeycar as dk

from influxdb import InfluxDBClient
import json

# Server & ports
INFLUX_HOST   = "127.0.0.1"
INFLUX_PORT   = 8086
INFLUXDB_NAME = "plnracing1"

class InfluxController(object):
    '''
    store actual simulator data into influxdb
    '''
    def __init__(self, path, inputs=None, types=None, user_meta=[]):
        # standard variables
        print("setting up part: influx...")

        self.inputs    = inputs
        self.types     = types
        self.user_meta = user_meta
        self.istep     = 0
        self.isaved    = 0

        # setup influxdb
        self.influx_user     = os.environ['INFLUXDB_MYUSER']
        self.influx_password = os.environ['INFLUXDB_MYPASSWORD']
        databasename         = INFLUXDB_NAME
        self.dbclient        = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, self.influx_user, self.influx_password, databasename)
        self.dbclient.drop_database(databasename)
        self.dbclient.create_database(databasename)
        
        self.lock = threading.Lock()
        self.json_body = []  # buffer for 
        self.running = True

    def add_record(self, one_json_body):
        #print("influx: add_record")
        #print(f"self.lock: {self.lock}")
        if one_json_body:
            #
            # make sure we access self.json_body safely.
            # This will block until it is safe to append'
            #
            #print("influx: add_record: adding record", one_json_body)
            with self.lock:
                self.dbclient.get_list_database()
                self.json_body.append(one_json_body)
                #print(one_json_body) #rb
    
    def write_records(self):
        #
        # make sure we access self.json_body in
        # a threadsafe manner.
        # This will not block:  
        # - If it can't write then it will return 0.  
        # - If it can write then it will return the 
        #   number of records that were written
        # After a successful write the self.json_body
        # buffer is cleared so these records are
        # not written again.
        #
        count = 0
        if self.lock.acquire(blocking=False):
            try:
                count = len(self.json_body)
                if count > 0:
                    self.dbclient.write_points(self.json_body)
                    self.json_body = []  # empty the buffer
            finally:
                self.lock.release()
        return count
        
    def update(self):
        #print("influx: update")
        while self.running:
            self.isaved += self.write_records()

    def run(self, *args):
        #print("influx: run")
        if self.running:
            self.run_threaded(*args)
            self.write_records() #rb
        
    def run_threaded(self, *args):
        #print("influx: run_threaded")
        if self.running:
            #print("influx: run_threaded: starting thread")
            # prepare record
            assert len(self.inputs) == len(args)
            record = dict(zip(self.inputs, args))
            
            # get rid of non-numeric fields
            del record["cam/image_array"]
            del record["user/mode"]
            
            # influxdb complains about zero integers when field is already a float
            #print("influx: run_threaded: record:", record) #rb
            for i in record:
                if record[i] != None:
                    record[i] = float(record[i])
                elif record[i] == None:
                    record[i] = 999999999.0 # catch case of values is still "None"

            # count the datasets saved
            record["istep"] = self.istep
            
            # prepare payload for influxdb
            this_json_body = {
                            'measurement': 'DonkeySimulator', 
                            'tags': {
                                'car':'PLN_8',
                                'race':'training'
                            },
                            'time':'2020-05-10T13:11:00Z', # dummy timestamp
                            'fields':'json_packet_placeholder'
                        }

            # InfluxDB needs nanoseconds since the epoch as timestamp 
            this_json_body["time"]   = time.time_ns()

            # populate the fields we got from DonkeySim
            this_json_body["fields"] = record

            #
            # append this payload so it can be written
            # in the update thread
            #
            #print("influx: run_threaded: adding record", this_json_body)
            self.add_record(this_json_body)
            #print(this_json_body)

            self.istep += 1
            
    def shutdown(self):
        #print("influx: shutdown")
        self.running = False
