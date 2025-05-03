#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
    print("Hold an RFID tag near the reader...")
    uid, data = reader.read()
    print(f"→ Tag UID : {uid}")
    print(f"→ Block 0 data (decoded): '{data.strip()}'")
finally:
    GPIO.cleanup()
