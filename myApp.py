from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect
import MySQLdb       
import math
import time
import configparser as ConfigParser
import random
import serial
import os

async_mode = None

app = Flask(__name__)


config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')


app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 


def background_thread(args):
    count = 0  
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
    ser=serial.Serial("/dev/ttyACM0",9600)
    ser.baudrate=9600
    dataList = []
    dataCounter = 0
    while True:
        try:
            arr = ser.readline().strip().decode( "utf-8" ).split("|", 3)
            if args:
              dbV = dict(args).get('db_value')
              A = dict(args).get('A')
            else:
              dbV = 'nieco'
              A = 50
            B = dict(args).get('B')
            print("B:")
            print(B)
            print("A:")
            print(A)
            print("Dist:")
            print(arr[2])
            print(arr[2] < A)
            if arr[2] < A:
                print("Temp:"+arr[0]+" Him:"+arr[1]+" Dist:"+arr[2])
                print(args)
                socketio.emit('my_response', {'count':count,'t': arr[0], 'h': arr[1],'d' :arr[2]},namespace='/test') 
                dataCounter +=1
                count +=1
                socketio.sleep(2)
                print(dbV)
                if dbV == 'start':
                  dataDict = {'count':dataCounter,'t': arr[0], 'h': arr[1],'d' :arr[2]}
                  dataList.append(dataDict)
                else:
                  if len(dataList)>0:
                    fuj = str(dataList).replace("'", "\"")
                    if B:
                        print(fuj)
                        cursor = db.cursor()
                        cursor.execute("SELECT MAX(id) FROM graph")
                        maxid = cursor.fetchone()
                        print("DONE!!!"+str(maxid))
                        cursor.execute("INSERT INTO graph (id, hodnoty) VALUES (%s, %s)", (maxid[0] + 1, fuj))
                        db.commit()
                    else:
                        fo = open("static/files/test.txt","a+") 
                        fo.write("%s\r\n" %fuj)
                        fo.close()
                    
                  dataList = []
                  dataCounter = 0
                
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

@app.route('/dbdata/<string:num>', methods=['GET', 'POST'])
def dbdata(num):
  db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
  cursor = db.cursor()
  print(num)
  cursor.execute("SELECT hodnoty FROM  graph WHERE id=%s", num)
  rv = cursor.fetchone()
  return str(rv[0])
  
@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']  
    session['B'] = message['valueRadio']  
    emit('my_response',
         {'data': message['value'], 'count': session['receive_count'], 'valueRadio': session['valueRadio']})
  
@socketio.on('db_event', namespace='/test')
def db_message(message):   
    session['db_value'] = message['value']   

@app.route('/read/<string:num>', methods=['GET', 'POST'])
def readmyfile(num):
    fo = open("static/files/test.txt","r")
    rows = fo.readlines()
    return rows[int(num)-1] 

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=81, debug=True)
