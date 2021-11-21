###########################################
# James Flemings
# tcp.py
# 11/06/2020
# CSCE 365
# Programming Assignment 2: TCP Client
###########################################
from socket import *
from bitstring import *
import header
import time
import random
import threading
import copy

class tcp_client():
    # all possible states for the client
    states = {'LISTEN': 0, 'SYN-SENT': 1, 'SYN-RECEIVED': 2, 
            'ESTABLISHED': 3, 'FIN-WAIT-1': 4, 'FIN-WAIT-2': 5, 
            'CLOSE-WAIT': 6, 'CLOSING': 7, 'LAST-ACK': 8, 
            'TIME-WAIT': 9, 'CLOSED': 10}

    def __init__(self, clientPort, serverPort, serverAddress, mode, state=0):
        self.state = state
        self.mode = mode
        self.clientPort = clientPort
        self.serverPort = serverPort
        self.serverAddress = serverAddress
        self.retransmissionQueue = [] # store segments that haven't been ack'd 
        self.receiveBuffer = [] # store out of order segments received of type header
        self.unAckSegments = {} # segments send, but not ack'd
        self.fullText = [] # elements of 1452 bytes to write to server in bytes
        self.cur_line = 0  # current location in textfile
        ######################## Send sequence variables
        self.send_window = 5808   # the range of sequence numbers for send
        self.send_nxt = 0      # next sequence number to use
        self.send_base = 0     # oldest unacknowledged squence number
        ######################## Recieve sequence variables
        self.rcv_window = 3*1452    # max size of receive buffer 
        self.rcv_nxt = 0      # next expected sequence number to recieve
        self.rcv_base = 0      # oldest expected but not recieved squence number 

        self.finished = False
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)
        self.clientSocket.bind(('0.0.0.0', clientPort))
        self.clientSocket.settimeout(0.4) # best: 1.1

    # setting up an initial connection with a TCP server
    # 3 step process: 
    # (1)-- client sends SYN segment to server, contains initial send sequence number and
    # no data field
    # (2)-- server sends SYN-ACK, contains intial recieve sequence (irs) and no data field
    # (3)-- client sends ACK with irs+1 in ackNum. if client is reading, no data field;
    # else send data
    def handShake(self):
        #isn = random.randint(0, 2**32-1) # initial send sequence number 

        syn = header.header(sourcePort=self.clientPort, destinationPort=self.serverPort,
                seqNum=0, ackNum=self.rcv_nxt, dataOffset=5, reserved=0,
                URG=0, ACK=0, PSH=0, RST=0, SYN=1, FIN=0, window=self.send_window,
                checkSum=0, urgPoint=0, data=None)

        self.state = self.states['SYN-SENT'] # change state from listen to syn-sent
        # client sends SYN to server

        #t = threading.Timer(0.3, self.retransmit, [self.send_nxt+1, syn, 1])
        #self.unAckSegments[self.send_nxt+1]= [t, syn]
        #t.start() 
        self.clientSocket.sendto(syn.getSegment(),
              (self.serverAddress, self.serverPort))

        while True:
            try:
                message, serverAddress = self.clientSocket.recvfrom(2048)
                serverSegment = header.header(message) # server sends SYN-ACK to client
                if serverSegment.header_components['SYN'].uint:                
                    break
            except:
                self.clientSocket.sendto(syn.getSegment(),
                    (self.serverAddress, self.serverPort))
        
        serverSegment = header.header(message) # server sends SYN-ACK to client
        self.send_nxt = serverSegment.header_components['ackNum'].uint
        self.rcv_base = serverSegment.header_components['seqNum'].uint+1
        self.send_window = serverSegment.header_components['window'].uint
        self.rcv_window = serverSegment.header_components['window'].uint
        
        segment_send = 0 # ack segment from syn-ack 
        if self.mode == 'r':
            #segment_send = header.header(sourcePort=self.clientPort,
            #        destinationPort=self.serverPort,
            #        seqNum=self.send_nxt, ackNum=self.rcv_nxt, dataOffset=5, reserved=0,
            #        URG=0, ACK=1, PSH=0, RST=0, SYN=0, FIN=0, window=self.rcv_window,
            #        checkSum=0, urgPoint=0, data=None)

            #self.send_nxt = (self.send_nxt + 1) % 2**32
            #self.clientSocket.sendto(segment_send.getSegment(),
            #        (self.serverAddress, self.serverPort))
            self.send_ack(serverSegment)
            return True, serverSegment

        elif self.fullText[self.cur_line] != b'':
            self.rcv_nxt = serverSegment.header_components['seqNum'].uint+1
            data = self.fullText[self.cur_line]
            segment_send = header.header(sourcePort=self.clientPort,
                    destinationPort=self.serverPort,
                    seqNum=self.send_nxt, ackNum=self.rcv_nxt, dataOffset=5, reserved=0,
                    URG=0, ACK=1, PSH=0, RST=0, SYN=0, FIN=0, window=self.send_window,
                    checkSum=0, urgPoint=0, data=data)

            t = threading.Timer(0.3, self.retransmit, [self.send_nxt+len(data), segment_send, 0])
            self.unAckSegments[self.send_nxt+len(data)] = [t, segment_send]
            t.start()

            self.clientSocket.sendto(segment_send.getSegment(),
                (self.serverAddress, self.serverPort))
            self.send_base = self.send_nxt
            self.send_nxt = (self.send_nxt + len(data)) % 2**32
            self.rcv_nxt = (self.rcv_nxt + 1) % 2**32
            self.cur_line += 1
            self.sendSegment() 

        else:
            self.rcv_nxt = serverSegment.header_components['seqNum'].uint+1
            self.send_fin()
            self.finished = True
            self.state = self.states['FIN-WAIT-1']
            return False, None

        self.state = self.states['ESTABLISHED']  
        return True, segment_send

    def send_ack(self, segment):
        # ackNum = (seg's seqNum + length of data) mod 2^32
        if segment.header_components['data'] != None:
            data = len(segment.header_components['data'].bytes)
            self.rcv_nxt = (segment.header_components['seqNum'].uint+data) % 2**32
        else:
            self.rcv_nxt = (segment.header_components['seqNum'].uint+1) % 2**32
        ack = header.header(sourcePort=self.clientPort,
                destinationPort=self.serverPort,
                seqNum=segment.header_components['ackNum'].uint,
                ackNum=self.rcv_nxt, dataOffset=5, reserved=0,
                URG=0, ACK=1, PSH=0, RST=0, SYN=0, FIN=0, window=self.rcv_window,
                checkSum=0, urgPoint=0, data=None)

        self.send_nxt = (self.send_nxt+1) % 2**32
        self.clientSocket.sendto(ack.getSegment(), (self.serverAddress, self.serverPort))
        return 

    def readSegment(self, segment, segments_to_write):
        seqNum = segment.header_components['seqNum'].uint
        # segment's seqNum in [rcv_base, rcv_base+N-1]
        if self.rcv_base <= seqNum and seqNum <= (self.rcv_base+self.rcv_window):
            if segment not in self.receiveBuffer: # packet was not previously received
                self.receiveBuffer.append(segment)
                self.send_ack(segment) # acknowledge that the packet is received

            if self.rcv_base == seqNum: 
                i = 0
                # segments could be out of order so go back to the start of list if  
                # recieve base is moved
                while i < len(self.receiveBuffer): 
                    cur_segment = self.receiveBuffer[i]
                    # packet sequence number == base of recieve window
                    if cur_segment.header_components['seqNum'].uint == self.rcv_base:
                        segments_to_write[self.rcv_base] = self.receiveBuffer.pop(i).header_components['data'].bytes
                    # move receive window by one segment (packet seqNum + bytes of data)
                        self.rcv_base = ((cur_segment.header_components['seqNum'].uint+
                                len(cur_segment.header_components['data'].bytes)) % 2**32)

                        i = 0
                    else:
                        i += 1

        # segment's seqNum in [rcv_base-N, rcv_base+1]
        # segment that the receiver has previously acknowledged
        else:
               self.send_ack(segment) 
        return 
    
    # received an ack, check if corresponding segment stored in send buffer
    def checkUnAck(self, segment):
        ackNum = segment.header_components['ackNum'].uint
        seqNum = segment.header_components['seqNum'].uint
        segment = self.unAckSegments.pop(ackNum, None) # if key exists, else None
        ackSegs = []
        largest = -1 
        for key, value in self.unAckSegments.items():
            if ackNum > key:
                if key > largest:
                    largest = key

                self.unAckSegments[key][0].cancel()
                ackSegs.append(key)
                self.send_base = ackNum

        for key in ackSegs:
            if key == largest and segment == None:
                segment = self.unAckSegments.pop(key)
            else:
                self.unAckSegments.pop(key)
            
        if segment != None and ackNum == (self.send_base+len(segment[1].header_components['data'].bytes)):
            segment[0].cancel()
            data = segment[1].header_components['data'].bytes
            self.send_base = (self.send_base + len(data)) % 2**32

    # after some time if the client doesn't receive an ack for a segment, then 
    # the client will retransmit the unack'd segment
    def retransmit(self, send_nxt, segment_send, i):
        if self.finished:
            return
        if i == -1:
            return
        if send_nxt in self.unAckSegments:
            t = threading.Timer(0.3, self.retransmit, [send_nxt, segment_send, 0])
            self.unAckSegments[send_nxt] = [t, segment_send]
            #newAck = BitArray('uint:32={}'.format(self.rcv_nxt))
            #segment_send.header_components['ackNum'] = newAck 
            t.start()
            self.clientSocket.sendto(segment_send.getSegment(),
                (self.serverAddress, self.serverPort))
         
    def sendSegment(self):
        while (self.send_nxt < (self.send_base + self.send_window-self.send_window/2) and
                self.cur_line != len(self.fullText)):
            data = self.fullText[self.cur_line]
            segment_send = header.header(sourcePort=self.clientPort,
                    destinationPort=self.serverPort,
                    seqNum=self.send_nxt, ackNum=self.rcv_nxt, dataOffset=5, reserved=0,
                    URG=0, ACK=0, PSH=0, RST=0, SYN=0, FIN=0, window=self.send_window,
                    checkSum=0, urgPoint=0, data=data)
            
            t = threading.Timer(0.3, self.retransmit, [self.send_nxt+len(data), segment_send, 0])
            self.unAckSegments[self.send_nxt+len(data)] = [t, segment_send] 
            t.start()

            self.clientSocket.sendto(segment_send.getSegment(),
                (self.serverAddress, self.serverPort))
            self.send_nxt = (self.send_nxt + len(data)) % 2**32
            self.rcv_nxt = (self.rcv_nxt + 1) % 2**32
            self.cur_line += 1

        return 


    def send_fin(self):
        fin = header.header(sourcePort=self.clientPort,
             destinationPort=self.serverPort,
             seqNum=self.send_nxt, ackNum=self.rcv_nxt, dataOffset=5, reserved=0,
             URG=0, ACK=1, PSH=0, RST=0, SYN=0, FIN=1, window=self.rcv_window,
             checkSum=0, urgPoint=0, data=None)
        #t = threading.Timer(0.3, self.retransmit, [self.send_nxt, fin, 0])
        #self.unAckSegments[self.send_nxt] = [t, fin]
        #t.start()
                    
        self.clientSocket.sendto(fin.getSegment(), (self.serverAddress, self.serverPort))
        return

    def closeConnection(self, segment):
        # check what state self is in
        segment_send = 0
        if self.state == self.states['CLOSE-WAIT']: # server sent FIN and we ack, so send FIN
            self.send_fin()
            self.state = self.states['LAST-ACK']

            i = 0 
            while True:
                try:
                    message, serverAddress = self.clientSocket.recvfrom(2048)
                    segment_recd = header.header(message)
                    if segment_recd.header_components['ACK'].uint:
                        break
                except:
                    if i >= 4:
                        break
                    self.send_fin()
                    i += 1

            for key in self.unAckSegments:
                self.unAckSegments[key][0].cancel()

            self.state = self.states['CLOSED']
            self.clientSocket.close()

        elif self.state == self.states['FIN-WAIT-1']: # we sent fin, so wait for ack
            #print(self.unAckSegments)
            while True:
                try:
                    message, serverAddress = self.clientSocket.recvfrom(2048)
                    segment_recd = header.header(message)
                    if segment_recd.header_components['ACK'].uint and segment_recd.header_components['FIN'].uint:
                        break 
                except:
                    self.send_fin() 

            for key in self.unAckSegments:
                self.unAckSegments[key][0].cancel()

            self.send_ack(segment_recd)

        self.clientSocket.close() 
        return
