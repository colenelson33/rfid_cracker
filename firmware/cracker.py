#!/usr/bin/env python3
import time
import logging
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
from RPLCD.i2c import CharLCD

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('mfrc522').setLevel(logging.CRITICAL)

# === I2C LCD SETUP ===
# Note: change 'PCF8574' & address if your backpack uses a different expander or I2C address.
lcd = CharLCD(
    i2c_expander='PCF8574',
    address=0x27,
    port=1,
    cols=16, rows=2,
    charmap='A00',
    auto_linebreaks=True
)

def read_with_key(sector, key):
    """Try to read block 4*sector with this 6-byte key. Return the string on success, else None."""
    rdr = MFRC522()
    data_blk = sector * 4
    try:
        status, _  = rdr.MFRC522_Request(rdr.PICC_REQIDL)
        if status != rdr.MI_OK:
            return None
        status, uid = rdr.MFRC522_Anticoll()
        if status != rdr.MI_OK:
            return None
        rdr.MFRC522_SelectTag(uid)

        status = rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, data_blk, key, uid)
        if status != rdr.MI_OK:
            logger.info("  key %s failed auth", [hex(b) for b in key])
            return None

        # data = rdr.MFRC522_Read(data_blk)
        # if not data:
        #     return None
        # secret = bytes(data).rstrip(b'\x00').decode('utf-8', errors='ignore')
        # rdr.MFRC522_StopCrypto1()
        # return secret
        return key

    except Exception:
        return None
    # ⚠ We omit GPIO.cleanup() here so we don’t tear down the I²C lines.

def load_keys(path):
    keys = []
    with open(path, 'r') as f:
        for raw in f:
            line = raw.split('#', 1)[0].strip()
            if len(line) != 12:
                continue
            try:
                keys.append([int(line[i:i+2], 16) for i in range(0, 12, 2)])
            except ValueError:
                continue
    return keys

if __name__ == "__main__":
    lcd.clear()
    lcd.write_string("Cracking...")
    keys = load_keys("./../config/keys.txt")

    for idx, key in enumerate(keys, 1):
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"{idx}/{len(keys)}")
        result = read_with_key(sector=1, key=key)
        if result:
            # Convert key to hex string (e.g., "FFFFFFFFFFFF")
            key_hex = ''.join([f'{b:02X}' for b in result])
            lcd.clear()
            lcd.write_string("Found:")
            lcd.cursor_pos = (1, 0)
            # Display first 16 chars of hex key (fits 16-col LCD)
            lcd.write_string(key_hex[:16])
            print("Key:", key_hex)
            break
    else:
        lcd.clear()
        lcd.write_string("No key found")
        print("None of the keys succeeded")
