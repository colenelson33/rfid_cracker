#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

def write_tag():
    reader = SimpleMFRC522()

    try:
        text = input("Enter the text you want to write to the tag: ")
        print("Now place your RFID tag on the reader and press Enter...")
        input()
        reader.write(text)
        print("✅ Data written to tag!")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    write_tag()
