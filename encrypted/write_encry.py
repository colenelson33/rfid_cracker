#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_with_new_key(sector=2, secret=b"Encrypted123456"):
    rdr = MFRC522()
    default_key = [0xFF] * 6
    new_key = [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]
    key_b = [0x00] * 6  # Unused key B
    # Access bits: FF078069 allows read/write with key A
    access_bits = [0xFF, 0x07, 0x80, 0x69]

    trailer_blk = sector * 4 + 3
    data_blk = sector * 4

    if sector < 1 or sector > 15:
        logger.error("Invalid sector for MIFARE Classic 1K")
        return

    if len(secret) > 16:
        logger.warning("Secret exceeds 16 bytes; truncating")
        secret = secret[:16]
    payload = list(secret.ljust(16, b'\x00'))

    try:
        input("Place tag on reader and press Enter…")

        # Detect and select tag
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

        # Authenticate with default key for trailer
        status = rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, trailer_blk, default_key, uid)
        if status == rdr.MI_OK:
            logger.info("✔ Default key OK — re-keying sector trailer")
            trailer_data = new_key + access_bits + key_b
            rdr.MFRC522_Write(trailer_blk, trailer_data)
            rdr.MFRC522_StopCrypto1()  # Stop Crypto1
            time.sleep(0.5)  # Increased delay for tag stability

            # Retry tag detection
            for attempt in range(3):
                (status, _) = rdr.MFRC522_Request(rdr.PICC_REQIDL)
                if status == rdr.MI_OK:
                    break
                logger.warning("Tag detection failed (attempt %d)", attempt + 1)
                time.sleep(0.2)
            else:
                logger.error("❌ Tag lost after re-keying")
                return

            (status, uid) = rdr.MFRC522_Anticoll()
            if status != rdr.MI_OK:
                logger.error("❌ Anticollision failed after re-keying")
                return
            rdr.MFRC522_SelectTag(uid)
            logger.info("✔ Re-detected UID: %s", uid)
        else:
            logger.warning("Default key failed; assuming trailer uses new key")

        # Authenticate with new key for data block
        status = rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, data_blk, new_key, uid)
        if status != rdr.MI_OK:
            logger.error("Auth to data block with new key failed")
            return

        # Write secret payload
        rdr.MFRC522_Write(data_blk, payload)
        logger.info("✅ Secret written")

        # Verify write
        rdr.MFRC522_Auth(rdr.PICC_AUTHENT1A, data_blk, new_key, uid)
        read_data = rdr.MFRC522_Read(data_blk)
        if read_data == payload:
            logger.info("✅ Write verified")
        else:
            logger.error("❌ Write verification failed")

    except Exception as e:
        logger.error("Error: %s", e)
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    write_with_new_key(sector=2, secret=b"Encrypted123456")