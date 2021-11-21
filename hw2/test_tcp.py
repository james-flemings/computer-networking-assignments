###############################################
# James Flemings
# test_tcp.py
# 11/06/2020
# CSCE 365
# Programming Assignment 2: TCP Client
###############################################
from bitstring import *
from socket import *
import header
import tcp


def test_header():
    # defining each field in the tcp header
    fields = {'sourcePort': 5001, 'destinationPort': 10000, 'seqNum': 450,
                'ackNum': 1000, 'dataOffset': 5, 'reserved': 0, 'URG': 0,
                'ACK': 1, 'PSH': 0, 'RST': 0, 'SYN': 0, 'FIN': 1, 'window': 5,
                'checkSum': 0, 'urgPoint': 0, 'data': None}

    #correct_segment = BitArray()
    #for value in fields:
    #    correct_segment += BitArray(


    # inserting the fields into the header class to see if it reads it correctly
    segment_1 = header.header(sourcePort=fields['sourcePort'],
            destinationPort=fields['destinationPort'], seqNum=fields['seqNum'],
            ackNum=fields['ackNum'], dataOffset=fields['dataOffset'],
            reserved=fields['reserved'], URG=fields['URG'], ACK=fields['ACK'],
            PSH=fields['PSH'], RST=fields['RST'], SYN=fields['SYN'], FIN=fields['FIN'],
            window=fields['window'], checkSum=fields['checkSum'],
            urgPoint=fields['urgPoint'], data=fields['data'])

    # a couple of tests to ensure that each field is entered correctly
    for key, value in fields.items():
        assert segment_1.header_components[key] == value

    # testing passing segment into constructor works correctly
    segment_1.getSegment()
    segment_2 = header.header(segment=segment_1.getSegment())
    for key, value in fields.items():
        if key == 'data' and fields['SYN'] == 1:
            break
        assert segment_2.header_components[key] == value

test_header()
