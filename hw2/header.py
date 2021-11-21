#######################################
# James Flemings
# header.py
# 11/06/2020
# CSCE 365
# Programming Assignment 2: TCP Client
#######################################
from bitstring import *
import sys

# this class just allows me to change this functionality:
# header().header_components[key]; either return a string or an int instead
# of a bit array
class MyDict(dict):
    def __getitem__(self, key):
        if key == 'data':
            if super().__getitem__(key) == None: # data field not used
                return None
            else:
                return super().__getitem__(key).bytes.decode() # return a string
        else:
            return super().__getitem__(key).uint # return an unsigned int

# a class to help decipher or create headers of tcp segments
class header():
    # all arguments must be of type string and decimal values
    def __init__(self, segment=0, **kargs):

        # each field and its corresponding value
        self.header_components = {'sourcePort': None, 'destinationPort':None,
                'seqNum': None, 'ackNum': None, 'dataOffset': None,'reserved': None,
                'URG': None, 'ACK': None, 'PSH': None, 'RST': None, 'SYN': None, 
                'FIN': None, 'window': None, 'checkSum': None, 'urgPoint': None,
                'data': None}
        self.header_sizes = {'sourcePort': 16, 'destinationPort': 16,
                'seqNum': 32, 'ackNum': 32, 'dataOffset': 4,'reserved': 6,
                'URG': 1, 'ACK': 1, 'PSH': 1, 'RST': 1, 'SYN': 1, 
                'FIN': 1, 'window': 16, 'checkSum': 16, 'urgPoint': 16,
                'data': 8*1452}
        self.header_fields = ['sourcePort', 'destinationPort', 'seqNum', 'ackNum',
                'dataOffset', 'reserved', 'URG', 'ACK', 'PSH', 'RST', 'SYN', 
                'FIN', 'window', 'checkSum', 'urgPoint', 'data']

        if segment == 0: # passing in info to create header for TCP segment
            # component[0] = 'field'; component[1] = 'value of field'
            for key, value in kargs.items(): 
                if key == 'data':
                    if value != None: 
                        self.header_components[key]=BitArray(value)
                else:
                    newValue = "uint:{}={}".format(self.header_sizes[key], value)
                    self.header_components[key]=BitArray(newValue)

        else: # passing in info from a tcp segment
            accum = 0
            bit_segment = BitArray(segment) # convert bytes into bit array
            for key in self.header_fields:
                length = self.header_sizes[key]
                if key != 'data':
                    self.header_components[key] = bit_segment[accum:accum+length]
                else:
                    self.header_components[key] = bit_segment[accum:]
                accum += length 

        for key, value in self.header_components.items(): 
            # checking if all fields are filled unless data == None, then SYN=1
            if value == None and key != 'data': 
                sys.exit("Missing {} in constructor".format(key))

    def getSegment(self):
        segment = BitArray()
        for key in self.header_fields:
            segment += self.header_components[key]
        return segment.tobytes()
