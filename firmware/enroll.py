#!/usr/bin/env python3
import json
from hardware import RFIDReader
from writer import write_trailer_block

def enroll_new_card():
    reader = RFIDReader()
    print("Present new card to enroll...")
    uid_bytes = reader.wait_for_tag()
    uid_str = uid_bytes.hex().upper()
    # Append to whitelist
    whitelist = json.load(open('./../config/whitelist.json'))
    if uid_str in whitelist:
        print(f"UID {uid_str} already enrolled.")
        return

    # Provision the card: write the current Key A into the trailer so card uses correct key
    #state = json.load(open('./../config/state.json'))
    
    state = whitelist.get(uid_str, 0)
    
    current_key = bytes.fromhex(json.load(open('./../config/keys.json'))[state])
    
    whitelist[uid_str] = state
    with open('./../config/whitelist.json','w') as f:
        json.dump(whitelist, f, indent=2)
        
    # Write Key A and Key B (same value) to sector 1 trailer
    write_trailer_block(sector=1, keyA=current_key, keyB=current_key, access_bits=None, state=state)
    print(f"Provisioned card with Key A: {current_key.hex().upper()}")
    print(f"Enrolled new UID: {uid_str}")

if __name__ == '__main__':
    enroll_new_card()