#!/usr/bin/env python3
import json
from mfrc522 import MFRC522

# Default access bits for Key A write
DEFAULT_ACCESS = [0xFF, 0x07, 0x80, 0x69]

def write_trailer_block(sector, keyA=None, keyB=None, access_bits=None, state=0):
    # Load current key for authentication
    current_key = bytes.fromhex(json.load(open('./../config/keys.json'))[state])

    rdr = MFRC522()
    # Select tag and authenticate
    rdr.MFRC522_Request(rdr.PICC_REQIDL)
    _, uid = rdr.MFRC522_Anticoll()
    rdr.MFRC522_SelectTag(uid)
    trailer = sector * 4 + 3
    curr_key_bytes = list(current_key)
    rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, trailer, curr_key_bytes, uid)
    # Prepare block data, this is the format: KeyA | access_bits | KeyB
    block_data = []
    if keyA:
        block_data += list(keyA)
    if access_bits is None:
        block_data += DEFAULT_ACCESS
    else:
        block_data += access_bits
    if keyB:
        block_data += list(keyB)
    # Write 16-byte trailer
    rdr.MFRC522_Write(trailer, block_data)
    rdr.MFRC522_StopCrypto1()