#!/usr/bin/env python3
import json
import time
import random
from mfrc522 import MFRC522
from hardware import LCD, RFIDReader
from writer import write_trailer_block

# database imports
import sqlite3

# database setup and alarm system
DB_PATH      = './../database/rfid.db'

# Load configuration and state
config = json.load(open('./../config/keys.json'))
whitelist = json.load(open('./../config/whitelist.json'))

# Database helpers

# this table will log every attempt
def init_db(conn):
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
      id        INTEGER PRIMARY KEY AUTOINCREMENT,
      uid       TEXT    NOT NULL,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      success   INTEGER NOT NULL
    )""")
    conn.commit()

# SQL for logging an attempt
def log_attempt(conn, uid, success):
    """Insert every authentication attempt."""
    conn.execute(
        "INSERT INTO attempts(uid, success) VALUES(?, ?)",
        (uid, int(success))
    )

    conn.commit()
    

# Initialize hardware from helpers
reader = RFIDReader()
display = LCD()

def get_current_key(uid_str):
    idx = whitelist.get(uid_str, 0)
    hexkey = config[idx]
    return [int(hexkey[i:i+2],16) for i in range(0,12,2)]

# Rotate to a random Key A for the given UID in-place in whitelist.json

def rotate_key_on_card(uid_str):
    next_idx = random.randrange(len(config))
    if isinstance(uid_str, bytes):
        uid_str = uid_str.hex().upper()  # Convert to hex string
    new_hex = config[next_idx]
    new_key = bytes.fromhex(new_hex)
    state = whitelist.get(uid_str, 0)
    
    # Write new Key A and Key B into sector 1 trailer
    write_trailer_block(sector=1, keyA=new_key, keyB=new_key, access_bits=None, state=state)
    # Update the mapping and persist
    whitelist[uid_str] = next_idx
    with open('./../config/whitelist.json','w') as f:
        json.dump(whitelist, f, indent=2)

if __name__ == '__main__':
    # DB init
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    init_db(conn)
    
    display.clear()
    display.write("Waiting for card")

    while True:
        uid = reader.wait_for_tag()         # blocking until tag seen
        uid_str = bytes(uid).hex().upper()

        display.clear()
        display.write(f"UID: {uid_str}")

        keyA = get_current_key(uid_str)
        auth_ok = reader.authenticate(sector=1, key=keyA, uid=uid)

        # Log every attempt
        if not auth_ok:
            log_attempt(conn, uid_str, auth_ok)
            display.cursor(1, 0)
            display.write("Auth Failed")
        else:
            if uid_str in whitelist:
                log_attempt(conn, uid_str, auth_ok)
                display.clear()
                display.write("Unlocked")
                rotate_key_on_card(uid_str)
            else:
                log_attempt(conn, uid_str, 0)
                # This will have passed authentification, but not be in our whitelist of uids
                display.clear()
                display.write("Intrusion!")

        # Pause so we can read screen for a bit before going back to scanning
        time.sleep(2)
        display.clear()
        display.write("Waiting for card")