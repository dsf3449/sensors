import serial
import time


# pass in upper and lower 8 bit values
# returns the 16 bit value as an int
# def PrintContcatBytes(valueOne, valueTwo):
#	print bin(valueOne)[2:].rjust(8,'0')

class ReturnValue(object):
    def __init__(self, valid, pm10, pm25, pm100, num3, num5, num10, num25, num50, num100):
        self.valid = valid
        self.pm10 = pm10
        self.pm25 = pm25
        self.pm100 = pm100
        self.num3 = num3
        self.num5 = num5
        self.num10 = num10
        self.num25 = num25
        self.num50 = num50
        self.num100 = num100


def ConcatBytes(valueOne, valueTwo):
    return int(bin(valueOne)[2:].rjust(8, '0') + bin(valueTwo)[2:].rjust(8, '0'), 2)


def readlineCRtest(port):
    for i in range(256):
        for j in range(256):
            if i * 256 + j != ConcatBytes(i, j):
                print (i, j, i * 256 + j, ConcatBytes(i, j))
        print (i)


def readlineCR(port):
    """
    Output values are explained here: https://www.dfrobot.com/wiki/index.php/PM2.5_laser_dust_sensor_SKU:SEN0177#Communication_protocol
    :param port:
    :return:
    """
    data = []
    summation = 0
    data.append(ord(port.read()))
    data.append(ord(port.read()))
    #	data.append(22) data.append(17) print (int("42", 16), int("4d", 16)) print int(bin(32)[2:].rjust(8, '0'),2) print (data[0], data[1])
    while (data[0] != int("42", 16) and data[1] != int("4d", 16)):
        print("failed - scooting over")
        data.pop(0)
        data.append(ord(port.read()))
    summation += data[0] + data[1]
    while len(data) < 17:
        upperVal = ord(port.read())
        lowerVal = ord(port.read())
        if len(data) < 16:
            summation += upperVal
            summation += lowerVal
        data.append(ConcatBytes(upperVal, lowerVal))
    #	for message in data:
    #		print message print "Last num should be: ", summation
    if data[16] != summation:
        return ReturnValue("False", 0, 0, 0, 0, 0, 0, 0, 0, 0)
    #		print (int(message[0], 16)) print (len(message), message) if (int(message[0], 16) != int("42", 16) or len(message) > 1 and int(message[1], 16) != int("4d", 16)):
    #			print("character deleted to scoot over") message = message[1:]
    return ReturnValue("True", data[3], data[4], data[5], data[9], data[10], data[11], data[12], data[13], data[14])


# if ch == '\r' or ch == chr(66) or ch == '':
#  return rv

port = serial.Serial("/dev/serial0", baudrate=9600, timeout=2)

while True:
    boxOfStuff = readlineCR(port)

    port.write(b"I typed stuff")
    if boxOfStuff.valid:
        print(boxOfStuff.pm10, boxOfStuff.pm25, boxOfStuff.pm100, boxOfStuff.num3, boxOfStuff.num5, boxOfStuff.num10,
              boxOfStuff.num25, boxOfStuff.num50, boxOfStuff.num100)
    else:
        print("message failed")
