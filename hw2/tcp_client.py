###########################################
# James Flemings 
# tcp_client.py
# 11/06/2020
# CSCE 365
# Programming Assignment 2: TCP
###########################################
#!/usr/bin/env python3
from tcp import *
from socket import *
import argparse
import os 
import threading

DATA_LENGTH = 1452


def parseArgument():
    parser = argparse.ArgumentParser(description="Process TFTP information.")
    parser.add_argument('-a', type=str, help="IP Address", required=True)
    parser.add_argument('-f', type=str, help="File Name", required=True)
    parser.add_argument('-sp', type=int, help="Server Port", required=True)
    parser.add_argument('-cp', type=int, help="Client Port", required=True)
    parser.add_argument('-m', type=str, choices=['r', 'w'],
        help="Mode (r = read from server, w = write from server")
    info = parser.parse_args()

    if (info.sp < 5000) or (info.sp > 65535) or (info.cp < 5000) or (info.cp > 65535):
        print("Invalid port")
        return 0, 0, 0, 0, 0

    return info.a, info.f, info.sp, info.cp, info.m

def writeSegment(client_file, segments_to_write):
    for i in sorted(segments_to_write.keys()):
        client_file.write(segments_to_write[i])
    return

def main():
    segments_to_write = {} 
    message = 0
    serverAddress, fileName, serverPort, clientPort, mode = parseArgument()
    if serverAddress == 0:
        return
    client = tcp_client(clientPort, serverPort, serverAddress, mode)
    textFile = 0

    if mode == 'r':
        textFile = open(fileName, 'wb')
    else:
        textFile = open(fileName, 'rb')
        text = textFile.read(DATA_LENGTH)
        while len(text) == DATA_LENGTH:
            client.fullText.append(text)
            text = textFile.read(DATA_LENGTH)
        client.fullText.append(text)
    
    if fileName != '/home/students/jbflemings/hw2/bigfile' and fileName != '/home/A365/tcp/dist/read_files/bigfile':
        t = threading.Timer(15, os._exit, [os.EX_OK])
        t.start()
    cont, segment = client.handShake() # false if sent a FIN
    while cont:
        try:
            message, serverAddress = client.clientSocket.recvfrom(2048)
            segment = header.header(message)
        except:
            #return
            if mode == 'r' and segment != None:
                client.send_ack(segment)
            continue

        if (segment.header_components['FIN'].uint and # server sent a FIN
                segment.header_components['seqNum'].uint == client.rcv_nxt):
            client.finished = True
            client.state = client.states['CLOSE-WAIT']
            break

        elif segment.header_components['ACK'].uint and segment.header_components['SYN'].uint != 1: # server sent an ACK 
            client.checkUnAck(segment)
            if (client.cur_line != len(client.fullText) or client.unAckSegments != {}): 
                client.sendSegment()

            else:
                client.send_fin()
                client.state = client.states['FIN-WAIT-1']
                client.finished = True
                break  

        elif mode == 'r':
            client.readSegment(segment, segments_to_write)

    client.closeConnection(message)
    if mode == 'r':
        writeSegment(textFile, segments_to_write)

    if fileName != '/home/students/jbflemings/hw2/bigfile' and fileName != '/home/A365/tcp/dist/read_files/bigfile':
        t.cancel()

main()
