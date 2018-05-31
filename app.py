# -*- coding: utf-8 -*-
from flask import Flask, request, Response, send_from_directory, send_file
import json
import threading
import requests
import os
import tarfile
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './traces/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.debug = True

CALLBACK_URL = ''
FAKE_STATE=''

@app.route('/api/reset', methods=['GET'])
def reset():
    global FAKE_STATE
    FAKE_STATE = 'Connected'
    return Response('OK',200)

@app.route('/api/cancel', methods=['GET'])
def cancel():
    global FAKE_STATE
    FAKE_STATE = 'Cancelling'
    return Response('OK',200)
    
@app.route('/api/init', methods=['POST'])
def init():
    '''
    {
        'callback_url':'localhost/callback:5001'
    }
    '''
    config = json.loads(request.get_json())

    if all([key in config.keys() for key in ['callback_url']]):
        global CALLBACK_URL
        CALLBACK_URL = config['callback_url']
        global FAKE_STATE
        FAKE_STATE = 'NotConnected'
        return Response('OK',200)
    else:
        return Response('Bad Request',404)

@app.route('/api/connect', methods=['GET'])
def connect():
    global FAKE_STATE
    FAKE_STATE = 'Connected'
    return Response('OK',200)

@app.route('/api/disconnect', methods=['GET'])
def disconnect():
    global FAKE_STATE
    FAKE_STATE = 'NotConnected'
    return Response('OK',200)

@app.route('/api/scan', methods=['POST'])
def scan():
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
    # TODO: check if json exist
    scan_config = json.loads(request.get_json())
    
    if all([key in scan_config.keys() for key in ['scan_id','trace_config','instrument_config','probe_config']]):
        # TODO: create mock for instrument and probe configs
        threading.Thread(scan_mockup, name='scanner',args=(scan_config['trace_config'],False,scan_config['scan_id'])).start()
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

    To consider:
    Cover basic gcode commands with high level commands - in order to make it easier to use by non experienced user.
    '''
    # TODO: check if json exist
    command = json.loads(request.get_json())

    if all([key in command.keys() for key in ['command']]):
        
        data = {
            'response': 'OK\n'
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

@app.route('/api/traces/',methods=['GET'])
def traces():
    data = {
        'traces':os.listdir('./traces/')
        }
    return Response(json.dumps(data), status=200, mimetype='application/json')

@app.route('/api/traces/<trace>',methods=['GET'])
def send_trace(trace):
    # TODO: check if trace exist
    return send_file('./traces/{}'.format(trace), mimetype='text/plain')

@app.route('/api/measurements/',methods=['GET'])
def measurements():
    data = {
        'measurements':os.listdir('./data/')
        }
    return Response(json.dumps(data), status=200, mimetype='application/json')

@app.route('/api/measurements/<measurement>',methods=['GET'])
def send_measurement(measurement):
    # TODO: check if measurement exist
    archive_filename = './data/{}.tar.gz'.format(measurement)
    with tarfile.open(archive_filename,'w:gz') as tar:
        for filename in os.listdir('./data/{}'.format(measurement)):
            tar.add(filename)
    return send_from_directory('./data',archive_filename, as_attachment=True, mimetype='application/gzip')

# wywoływane przez NFS aby uaktualnić stan pomiaru
def callback_handler(measurement_no, total):
    try:
        resp = requests.post(CALLBACK_URL,json=json.dumps({'measurement_no':measurement_no,'total':total}),timeout=1)
    except Exception:
        pass

def scan_mockup(trace_config, verbose, scan_id):
    global FAKE_STATE
    for i in range(100):
        if FAKE_STATE == 'Cancelling':
            break
        callback_handler(i,100)
        time.sleep(1)
    FAKE_STATE = 'Postprocessing'
    for i in range(5):
        time.sleep(1)
    FAKE_STATE = 'Connected'

# set the secret key.  keep this really secret:
app.secret_key = b'\xcb\xd9\x99\xbf\xd6\xda\xc4\xd2\xc8\x80\\\x0e\xd0\x17\xaa\xda\xcd\x91\x8al4\xa2\xe2\xfd'
