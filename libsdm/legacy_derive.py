import hashlib


# old derivation algorithm compatible with NFC Developer App

# derive a key which is UID-diversified
def derive_tag_key(master_key: bytes, uid: bytes, key_no: int) -> bytes:

    # print("master_key")
    # print(master_key)

    # print("uid")
    # print(uid)

    return master_key

    if master_key == (b"\x00" * 16):
        return b"\x00" * 16

    return hashlib.pbkdf2_hmac('sha512', master_key, b"key" + uid + bytes([key_no]), 5000, 16)


# derive a key which is not UID-diversified
def derive_undiversified_key(master_key: bytes, key_no: int) -> bytes:

    return master_key

    if master_key == (b"\x00" * 16):
        return master_key
        # return b"\x00" * 16

    return hashlib.pbkdf2_hmac('sha512', master_key, b"key_no_uid" + bytes([key_no]), 5000, 16)
