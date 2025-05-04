#!/usr/bin/env python3
import json
import time
from hardware import RFIDReader, LCD
from writer import write_trailer_block

# Code to add a fresh card to whitelist
def enroll_new_card():
    reader = RFIDReader()
    lcd = LCD()
    lcd.clear()
    lcd.write("Enroll fresh tag")
    uid_bytes = reader.wait_for_tag()
    uid_str = uid_bytes.hex().upper()
    # Append to whitelist
    whitelist = json.load(open('./../config/whitelist.json'))
    if uid_str in whitelist:
        lcd.clear()
        lcd.write("Already enrolled")
        time.sleep(2)
        lcd.clear()
        return
    
    state = whitelist.get(uid_str, 0)
    
    current_key = bytes.fromhex(json.load(open('./../config/keys.json'))[state])
    
    whitelist[uid_str] = state
    with open('./../config/whitelist.json','w') as f:
        json.dump(whitelist, f, indent=2)
        
    # Write Key A and Key B (same value) to sector 1 trailer
    write_trailer_block(sector=1, keyA=current_key, keyB=current_key, access_bits=None, state=state)
    lcd.clear()
    lcd.write("Enrolled new tag")
    print(f"Provisioned card with Key A: {current_key.hex().upper()}")
    print(f"Enrolled new UID: {uid_str}")

if __name__ == '__main__':
    enroll_new_card()