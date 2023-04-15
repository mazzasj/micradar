from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
socketio = SocketIO(app)

def read_sensor_data():
    # Replace this function with actual code to read data from the respiratory radar
    return {
        'heart_rate': random.randint(60, 100),
        'respiration': random.randint(12, 20),
        'timestamp': time.time()
    }

@app.route('/')
def index():
    return render_template('index.html')

def sensor_data_emitter():
    while True:
        sensor_data = read_sensor_data()
        socketio.emit('new_sensor_data', sensor_data)
        time.sleep(1)

if __name__ == '__main__':
    data_thread = threading.Thread(target=sensor_data_emitter)
    data_thread.start()
    socketio.run(app, debug=False)
