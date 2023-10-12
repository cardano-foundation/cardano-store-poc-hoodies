import os
from os.path import exists
from dotenv import load_dotenv
import mysql.connector
from pycardano import *
from blockfrost import BlockFrostApi, ApiError, ApiUrls,BlockFrostIPFS
import time
import requests
import magic
import io



load_dotenv()
network = os.getenv('network')
mysql_host = os.getenv('mysql_host')
mysql_user = os.getenv('mysql_user')
mysql_password = os.getenv('mysql_password')
mysql_database = os.getenv('mysql_database')
wallet_mnemonic = os.getenv('wallet_mnemonic')
blockfrost_apikey = os.getenv('blockfrost_apikey')
blockfrost_ipfs = os.getenv('blockfrost_ipfs')
#Policy Closed Change 1
policy_lock_slot = int(os.getenv('policy_lock_slot'))
base_name = "HOODIE"



def split_into_64chars(string):
    if len(string) <= 64:
        return string
    else:
        return [string[i:i+64] for i in range(0, len(string), 64)]

def split_into_array(string):
    return string.split(",")

def connect_to_db():
    global mydb 
    mydb = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database,
        auth_plugin="mysql_native_password"
    )

connect_to_db()
mycursor = mydb.cursor(dictionary=True)
custom_header = {"project_id": blockfrost_ipfs}

if network=="testnet":
    base_url = ApiUrls.preprod.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET

api = BlockFrostApi(project_id=blockfrost_apikey, base_url=base_url)        
cardano = BlockFrostChainContext(project_id=blockfrost_apikey, base_url=base_url)



new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)

payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)

main_address=Address(payment_part=payment_skey.to_verification_key().hash(), staking_part=staking_skey.to_verification_key().hash(),network=cardano_network)

print(f"Main_address: {main_address}")

if not exists(f"keys/policy.skey") and not exists(f"keys/policy.vkey"):
    payment_key_pair = PaymentKeyPair.generate()
    payment_signing_key = payment_key_pair.signing_key
    payment_verification_key = payment_key_pair.verification_key
    payment_signing_key.save(f"keys/policy.skey")
    payment_verification_key.save(f"keys/policy.vkey")

policy_signing_key = PaymentSigningKey.load(f"keys/policy.skey")
policy_verification_key = PaymentVerificationKey.load(f"keys/policy.vkey")
pub_key_policy = ScriptPubkey(policy_verification_key.hash())

#Policy Closed Change 2
must_before_slot = InvalidHereAfter(policy_lock_slot)
policy = ScriptAll([pub_key_policy])

policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()
native_scripts = [policy]

print(f"Policy ID: {policy_id_hex}")

placeholder_paymentkey = '{"type": "PaymentSigningKeyShelley_ed25519", "description": "PaymentSigningKeyShelley_ed25519", "cborHex": "5820PLACEHOLDER"}'

# query = "select * from assets where status = 0 limit 5"
# mycursor.execute(query)
# assets = mycursor.fetchall()

assets = [
    {
        "id":1,
        "key": "BA4941D9E11CA74533922533EC42E82CFC5A8A7C7E272D2BDD516220784B7F24"
    },
    {
        "id":2,
        "key": "1d1935ac7d279d7844a624e800bb4c4afa8c0e01daf389e9a1db5fecced4d765"
    }
]






builder = TransactionBuilder(cardano)
builder.add_input_address(main_address)

#Policy Closed Change 3
builder.ttl = policy_lock_slot

metadata = {
            721: {  
                policy_id_hex: {
                    
                }
            }
        }

my_asset = Asset()
my_nft = MultiAsset()



for asset in assets:
    #adding more NFT's to mint

    new_nft = asset
    asset_id = new_nft["id"]

    asset_name = f"{base_name}{asset_id:04d}"
    asset_name_bytes = asset_name.encode("utf-8")
    asset_image = "assets/image.jpg"
    asset_private_key = new_nft["key"].lower()

    # asset_description = split_into_64chars(new_nft["description"])



    files = {'file': open(asset_image,'rb')}
    # print(f"Uploading {asset_image} to IPFS")
    res = requests.post("https://ipfs.blockfrost.io/api/v0/ipfs/add", headers= custom_header, files=files)
    hashed = res.json()['ipfs_hash']


    metadata[721][policy_id_hex][asset_name] = {
                            "name": asset_name,
                            "image": f"ipfs://{hashed}",
                            "mediaType": "image/jpg",                                
                        }

    payment_signing_key = placeholder_paymentkey.replace('PLACEHOLDER', asset_private_key)
    payment_signing_key = PaymentSigningKey.from_json(payment_signing_key)

    

    result = cip8.sign(message= asset_name, signing_key= payment_signing_key, network=cardano_network, attach_cose_key=True)


    public_key = result['key'][-64:]
    signature = split_into_64chars(result['signature'])

    metadata[721][policy_id_hex][asset_name]['Signature'] = signature


    nft1 = AssetName(asset_name_bytes)
    my_asset[nft1] = 1


my_nft[policy_id] = my_asset


print(metadata)

auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))

builder.native_scripts = native_scripts
builder.auxiliary_data = auxiliary_data
builder.mint = my_nft   

min_val = min_lovelace(
    cardano, output=TransactionOutput(main_address, Value(0, my_nft))
)


builder.add_output(TransactionOutput(main_address, Value(min_val, my_nft)))





signed_tx = builder.build_and_sign([payment_skey, policy_signing_key],change_address=main_address)

# print(signed_tx.transaction_body.inputs)

txid = str(signed_tx.id)

try: 
    cardano.submit_tx(signed_tx.to_cbor())
    print(f"Submitted TX ID: {txid}")

    # for asset in assets:
    #     asset_id = asset["id"]
    #     sql = f"UPDATE assets set status=1 where id = {asset_id}"
    #     mycursor.execute(sql)
    #     mydb.commit()
    #     print(f"updated status for asset {asset_id}")
    
except Exception as e:   
    print("Transaction faild, sleeping 10")
    print(str(e))
    time.sleep(10)  

# query = "select * from assets where status = 0 limit 5"
# mycursor.execute(query)
# assets = mycursor.fetchall()

print(f"Finished minting all NFT's")
