#!/usr/bin/env python3
import json
import time
import random
from mfrc522 import MFRC522
from hardware import LCD, RFIDReader
from writer import write_trailer_block
import RPi.GPIO as GPIO

# database imports
import sqlite3

# database setup and alarm system
DB_PATH      = './../database/rfid.db'
ALARM_PIN    = 11      # GPIO pin for buzzer/relay
ALARM_LENGTH = 5       # seconds

# Load configuration and state
config = json.load(open('./../config/keys.json'))
whitelist = json.load(open('./../config/whitelist.json'))

# ─── Database Helpers ──────────────────────────────────────────────────────────
def init_db(conn):
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
      id        INTEGER PRIMARY KEY AUTOINCREMENT,
      uid       TEXT    NOT NULL,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      success   INTEGER NOT NULL
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
      uid       TEXT PRIMARY KEY,
      failures  INTEGER NOT NULL DEFAULT 0,
      flagged   INTEGER NOT NULL DEFAULT 0,
      last_fail DATETIME
    )""")
    conn.commit()

def log_attempt(conn, uid, success):
    """Insert every authentication attempt."""
    conn.execute(
        "INSERT INTO attempts(uid, success) VALUES(?, ?)",
        (uid, int(success))
    )
    conn.commit()

def update_watchlist(conn, uid, success):
    """
    Increment failure counts on bad auth, flag after 3, trigger alarm.
    Reset failures to 0 on a successful auth.
    """
    c = conn.cursor()
    c.execute("SELECT failures, flagged FROM watchlist WHERE uid=?", (uid,))
    row = c.fetchone()

    if not row:
        failures, flagged = 0, 0
        c.execute("INSERT INTO watchlist(uid) VALUES(?)", (uid,))
    else:
        failures, flagged = row

    if success:
        # optionally clear past failures
        failures = 0
        c.execute(
            "UPDATE watchlist SET failures=?, flagged=0 WHERE uid=?",
            (failures, uid)
        )
    else:
        failures += 1
        c.execute(
            "UPDATE watchlist SET failures=?, last_fail=CURRENT_TIMESTAMP WHERE uid=?",
            (failures, uid)
        )
        if failures >= 3 and not flagged:
            # first time hitting 3 failures
            c.execute(
                "UPDATE watchlist SET flagged=1 WHERE uid=?",
                (uid,)
            )
            trigger_alarm()

    conn.commit()
    
def trigger_alarm():
    GPIO.setup(ALARM_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.output(ALARM_PIN, GPIO.HIGH)
    time.sleep(ALARM_LENGTH)
    GPIO.output(ALARM_PIN, GPIO.LOW)


# Initialize hardware
reader = RFIDReader()
display = LCD()          # wraps RPLCD.i2c CharLCD

def get_current_key(uid_str):
    idx = whitelist.get(uid_str, 0)
    hexkey = config[idx]
    return [int(hexkey[i:i+2],16) for i in range(0,12,2)]

# Rotate to a random Key A for the given UID in-place in whitelist.json

def rotate_key_on_card(uid_str):
    #next_idx = random.randrange(len(config))
    if isinstance(uid_str, bytes):
        uid_str = uid_str.hex().upper()  # Convert to hex string, e.g., '23B26C31CC'
    next_idx = 0
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
    # GPIO setup for alarm
    GPIO.setup(ALARM_PIN, GPIO.OUT, initial=GPIO.LOW)

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

        # Log every attempt & update watchlist
        log_attempt(conn, uid_str, auth_ok)
        update_watchlist(conn, uid_str, auth_ok)

        if not auth_ok:
            display.cursor(1, 0)
            display.write("Auth Failed")
        else:
            if uid_str in whitelist:
                display.clear()
                display.write("Unlocked")
                rotate_key_on_card(uid_str)
            else:
                display.clear()
                display.write("Intrusion!")

        time.sleep(2)   # pause so the user can read
        display.clear()
        display.write("Waiting for card")