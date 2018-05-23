# -*- coding: utf-8 -*-
from flask import Flask, request, Response
import json
import threading
import requests
import time

app = Flask(__name__)
app.debug = True

FAKE_STATE=''
CALLBACK_URL = ''

@app.route('/api/configure', methods=['POST'])
def configure():
    '''
    Allows to make all the configuration actions:
     - initializing (on pw-nfs/app start)
     - connecting
     - disconnecting
     - reseting grbl
     - ... ?

     request json examples:
     {
         'action':'init'
         'callback_url':'localhost/callback:5001'
     }
     {
         'action':'connect'
     }
     {
         'action':'disconnect'
     }
     {
         'action':'reset'
     }
    '''

    config = json.loads(request.get_json())

    global FAKE_STATE
    global CALLBACK_URL
    if all([key in config.keys() for key in ['action','callback_url']]) and config['action'] == 'init':
        CALLBACK_URL = config['callback_url']
        FAKE_STATE = 'NotConnected'
        return Response('OK',200)
    elif all([key in config.keys() for key in ['action']]) and config['action'] == 'connect':
        FAKE_STATE = 'Idle'
        return Response('OK',200)
    elif all([key in config.keys() for key in ['action']]) and config['action'] == 'disconnect':
        FAKE_STATE = 'NotConnected'
        return Response('OK',200)
    elif all([key in config.keys() for key in ['action']]) and config['action'] == 'reset':
        return Response('OK',200)
    else:
        return Response('Bad Request',404)
    


@app.route('/api/scan/new', methods=['POST'])
def new_scan():
    '''
    Allows to start a new scan 

    request json example:
     {
         'scan_id':'dc-boost-200MHz-2mm'
         'trace_config':'dc-boost-2mm'
         'instrument-config':'200MHz'
         'probe_config':'Ez-150mm-001'
     }
    '''

    scan_config = json.loads(request.get_json())
    
    global FAKE_STATE
    if all([key in scan_config.keys() for key in ['scan_id','trace_config','instrument_config','probe_config']]):
        FAKE_STATE = 'Scanning'
        threading.Thread(target=scan_mockup, name='scanner',args=(scan_config['trace_config'],False,scan_config['scan_id'])).start()
        return Response('Accepted',202)
    else:
        return Response('Bad Request',404)
    

@app.route('/api/command',methods=['POST'])
def write_command():
    '''
    Allows to write grbl command.
    request json example:
     {
         'command':'G0 X100.0 Y120.0 Z88.2 F1500'
     }
    '''
    command = json.loads(request.get_json())
    if all([key in command.keys() for key in ['command']]):
        response = 'fake-OK\n'
        data = {
            'response': response
        }
        return Response(json.dumps(data), status=200, mimetype='application/json')
    else:
        return Response('Bad Request',404)

@app.route('/api/state',methods=['GET'])
def state():
    data = {
        'state': FAKE_STATE
    }
    return Response(json.dumps(data), status=200, mimetype='application/json')


def callback_handler(measurement_no, total):
    requests.post(CALLBACK_URL,json=json.dumps({'measurement_no':measurement_no,'total':total}))

def scan_mockup(trace_config, verbose, scan_id):
    global FAKE_STATE
    for i in range(100):
        callback_handler(i,100)
        time.sleep(1)
    FAKE_STATE = 'Postprocessing'
    for i in range(5):
        time.sleep(1)
    FAKE_STATE = 'Idle'

# set the secret key.  keep this really secret:
app.secret_key = b'\xcb\xd9\x99\xbf\xd6\xda\xc4\xd2\xc8\x80\\\x0e\xd0\x17\xaa\xda\xcd\x91\x8al4\xa2\xe2\xfd'
