#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
from RPLCD.i2c import CharLCD

# LCD Setup
lcd = CharLCD(
    i2c_expander='PCF8574',
    address=0x27,
    port=1,
    cols=16, rows=2,
    charmap='A00',
    auto_linebreaks=True
)

def read_with_key(sector, key):
    # Attempt to read block 4 of sector 1, there might be data stored here but it doesnt matter
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
            return None

        return key

    except Exception:
        return None
    
def load_keys(path):
    # Load keys from the txt file
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

    # Keep track of how long it takes to crack Key A
    start_time = time.time()
    for idx, key in enumerate(keys, 1):
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"{idx}/{len(keys)}")
        result = read_with_key(sector=1, key=key)
        if result:
            elapsed = time.time() - start_time
            key_hex = ''.join(f'{b:02X}' for b in result)

            # Display result, wait 2 sec and show timing
            lcd.clear()
            lcd.write_string("Found:")
            lcd.cursor_pos = (1, 0)
            lcd.write_string(key_hex[:12])
            time.sleep(2)

            lcd.clear()
            lcd.write_string(f"T:{elapsed:.2f}s")
            break
    else:
        elapsed = time.time() - start_time
        lcd.clear()
        lcd.write_string("No key found")
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"T:{elapsed:.2f}s")
