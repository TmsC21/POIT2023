from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect
import MySQLdb       
import math
import time
import configparser as ConfigParser
import random
import serial

async_mode = None

app = Flask(__name__)


config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')
print(myhost)


app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 


def background_thread(args):
    count = 0  
    dataCounter = 0
    dataList = []
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
    ser=serial.Serial("/dev/ttyACM0",9600)
    ser.baudrate=9600
    
    while True:
        try:
            arr = ser.readline().strip().decode( "utf-8" ).split("|", 3)
            if float(arr[2]) < 50:
                print("Temp:"+arr[0]+" Him:"+arr[1]+" Dist:"+arr[2])
                socketio.emit('my_response', {'t': arr[0], 'h': arr[1],'d' :arr[2]},namespace='/test') 
        except Exception:
            pass  # or you could use 'continue'
    db.close()

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
   # emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=81, debug=True)
