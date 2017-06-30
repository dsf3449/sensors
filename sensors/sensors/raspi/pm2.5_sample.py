# -*- coding: utf-8 -*-
'''import serial
import time


def hexShow(argv):
    result = ''
    hLen = len(argv)
    for i in range(hLen):
        hvol = argv[i]
        hhex = '%02x' % hvol
        result += hhex + ' '
    print ('hexShow:', result)


t = serial.Serial('/dev/serial0', 9600)
t.setTimeout(1.5)
while True:
    t.flushInput()
    time.sleep(0.5)
    retstr = t.read(10)
    hexShow(retstr)
    if len(retstr) == 10:
        if (retstr[0] == 0xaa and retstr[1] == 0xc0):
            checksum = 0
            for i in range(6):
                checksum = checksum + int(retstr[2 + i])
            if checksum % 256 == retstr[8]:
                pm25 = int(retstr[2]) + int(retstr[3]) * 256
                # pm10=int(retstr[4])+int(retstr[5])*256
                print ("pm2.5:%.1f μg/m3" % (pm25 / 10.0))'''

import serial
import time


def readlineCR(port):
    rv = ""
    while True:
        ch = port.read()
        rv += ch
        if ch == '\r' or ch == chr(66) or ch == '':
            return rv


port = serial.Serial("/dev/serial0", baudrate = 9600, timeout = 2)

while True:
     rcv = readlineCR(port)
     port.write("I typed: " + repr(rcv))
     print(rcv)





