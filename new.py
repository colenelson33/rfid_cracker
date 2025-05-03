#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_with_new_key(sector=2, secret=b"Encrypted123456"):
    """
    Overwrites sector trailer with:
      Key A = new_key
      Access bits = default (0xFF,0x07,0x80,0x69)
      Key B = default_key (0xFF…FF)
    Then writes `secret` (max 16 bytes) into the first block of that sector.
    """
    rdr = MFRC522()
    default_key = [0xFF] * 6
    new_key     = [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]
    access_bits = [0xFF, 0x07, 0x80, 0x69]

    trailer_blk = sector * 4 + 3
    data_blk    = sector * 4

    # Prepare payload (pad or truncate to 16 bytes)
    if len(secret) > 16:
        logger.warning("Secret exceeds 16 bytes; truncating")
        secret = secret[:16]
    payload = list(secret.ljust(16, b"\x00"))

    # Sector sanity check
    if not (1 <= sector <= 15):
        logger.error("Invalid sector %d for MIFARE Classic 1K", sector)
        return

    try:
        input("Place tag on reader and press Enter…")

        # 1) Select tag
        (status, _) = rdr.MFRC522_Request(rdr.PICC_REQIDL)
        if status != rdr.MI_OK:
            logger.error("No tag detected")
            return
        (status, uid) = rdr.MFRC522_Anticoll()
        if status != rdr.MI_OK:
            logger.error("Anticollision failed")
            return
        rdr.MFRC522_SelectTag(uid)
        logger.info("✔ UID: %s", uid)

        # 2) Authenticate trailer block with the DEFAULT key
        status = rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, trailer_blk, default_key, uid)
        if status != rdr.MI_OK:
            logger.error("Default-key auth to trailer failed")
            return
        logger.info("✔ Authenticated to trailer with default key")

        # 3) Rewrite the trailer block
        trailer_data = new_key + access_bits + default_key
        rdr.MFRC522_Write(trailer_blk, trailer_data)
        logger.info("🔑 Trailer block re-keyed (Key A=new_key, Key B=default_key)")

        # Stop crypto to let the tag reset
        rdr.MFRC522_StopCrypto1()
        time.sleep(0.5)

        # 4) Re-detect & re-select the tag
        for attempt in range(3):
            (status, _) = rdr.MFRC522_Request(rdr.PICC_REQIDL)
            if status == rdr.MI_OK:
                break
            time.sleep(0.2)
        else:
            logger.error("Tag lost after trailer rewrite")
            return

        (status, uid) = rdr.MFRC522_Anticoll()
        if status != rdr.MI_OK:
            logger.error("Anticollision failed on re-detect")
            return
        rdr.MFRC522_SelectTag(uid)
        logger.info("✔ Re-selected UID: %s", uid)

        # 5) Authenticate data block with the NEW key (Key A)
        status = rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, data_blk, new_key, uid)
        if status != rdr.MI_OK:
            logger.error("Auth to data block with new key failed")
            return
        logger.info("🔐 Authenticated to data block with new key")

        # 6) Write your secret payload
        rdr.MFRC522_Write(data_blk, payload)
        logger.info("✅ Secret written to block %d", data_blk)

        # 7) Verify data write
        status = rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, data_blk, new_key, uid)
        read_back = rdr.MFRC522_Read(data_blk)
        if read_back == payload:
            logger.info("✅ Data write verified")
        else:
            logger.error("❌ Data mismatch on verify read")

        # 8) (Optional) Verify trailer write by re-reading it
        status = rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, trailer_blk, new_key, uid)
        raw_trailer = rdr.MFRC522_Read(trailer_blk)
        logger.info("🔄 Trailer raw bytes: %s", raw_trailer)

    except Exception as e:
        logger.error("Error: %s", e)

    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    write_with_new_key(sector=2, secret=b"Encrypted123456")
