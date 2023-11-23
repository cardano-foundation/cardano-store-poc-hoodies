import binascii
import sys
from derive import derive_tag_key, derive_undiversified_key
import argparse

def derive_key_for_uid(uid):
    SDM_MASTER_KEY = binascii.unhexlify("7481B1102F7C8D3D80291512F2F067AB")
    TAG_UID = binascii.unhexlify(uid)

    master_key = derive_tag_key(SDM_MASTER_KEY, TAG_UID, 0)
    key_1 = derive_undiversified_key(SDM_MASTER_KEY, 1)
    key_2 = derive_tag_key(SDM_MASTER_KEY, TAG_UID, 2)
    key_3 = derive_tag_key(SDM_MASTER_KEY, TAG_UID, 3)
    key_4 = derive_tag_key(SDM_MASTER_KEY, TAG_UID, 4)

    print('key 0', master_key.hex())
    print('key 1', key_1.hex())
    print('key 2', key_2.hex())
    print('key 3', key_3.hex())
    print('key 4', key_4.hex())

if __name__ == '__main__':
    parser = argparse.ArgumentParser("derive_keys.py")
    parser.add_argument("uid", help="The NFC uid. Example: python derive_keys.py 14A119420C1091", type=str)
    args = parser.parse_args()
    derive_key_for_uid(args.uid)