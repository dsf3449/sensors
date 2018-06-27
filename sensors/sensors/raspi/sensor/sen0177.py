import serial

from sensors.domain.sensor import ParticulateMatterSensor
from sensors.common.constants import *


class Sen0177(ParticulateMatterSensor):
    NAME = CFG_SENSOR_TYPE_SEN0177

    class Sen0177Result(object):
        def __init__(self, valid, pm10, pm25, pm100, num3, num5, num10, num25, num50, num100):
            self.valid = valid
            self.pm10 = int(pm10)
            self.pm25 = int(pm25)
            self.pm100 = int(pm100)
            self.num3 = int(num3)
            self.num5 = int(num5)
            self.num10 = int(num10)
            self.num25 = int(num25)
            self.num50 = int(num50)
            self.num100 = int(num100)

    @staticmethod
    def _concat_bytes(upper, lower):
        """
        There has to be a better way ...
        :param upper:
        :return:
        """
        return int(bin(lower)[2:].rjust(8, '0') + bin(upper)[2:].rjust(8, '0'), 2)

    @staticmethod
    def _read_sen0177(port):
        """
        Output values are explained here: https://www.dfrobot.com/wiki/index.php/PM2.5_laser_dust_sensor_SKU:SEN0177#Communication_protocol
        :param port:
        :return:
        """
        data = []
        summation = 0
        data.append(ord(port.read()))
        data.append(ord(port.read()))

        while data[0] != int("42", 16) and data[1] != int("4d", 16):
            # failed - scooting over
            data.pop(0)
            data.append(ord(port.read()))
        summation += data[0] + data[1]
        while len(data) < 17:
            upper = ord(port.read())
            lower = ord(port.read())
            if len(data) < 16:
                summation += upper
                summation += lower
            data.append(Sen0177._concat_bytes(upper, lower))
        if data[16] != summation:
            return Sen0177.Sen0177Result(False, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        return Sen0177.Sen0177Result(True, data[3], data[4], data[5], data[9], data[10], data[11], data[12], data[13], data[14])

    def _particulates(self):
        port = None
        try:
            port = serial.Serial("/dev/serial0", baudrate=9600, timeout=2)
            data = Sen0177._read_sen0177(port)
            if data.valid:
                result = float(data.pm25)
                parameters = {"pm1": str(data.pm10),
                              "pm10": str(data.pm100)}
                return result, parameters
            else:
                return None, None
        finally:
            if port is not None:
                port.close()

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
