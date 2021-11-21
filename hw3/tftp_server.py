from socket import *
import argparse, threading, queue, os
import headers

queue_list = dict() # indexed by client address
thread_list = dict() # indexed by client address
lock = threading.Lock()
serverSocket = socket(AF_INET, SOCK_DGRAM)

# constants 
DATA_LENGTH = 512
TIMEOUT = 2 
RESEND = 50

def read_write(message, clientAddress):
    block_num = 0
    fullText = list()
    textFile = 0
    read_opcode = b'\x00\x01'

    fileName = message[2:].split(b'\x00')[0].decode()    
    mode = message[0:2]  # read or write

    # client trying to read a nonexistent file
    if (not os.path.isfile(fileName)) and mode == read_opcode: 
        serverSocket.sendto(headers.error(1), clientAddress) # file not found
        return

    if mode == read_opcode: # read mode
        textFile = open(fileName, 'rb') # writing to client 
        text = textFile.read(DATA_LENGTH)

        while len(text) == DATA_LENGTH: # store content of text file into a list
            fullText.append(text)
            text = textFile.read(DATA_LENGTH)
        fullText.append(text)
        serverSocket.sendto(headers.data(block_num+1, fullText[block_num]), clientAddress)

    else: # write mode
        if fileName != "shutdown.txt":
            fileName = fileName.split('/')[6]
        textFile = open(fileName, 'wb') # reading from client
        serverSocket.sendto(headers.ack((block_num).to_bytes(2, byteorder='big')), 
        clientAddress)
        
    block_num = 1
    finished = False
    while not finished:
        try:
            message = queue_list[clientAddress].get(block=True, timeout=TIMEOUT)
            if message[:2] == b'\x00\x05': # error packet
                print("ERROR: ", message[4:].decode())
                finished = True
            elif mode == read_opcode:
                finished = read_client(message, clientAddress, block_num, fullText)
            else:
                finished = write_client(message, clientAddress, block_num, textFile)

            block_num += 1

        except queue.Empty: # server timeout
            print("Timeout")
            if mode == read_opcode:
                serverSocket.sendto(headers.data(block_num+1, fullText[block_num]),
                 clientAddress)
            else:
                serverSocket.sendto(headers.ack((block_num).to_bytes(2, byteorder='big')), 
                clientAddress)
     
    lock.acquire()
    thread_list.pop(clientAddress) # remove current thread from thread list
    lock.release()
    textFile.close()
    return

def read_client(message, clientAddress, block_num, fullText):
    if (block_num) >= len(fullText):
        return True

    serverSocket.sendto(headers.data(block_num+1, fullText[block_num]),
     clientAddress)

    return False

def write_client(message, clientAddress, block_num, textFile):
    if message[2:4] == (block_num).to_bytes(2, byteorder='big'):
        textFile.write(message[4:])
        serverSocket.sendto(headers.ack(message[2:4]), clientAddress)
    
    if len(message[4:]) < DATA_LENGTH:
        return True
     
    return False


def port_value(source_port):
    port = int(source_port)
    if (port < 5000) or (port > 65535): # port number must be in valid range
        raise argparse.ArgumentTypeError("Invalid port")
    return port

def parse(): # parse source port argument
    parser = argparse.ArgumentParser(description="TFTP information.")
    parser.add_argument('-sp', type=port_value, help="Server Port.", required=True)
    return parser.parse_args().sp

def main():
    finished = False
    sourcePort = parse()
    serverSocket.bind(('', sourcePort))

    while (not finished) or thread_list:
        message, clientAddress = serverSocket.recvfrom(2048)
        opcode = message[:2]
        fileName = message[2:].split(b'\x00')[0].decode()  
        if fileName == "shutdown.txt":
            finished = True 
            if opcode == b'\x00\x02': # received shutdown.txt in write mode
                lock.acquire()
                queue_list[clientAddress] = queue.Queue()
                thread_list[clientAddress] = threading.Thread(target=read_write,
                args=(message, clientAddress), daemon=True).start()
                lock.release()

        elif (opcode != b'\x00\x01') and (opcode != b'\x00\x02'): # packet not a RRQ/WRQ
            if clientAddress in queue_list:
                queue_list[clientAddress].put(message)
            #else: # valid packet but TID doesn't exist 
            #    serverSocket.sendto(headers.error(5), clientAddress)

        else: # packet is a RRQ/WRQ
            lock.acquire()
            queue_list[clientAddress] = queue.Queue()
            thread_list[clientAddress] = threading.Thread(target=read_write,
            args=(message, clientAddress), daemon=True).start()
            lock.release()

    serverSocket.close()
    return            

if __name__== '__main__':
    main()