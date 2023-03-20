import machine
import time

data_file80 = open("data80.txt", "w")
data_file81 = open("data81.txt", "w")

# Set the TX and RX pins
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



#responses = set() 
frame_buffer = []
time_last = 0

human_presence_switch(0)

time.sleep(1)

time_start = time.ticks_ms()

while True:
    # Wait for a response from the RaDAR
    response = uart.read(1)
    if response:
        frame_buffer.append(response[0])
        if frame_buffer[-1] == 0x43 and frame_buffer[-2] == 0x54: # check if the frame is complete
            for i in range(len(frame_buffer)): #find the beginning of the frame
                if frame_buffer[i] == 0x53 and frame_buffer[i+1] == 0x59:
                    good_checksum(frame_buffer) #check received packet checksum
                    frame_buffer = strip_header(frame_buffer) #remove header and checksum for readability
                    #print(list(map(hex, frame_buffer)), frame_buffer[-1]) #print the frame and final data bit in decimal
                    if frame_buffer[0] == 0x81 and frame_buffer[1] == 0x3: # filter this packet type so its data can be logged
                        #print("=========================================")
                        #print("control: ", hex(frame_buffer[0]))
                        #print("command: ", hex(frame_buffer[1]))
                        print("data: ", int(frame_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(frame_buffer[-1])) + " " + str(event_time) + "\n"
                        data_file81.write(data)
                        data_file81.flush()
                    if frame_buffer[0] == 0x80 and frame_buffer[1] == 0x3:
                        print("data: ", int(frame_buffer[-1]))
                        event_time = time.ticks_ms() - time_start
                        data = str(int(frame_buffer[-1])) + " " + str(event_time) + "\n"
                        data_file80.write(data)
                        data_file80.flush()

                frame_buffer.clear()
                #time_now = time.time()
                #if time_now - time_last > 10:
                #    send(hb_query)
                #    time_last = time_now
                    #print("sent heartbeat query")
                break
                    
# look into [0x81 0x3] and [0x80 0x3]
#[0x81 0x3] appears to be a movement detection packet which scales with the amount of movement

#[0x80 0x3] appears to be a respiration movement packet with possible heartbeat data