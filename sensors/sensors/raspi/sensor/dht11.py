import time

import RPi.GPIO as GPIO

from sensors.domain.sensor import AirTempRHSensor
from sensors.config.constants import *


class Dht11(AirTempRHSensor):
    NAME = CFG_SENSOR_TYPE_DHT11
    GPIO_PIN = 17
    STATE_INIT_PULL_DOWN = 1
    STATE_INIT_PULL_UP = 2
    STATE_DATA_FIRST_PULL_DOWN = 3
    STATE_DATA_PULL_UP = 4
    STATE_DATA_PULL_DOWN = 5

    def _read(self):
        GPIO.setup(self.GPIO_PIN, GPIO.OUT)

        # send initial high
        self._send_and_sleep(self.GPIO_PIN, GPIO.HIGH, 0.05)

        # pull down to low
        self._send_and_sleep(self.GPIO_PIN, GPIO.LOW, 0.02)

        # change to input using pull up
        GPIO.setup(self.GPIO_PIN, GPIO.IN, GPIO.PUD_UP)

        # collect data into an array
        data = self._collect_input()

        # parse lengths of all data pull up periods
        pull_up_lengths = self._parse_data_pull_up_lengths(data)

        # if bit count mismatch, return error (4 byte data + 1 byte checksum)
        if len(pull_up_lengths) != 40:
            return Dht11.DHT11Result(Dht11.DHT11Result.ERR_MISSING_DATA, 0, 0)

        # calculate bits from lengths of the pull up periods
        bits = self._calculate_bits(pull_up_lengths)

        # we have the bits, calculate bytes
        the_bytes = self._bits_to_bytes(bits)

        # calculate checksum and check
        checksum = self._calculate_checksum(the_bytes)
        if the_bytes[4] != checksum:
            return Dht11.DHT11Result(Dht11.DHT11Result.ERR_CRC, 0, 0)

        # ok, we have valid data, return it
        return Dht11.DHT11Result(Dht11.DHT11Result.ERR_NO_ERROR, the_bytes[2], the_bytes[0])

    @staticmethod
    def _send_and_sleep(pin, output, sleep):
        GPIO.output(pin, output)
        time.sleep(sleep)

    @staticmethod
    def _collect_input(pin):
        # collect the data while unchanged found
        unchanged_count = 0

        # this is used to determine where is the end of the data
        max_unchanged_count = 100

        last = -1
        data = []
        while True:
            current = GPIO.input(pin)
            data.append(current)
            if last != current:
                unchanged_count = 0
                last = current
            else:
                unchanged_count += 1
                if unchanged_count > max_unchanged_count:
                    break

        return data

    @staticmethod
    def _parse_data_pull_up_lengths(data):
        state = Dht11.STATE_INIT_PULL_DOWN

        # will contain the lengths of data pull up periods
        lengths = []
        # will contain the length of the previous period
        current_length = 0

        for i in range(len(data)):

            current = data[i]
            current_length += 1

            if state == Dht11.STATE_INIT_PULL_DOWN:
                if current == GPIO.LOW:
                    # ok, we got the initial pull down
                    state = Dht11.STATE_INIT_PULL_UP
                    continue
                else:
                    continue
            if state == Dht11.STATE_INIT_PULL_UP:
                if current == GPIO.HIGH:
                    # ok, we got the initial pull up
                    state = Dht11.STATE_DATA_FIRST_PULL_DOWN
                    continue
                else:
                    continue
            if state == Dht11.STATE_DATA_FIRST_PULL_DOWN:
                if current == GPIO.LOW:
                    # we have the initial pull down, the next will be the data pull up
                    state = Dht11.STATE_DATA_PULL_UP
                    continue
                else:
                    continue
            if state == Dht11.STATE_DATA_PULL_UP:
                if current == GPIO.HIGH:
                    # data pulled up, the length of this pull up will determine whether it is 0 or 1
                    current_length = 0
                    state = Dht11.STATE_DATA_PULL_DOWN
                    continue
                else:
                    continue
            if state == Dht11.STATE_DATA_PULL_DOWN:
                if current == GPIO.LOW:
                    # pulled down, we store the length of the previous pull up period
                    lengths.append(current_length)
                    state = Dht11.STATE_DATA_PULL_UP
                    continue
                else:
                    continue

        return lengths

    @staticmethod
    def _calculate_bits(pull_up_lengths):
        # find shortest and longest period
        shortest_pull_up = 1000
        longest_pull_up = 0

        for i in range(0, len(pull_up_lengths)):
            length = pull_up_lengths[i]
            if length < shortest_pull_up:
                shortest_pull_up = length
            if length > longest_pull_up:
                longest_pull_up = length

        # use the halfway to determine whether the period it is long or short
        halfway = shortest_pull_up + (longest_pull_up - shortest_pull_up) / 2
        bits = []

        for i in range(0, len(pull_up_lengths)):
            bit = False
            if pull_up_lengths[i] > halfway:
                bit = True
            bits.append(bit)

        return bits

    @staticmethod
    def _bits_to_bytes(bits):
        the_bytes = []
        byte = 0

        for i in range(0, len(bits)):
            byte = byte << 1
            if bits[i]:
                byte = byte | 1
            else:
                byte = byte | 0
            if (i + 1) % 8 == 0:
                the_bytes.append(byte)
                byte = 0

        return the_bytes

    @staticmethod
    def __calculate_checksum(the_bytes):
        return the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3] & 255

    def __init__(self, typ, *args):
        super().__init__(typ, *args)

    class DHT11Result(AirTempRHSensor.AirTempRHResult):
        ERR_NO_ERROR = 0
        ERR_MISSING_DATA = 1
        ERR_CRC = 2

        def __init__(self, error_code, temperature, humidity):
            super().__init__(temperature, humidity)
            self.error_code = error_code

        def is_valid(self):
            return self.error_code == self.ERR_NO_ERROR
