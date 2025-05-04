#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import time

# your “new” 6-byte key that you used before
NEW_KEY     = [0x00]*6
# factory default key
DEFAULT_KEY = [0xFF]*6
ACCESS_BITS = [0xFF, 0x07, 0x80, 0x69]  # standard access bits

def restore_factory(sectors=16):
    rdr = MFRC522()
    try:
        for sector in range(sectors):
            trailer_blk = sector*4 + 3

            input(f"\nPlace card for sector {sector} and press Enter…")
            rdr.MFRC522_Request(rdr.PICC_REQIDL)
            _, uid = rdr.MFRC522_Anticoll()
            rdr.MFRC522_SelectTag(uid)

            # 1) auth with *your* new key
            if rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, trailer_blk, NEW_KEY, uid) != rdr.MI_OK:
                print(f" ✖ Auth with NEW_KEY failed on sector {sector}")
                continue

            # 2) write default trailer: [KeyA][AccessBits][KeyB]
            trailer = DEFAULT_KEY + ACCESS_BITS + DEFAULT_KEY
            print(f" → Restoring sector {sector} trailer to default key…")
            rdr.MFRC522_Write(trailer_blk, trailer)
            rdr.MFRC522_StopCrypto1()
            time.sleep(0.1)

            print(f" ✔ Sector {sector} restored to factory key\n")

    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    restore_factory()
