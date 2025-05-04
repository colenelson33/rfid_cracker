#!/usr/bin/env python3
import RPi.GPIO as GPIO
import spidev
import time
from mfrc522 import MFRC522
from RPLCD.i2c import CharLCD

# Setup GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Create RFIDReader object
class RFIDReader:
    def __init__(self, bus=0, device=0):
        # init spi
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.reader = MFRC522()

    def wait_for_tag(self):
        # waits for a tag to be detected
        while True:
            status, _ = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)
            if status == self.reader.MI_OK:
                status, uid = self.reader.MFRC522_Anticoll()
                if status == self.reader.MI_OK:
                    return bytes(uid)
            time.sleep(0.1)

    def authenticate(self, sector, key, uid):
        # Once tag is selected, auth against sector 1 trailer with key A
        block = sector * 4 + 3
        uid_list = list(uid) if not isinstance(uid, list) else uid
        # Select the tag so the auth goes to the right UID
        self.reader.MFRC522_SelectTag(uid_list)
        # Perform authentication
        status = self.reader.MFRC522_Auth(
            self.reader.PICC_AUTHENT1A,
            block,
            list(key),
            uid_list
        )
        self.reader.MFRC522_StopCrypto1()
        return status == self.reader.MI_OK


class LCD:
    def __init__(self, address=0x27, port=1):
        # Init the I2C 16x2 LCD
        self.lcd = CharLCD(
            i2c_expander='PCF8574',
            address=0x27,
            port=1,
            cols=16, rows=2,
            charmap='A00',
            auto_linebreaks=True
        )

    def clear(self):
        self.lcd.clear()

    def write(self, text, line=0, pos=0):
        self.lcd.cursor_pos = (line, pos)
        self.lcd.write_string(text)

    def cursor(self, line, pos):
        self.lcd.cursor_pos = (line, pos)

# Clean up all pins on program exit
import atexit
atexit.register(GPIO.cleanup)