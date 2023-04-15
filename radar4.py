#this code writes movement data from the RaDAR to a small LCD display

import machine
import time
from ssd1306 import SSD1306_I2C
import math

data_log = open("data_log.txt", "w")

data_log801 = open("data_log801.txt", "w")
data_log802 = open("data_log802.txt", "w")
data_log803 = open("data_log803.txt", "w")
data_log811 = open("data_log811.txt", "w")
data_log812 = open("data_log812.txt", "w")
data_log813 = open("data_log813.txt", "w")
data_log814 = open("data_log814.txt", "w")
data_log815 = open("data_log815.txt", "w")
data_log816 = open("data_log816.txt", "w")
data_log817 = open("data_log817.txt", "w")
data_log818 = open("data_log818.txt", "w")
data_log819 = open("data_log819.txt", "w")



#create i2c object for display
i2c = machine.I2C(1, sda=machine.Pin(26), scl=machine.Pin(27))
display = SSD1306_I2C(128, 32, i2c)

display.fill(0)
display.text('BEE!', 0, 0, 1)
display.text('  Technologies', 0, 10, 1)
display.show()
time.sleep(3)
display.fill(0)
display.show()

# Set the TX and RX pins for RaDAR
tx_pin = machine.Pin(16)
rx_pin = machine.Pin(17)

# Configure the UART port
uart = machine.UART(0, 115200, tx=tx_pin, rx=rx_pin)
uart.init(115200, bits=8, parity=None, stop=1)

# Create heartbeat query packet
hb_query = bytearray([0x01] + [0x01] + [0x00] + [0x01] + [0x0F]) # [SUM] + [0x54] + [0x43])

def checksum_calc(packet): #calculate the checksum of the packet and add it to the end of the packet
    header = bytearray([0x53] + [0x59])
    packet[0:0] = header #add header to the beginning of the packet so it can be evaluated

    checksum = sum(packet) % 256
    packet.append(checksum)
    packet.append(0x54) #add tailings
    packet.append(0x43)
    return packet

def good_checksum(packet): #check if the checksum is correct
    recv_checksum = packet[-3] #store the checksum bit of the packet
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
        send(human_presence)
    else:
        human_presence.append(0x00)
        send(human_presence)

def send(packet):
    checksum_calc(packet)
    uart.write(packet)

def strip_header(packet):
    packet = packet[2:-3]
    return packet    



data_graph_y = [] #list of data points to be graphed 
event_time_x = [] #list of time points to be graphed
prev_data_graph_y = [] #list to create persistent graph
prev_event_time_x = [] #list to create persistent graph
packet_buffer = [] #create buffer for data packets from radar
time_last = 0


human_presence_switch(0)

time.sleep(1)

time_start = time.ticks_ms()

while True:
    # Wait for a response from the RaDAR
    response = uart.read(1)
    if response:
        packet_buffer.append(response[0])
        print(hex(response[0]))
        if packet_buffer[-1] == 0x43 and packet_buffer[-2] == 0x54: # check if the packet is complete
            for i in range(len(packet_buffer)): #find the beginning of the packet
                print("i: ", i)
                if packet_buffer[-i] == 0x53 and packet_buffer[-i+1] == 0x59:
                    if not good_checksum(packet_buffer): #check received packet checksum
                        print("bad packet: ", list(map(hex, packet_buffer)), packet_buffer[-1])
                        packet_buffer.clear()
                        break                    
                    packet_buffer = strip_header(packet_buffer) #remove header and checksum for readability
                    print(list(map(hex, packet_buffer)), packet_buffer[-1]) #print the packet and final data bit in decimal
                    if packet_buffer[0] == 0x82 and packet_buffer[1] == 0x3: # filter this packet type so its data can be logged
                        #print("=========================================")
                        #print("control: ", hex(packet_buffer[0]))
                        #print("command: ", hex(packet_buffer[1]))

                        #print("data: ", int(packet_buffer[-1]))
                        event_time_x.append(int(round((time.ticks_ms() - time_start)/71))) #format data to display
                        #data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        #data_file81.write(data)
                        #data_file81.flush()
                        #output waveform to display
                        data_graph_y.append(int(round(packet_buffer[-1])/240*19*(5/3))-7) #format data to display
                       # print(data_graph_y[-1]*5/3-7)
                        
                        
                        last_event_time = event_time_x[-1]
                        if last_event_time < 125 and len(event_time_x) > 1:
                            display.fill(0)
                            for i in range(len(event_time_x)-1): #begin drawing the graph
                                display.line(event_time_x[i], data_graph_y[i], event_time_x[i+1], data_graph_y[i+1], 1)
                                
                            if len(prev_event_time_x) > len(event_time_x):
                                for i in range(len(event_time_x)+3,len(prev_event_time_x)-1):
                                    display.line(prev_event_time_x[i], prev_data_graph_y[i], prev_event_time_x[i+1], prev_data_graph_y[i+1], 1)   
                        if last_event_time >= 125:
                            time_start = time.ticks_ms()
                            prev_data_graph_y.clear()
                            prev_event_time_x.clear()
                            for i in range(len(event_time_x)):
                                prev_event_time_x.append(event_time_x[i])
                            for i in range(len(data_graph_y)):
                                prev_data_graph_y.append(data_graph_y[i])
                            event_time_x.clear()
                            data_graph_y.clear()                   
                        display.show()

                    if packet_buffer[0] == 0x80 and packet_buffer[1] == 0x1:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log801.write(data)
                        data_log801.flush()

                    if packet_buffer[0] == 0x80 and packet_buffer[1] == 0x2:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log802.write(data)
                        data_log802.flush()        

                    if packet_buffer[0] == 0x80 and packet_buffer[1] == 0x3:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log803.write(data)
                        data_log803.flush()                                    

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x1:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log811.write(data)
                        data_log811.flush()

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x2:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log812.write(data)
                        data_log812.flush()

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x3:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log813.write(data)
                        data_log813.flush()                                                      

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x4:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log814.write(data)
                        data_log814.flush()

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x5:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log815.write(data)
                        data_log815.flush()

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x6:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log816.write(data)
                        data_log816.flush()                                                                                  

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x7:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log817.write(data)
                        data_log817.flush()

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x8:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log818.write(data)
                        data_log818.flush()

                    if packet_buffer[0] == 0x81 and packet_buffer[1] == 0x9:
                        #print("data: ", int(packet_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(packet_buffer[-1])) + " " + str(event_time) + "\n"
                        data_log819.write(data)
                        data_log819.flush()                                                            

                packet_buffer.clear()



                #time_now = time.time()
                #if time_now - time_last > 10:
                #    send(hb_query)
                #    time_last = time_now
                    #print("sent heartbeat query")
                break
                    
# look into [0x81 0x3] and [0x80 0x3]
#[0x81 0x3] appears to be a movement detection packet which scales with the amount of movement

#[0x80 0x3] appears to be a respiration movement packet with possible heartbeat data

#[0x80 0x2] mostly 0, sometimes 3 during heavy movement

#[0x80 0x1] 

#how to start a new project?