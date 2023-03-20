import machine
import time

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
    if x == 1:
        human_presence_enable = bytearray([0x80] + [0x00] + [0x00] + [0x01] + [0x01]) #last bit turns on detection reports
        checksum_calc(human_presence_enable)
        uart.write(human_presence_enable)
    else:
        human_presence_disable = bytearray([0x80] + [0x00] + [0x00] + [0x01] + [0x00]) #last bit turns on detection reports
        checksum_calc(human_presence_disable)
        uart.write(human_presence_disable)

def send(packet):
    checksum_calc(packet)
    uart.write(packet)

checksum_calc(hb_query) #append checksum to packet

good_checksum(hb_query)



responses = set()
frame_buffer = []
time_last = 0


time.sleep(1)

human_presence_switch(0)

while True:
    # Wait for a response
    response = uart.read(1)
    if response:
        frame_buffer.append(response[0])
        if frame_buffer[-1] == 0x43 and frame_buffer[-2] == 0x54: # check if the frame is complete
            for i in range(len(frame_buffer)): #find the beginning of the frame
                if frame_buffer[i] == 0x53 and frame_buffer[i+1] == 0x59:
                    good_checksum(frame_buffer) #check received packet checksum
                    #print(list(map(hex,frame_buffer))) #print the entire frame in hex format
                    if int(frame_buffer[-4]) != 1 and int(frame_buffer[-4]) != 0:
                        #print(hex(frame_buffer[2]))
                        if frame_buffer[2] == 0x80: # and int(frame_buffer[3]) == 1):
                            print("=========================================")
                            print("control: ", hex(frame_buffer[2]))
                            print("command: ", hex(frame_buffer[3]))
                            print("data: ", int(frame_buffer[-4]))
                frame_buffer.clear()
                time_now = time.time()
                if time_now - time_last > 10:
                    send(hb_query)
                    time_last = time_now
                    print("sent heartbeat query")
                break
                    

        