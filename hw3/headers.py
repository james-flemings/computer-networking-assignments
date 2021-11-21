'''
Encodes file name, mode (read or write), address of server, 
and port number into a header of a packet that will be sent
to the address of the server. Read/Write header format:
    2 bytes string 1 byte  string  1 byte
    -------------------------------------
RRQ/|01/02|Filename|  0  |  Mode  |  0  |
WRQ -------------------------------------
'''
def read_write_request(fileName, mode):
    header = bytearray([0])
    # determine if read or write request
    if mode =='r':
        header.append(1)
    else:
        header.append(2)
    # encode file name and append to header 
    header += bytearray(fileName.encode())
    header.append(0)
    header += bytearray('netascii'.encode())
    header.append(0)
    return header

# block_num is already in bytes
def ack(block_num):
    return (bytearray([0, 4]) + block_num)

# data already in bytes
def data(block_num, data):
    return (bytearray([0, 3]) + (block_num).to_bytes(2, byteorder='big') + data)

def error(code):
    errorCodes = {
        # Value Meaning
            0:  "Not defined, see error message (if any).",
            1:  "File not found.",
            2:  "Access violation.",
            3:  "Disk full or allocation exceeded.",
            4:  "Illegal TFTP operation.",
            5:  "Unknown transfer ID.",
            6:  "File already exists.",
            7:  "No such user."
            };

    message = bytearray([0, 5])
    message += (code).to_bytes(2, byteorder='big')
    message += errorCodes[code].encode()
    message.append(0)
    return message 
