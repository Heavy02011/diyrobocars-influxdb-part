#!/usr/bin/env python3
"""
Scripts for storing data into Influxdb with the Donkeycar

author: Rainer Bareiß, 2020
many thanks to the Parking Lot Nerds team & 
especially Paul for valuable hints how to code this

specify your user credentials for InfluxDB in ./bashrc
export INFLUXDB_MYUSER='<user>'
export INFLUXDB_MYPASSWORD='<password>'

"""

import os
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

        # setup influxdb
        self.influx_user     = os.environ['INFLUXDB_MYUSER']
        self.influx_password = os.environ['INFLUXDB_MYPASSWORD']
        databasename         = INFLUXDB_NAME
        self.dbclient        = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, self.influx_user, self.influx_password, databasename)
        self.dbclient.drop_database(databasename)
        self.dbclient.create_database(databasename)
        
    def update(self):
        pass

    def run(self, *args):
        self.poll()
        return self.run_threaded()
        
    def run_threaded(self, *args):
        # prepare record
        assert len(self.inputs) == len(args)
        record = dict(zip(self.inputs, args))
        
        # get rid of non-numeric fields
        del record["cam/image_array"]
        del record["user/mode"]
        
        # influxdb complains about zero integers when field is already a float
        for i in record:
            record[i] = float(record[i])

        # count the datasets saved
        record["istep"] = self.istep
        
        # prepare payload for influxdb
        json_body_fields = { 'fields': 'placeholder'}
        self.json_body = {
                        'measurement': 'DonkeySimulator', 
                        'tags': {
                            'car':'PLN_8',
                            'race':'training'
                        },
                        'time':'2020-05-10T13:11:00Z', # dummy timestamp
                        'fields':'json_packet_placeholder'
                    }

        # InfluxDB needs nanoseconds since the epoch as timestamp 
        self.json_body["time"]   = time.time_ns()

        # populate the fields we got from DonkeySim
        self.json_body["fields"] = record
        self.json_body = [self.json_body]
        #print(self.json_body)
        
        # write json to influxdb
        if self.istep > 0:
            self.dbclient.write_points(self.json_body)
        self.istep += 1
    
    def shutdown(self):
        self.on = False
        
if __name__ == '__main__':
    pass
