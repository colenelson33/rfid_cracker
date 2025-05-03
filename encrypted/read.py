#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def read_with_key(sector, key):
    """Try to read block 4*sector with this 6-byte key. Return the string on success, else None."""
    rdr = MFRC522()
    data_blk = sector * 4

    try:

        # detect & anticollide
        status, _ = rdr.MFRC522_Request(rdr.PICC_REQIDL)
        if status != rdr.MI_OK:
            return None
        status, uid = rdr.MFRC522_Anticoll()
        if status != rdr.MI_OK:
            return None
        rdr.MFRC522_SelectTag(uid)
        logger.info("✔ UID: %s", uid)

        # auth with this key
        status = rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, data_blk, key, uid)
        if status != rdr.MI_OK:
            #logger.info("  key %s failed auth", [hex(b) for b in key])
            return None

        # read & decode
        data = rdr.MFRC522_Read(data_blk)
        if not data:
            #logger.error("Read failed")
            return None
        secret = bytes(data).rstrip(b'\x00').decode('utf-8', errors='ignore')
        rdr.MFRC522_StopCrypto1()
        logger.info
        return secret

    except Exception as e:
        #logger.error("Error: %s", e)
        return None
    finally:
        GPIO.cleanup()
        
def load_keys(path):
    """
    Read a file where each non-comment line is exactly 12 hex chars (e.g. FFFFFFFFFFFF),
    ignore lines starting with # or blank lines, and return a list of 6-byte key lists.
    """
    keys = []
    with open(path, 'r') as f:
        for raw in f:
            # strip whitespace, drop anything after a '#' (inline or full-line comment)
            line = raw.split('#', 1)[0].strip()
            if not line:
                continue  # skip blank/comment lines
            if len(line) != 12:
                logger.warning("Skipping invalid key line: %r", raw.rstrip())
                continue
            # parse each pair of hex chars into an int
            try:
                key = [int(line[i : i+2], 16) for i in range(0, 12, 2)]
                keys.append(key)
            except ValueError:
                logger.warning("Non-hex characters in line: %r", raw.rstrip())
    return keys


if __name__ == "__main__":
    
    keys = load_keys("./../keys.txt")
    for key in keys:
        result = read_with_key(sector=2, key=key)
        if result != -1:
            print(result)