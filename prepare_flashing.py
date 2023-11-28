import binascii
import sys
from derive import derive_tag_key, derive_undiversified_key
import argparse
from os.path import exists

def derive_key_for_uid(uid, master_key_hex):
    SDM_MASTER_KEY = binascii.unhexlify(master_key_hex)
    TAG_UID = binascii.unhexlify(uid)

    master_key = derive_tag_key(SDM_MASTER_KEY, TAG_UID, 0)
    key_1 = derive_undiversified_key(SDM_MASTER_KEY, 1)
    key_2 = derive_tag_key(SDM_MASTER_KEY, TAG_UID, 2)

    return master_key, key_1, key_2


def prepare_asset_urls(master_key, key_1, key_2):
    url_path_params = "?picc_data=00000000000000000000000000000000&enc=<PRIVAT_KEY>0000000000000000000000000000000000000000000000000000000000000000&cmac=0000000000000000"
    already_done = []

    if exists('done.csv'):
        with open('done.csv') as file:
            already_done = file.readlines()

    with open('todo.csv') as file:
        lines = file.readlines()

    for line in lines:
        if line not in already_done:
            url, private_key = line.split('|')
            url = url.replace('https://', '')
            actual_offset = len('https://' + url + '?picc_data=') - 1
            url = url + url_path_params.replace('<PRIVAT_KEY>', private_key)
            print(url)
            
            PICC_DATA_OFFSET = 54
            SMD_ENCRYPTED_FILE_OFFSET = 91
            SDM_MAC_OFFSET = 225
            SMD_MAC_INPUT_OFFSET = 91
            
            relative_offset = actual_offset - PICC_DATA_OFFSET

            print('SMD_ENCRYPTED_FILE_LENGTH', 128)
            print('SMD_MAC_INPUT_OFFSET', SMD_MAC_INPUT_OFFSET + relative_offset)
            print('SDM_MAC_OFFSET', SDM_MAC_OFFSET + relative_offset)
            print('SMD_ENCRYPTED_FILE_OFFSET', SMD_ENCRYPTED_FILE_OFFSET + relative_offset)
            print('PICC_DATA_OFFSET', PICC_DATA_OFFSET + relative_offset)

            with open('done.csv', 'a') as file:
                file.write('\n' + line)
                file.write(master_key.hex() + '|' + key_1.hex() + '|' + key_2.hex())

            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser("derive_keys.py")
    parser.add_argument("uid", help="The NFC uid. Example: python derive_keys.py 14A119420C1091", type=str)
    
    if not exists('master_key.txt'):
        print('Please create a master_key.txt file with the master key in it.')
        sys.exit(1)

    if not exists('todo.csv'):
        print('Please create an todo.csv file with the asset ids in it.')
        sys.exit(1)

    with open('master_key.txt') as file:
        master_key = file.read().strip()

    args = parser.parse_args()

    master_key, key_1, key_2 = derive_key_for_uid(args.uid, master_key)
    prepare_asset_urls(master_key, key_1, key_2)
    
    print('key 0', master_key.hex())
    print('key 1', key_1.hex())
    print('key 2', key_2.hex())