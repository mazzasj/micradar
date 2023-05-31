import  serial, time 
import  RPi.GPIO as GPIO
import threading
import queue
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Flask + SocketIO initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkeyree'
socketio = SocketIO(app)

#serial init
ser  =  serial.Serial(port  =  "/dev/serial0" , baudrate = 115200 ) # timeout = 1 removed
if  (ser.isOpen()  ==  False):
    ser. open ()                                       # check and open Serial0
ser.flushInput()                                       # clear the UART Input buffer
ser.flushOutput()                                      # clear the UART output buffer


# Create a Queue object to allow communication between threads
packet_queue = queue.Queue()

def checksum_calc(packet): #calculate the checksum of the packet and add it to the end of the packet
    header = bytearray([0x53] + [0x59])
    packet[0:0] = header #add header to the beginning of the packet so it can be evaluated

    checksum = sum(packet) % 256
    packet.append(checksum)
    packet.append(0x54) #add tailings
    packet.append(0x43)
    return packet

def good_checksum(packet): #check if the checksum is correct
    recv_checksum = packet[-3] #store the checksum byte of the packet
    packet = packet[0:-3] #remove tailings including the checksum
    checksum = sum(packet) % 256 #calculate the checksum of the packet
    
    if checksum == recv_checksum:
        #print("good checksum")
        return True
    else:
        print("bad checksum")
        print("expected: ", checksum)
        print("received: ", recv_checksum)
        return False
    

def human_presence_switch(x):
    human_presence = bytearray([0x80] + [0x00] + [0x00] + [0x01])
    if x == 1:
        human_presence.append(0x01)
    else:
        human_presence.append(0x00)
    checksum_calc(human_presence)
    send(human_presence)

def send(packet):
    #checksum_calc(packet)
    ser.write(packet)
    print("sent", list(map(hex, packet)))

def strip_header(packet):
    packet = packet[2:-3]
    return packet

def get_packet_data(packet): #strips packet headers and returns the first 2 packet identifiers and the data byte
    clean_packet = strip_header(packet)
    packet_data = []
    packet_data.append(clean_packet[0])
    packet_data.append(clean_packet[1])
    packet_data.append(clean_packet[-1])
    return packet_data

@app.route('/')
def index():
    return render_template('index.html')

def get_packet():
    packet_buffer = []
    packet = []
    ser.flushInput()                    # Clear UART Input buffer
    ser.flushOutput()                   # Clear UART Output buffer
    
    while True:
        serial_in = ser.read() # read 1 byte of the rec buffer
        if serial_in:
            packet_buffer.append(serial_in[0]) #build a packet buffer
            
            if len(packet_buffer) > 1 and packet_buffer[-1] == 0x43 and packet_buffer[-2] == 0x54: #found end of packet
                for i in range(len(packet_buffer)): #find the beginning of the packet
                    if packet_buffer[-i] == 0x53 and packet_buffer[-i+1] == 0x59:
                        packet = packet_buffer[-i:] #excludes any fragmented data outside packet headers
                        packet_queue.put(packet) #shares packet data with the main program
                        packet_buffer.clear()
                        break

def sensor_data_emitter():
    while True:
        if not packet_queue.empty():
            packet = packet_queue.get()
            now = time.perf_counter_ns()
            good_packet = good_checksum(packet)
            if good_packet == True:
                packet_data = get_packet_data(packet)
                if packet_data[0] == 0x81:
                    if packet_data[1] == 0x3:  # heartbeat packet
                        sensor_data = {
                            'heart_rate': packet_data[2],
                            'timestamp': now
                        }
                    elif packet_data[1] == 0x6:  # respiration packet
                        sensor_data = {
                            'respiration': packet_data[2],
                            'timestamp': now
                        }
                    else:
                        continue
                    socketio.emit('new_sensor_data', sensor_data)
        time.sleep(0.02)

def destroy():
    ser.close ()                                          # Closes the serial port
    print ("Serial connection closed")

if __name__ == '__main__':
    try:
        #Initialize data stream
        human_presence_switch(1)
        hb_query = bytearray([0x01] + [0x01] + [0x00] + [0x01] + [0x0F])
        checksum_calc(hb_query)
        send(hb_query)

        # create the threads to keep serial open
        packet_thread = threading.Thread(target=get_packet)
        data_thread = threading.Thread(target=sensor_data_emitter)

        # start threading
        packet_thread.start()
        data_thread.start()

        # run flask app
        socketio.run(app, host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        destroy()
    finally:
        destroy()
