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

if not exists(f"keys/policy.skey") and not exists(f"keys/policy.vkey"):
    payment_key_pair = PaymentKeyPair.generate()
    payment_signing_key = payment_key_pair.signing_key
    payment_verification_key = payment_key_pair.verification_key
    payment_signing_key.save(f"keys/policy.skey")
    payment_verification_key.save(f"keys/policy.vkey")

if not exists(f"keys/merchadise.skey") and not exists(f"keys/merchadise.vkey"):
    payment_key_pair = PaymentKeyPair.generate()
    payment_signing_key = payment_key_pair.signing_key
    payment_verification_key = payment_key_pair.verification_key
    payment_signing_key.save(f"keys/merchadise.skey")
    payment_verification_key.save(f"keys/merchadise.vkey")



merchadise_signing_key = PaymentSigningKey.load(f"keys/merchadise.skey")
merchadise_verification_key = PaymentVerificationKey.load(f"keys/merchadise.vkey")

policy_signing_key = PaymentSigningKey.load(f"keys/policy.skey")
policy_verification_key = PaymentVerificationKey.load(f"keys/policy.vkey")
pub_key_policy = ScriptPubkey(policy_verification_key.hash())

#Policy Closed Change 2
must_before_slot = InvalidHereAfter(policy_lock_slot)
policy = ScriptAll([pub_key_policy, must_before_slot])

policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()
native_scripts = [policy]

print(main_address)





query = "select * from shirts where status = 0 and id > 50 and id < 100 limit 5"
mycursor.execute(query)
shirts = mycursor.fetchall()


while len(shirts) > 0:
    print("still nft's to mint: {}".format(len(shirts)))

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

    

    for shirt in shirts:
        #adding more NFT's to mint

        new_nft = shirt

        asset_name = new_nft["name"]
        asset_name_bytes = asset_name.encode("utf-8")
        asset_image = new_nft["image"]
        asset_product = split_into_64chars(new_nft["product"])
        asset_product_type = split_into_64chars(new_nft["product_type"])
        asset_description = split_into_64chars(new_nft["description"])
        asset_limited_quantity = split_into_64chars(new_nft["limited_quantity"])
        asset_date = split_into_64chars(new_nft["date"])
        asset_official_event_website = split_into_64chars(new_nft["official_event_website"])
        asset_location = split_into_64chars(new_nft["location"])
        asset_apparel_company = split_into_64chars(new_nft["apparel_company"])
        asset_championship_venue = split_into_64chars(new_nft["championship_venue"])
        asset_venue_location = split_into_64chars(new_nft["venue_location"])
        asset_secondary_venue = split_into_64chars(new_nft["secondary_venue"])
        asset_tertiary_venue = split_into_64chars(new_nft["tertiary_venue"])
        asset_presenting_sponsor = split_into_64chars(new_nft["presenting_sponsor"])
        asset_merchandising_partner = split_into_64chars(new_nft["merchandising_partner"])
        asset_technology_partner = split_into_64chars(new_nft["technology_partner"])
        asset_blockchain_partner = split_into_64chars(new_nft["blockchain_partner"])
        asset_championship_game_ball = split_into_64chars(new_nft["championship_game_ball"])
        asset_participating_countries = split_into_array(new_nft["participating_countries"])
        asset_video =  new_nft["file_source"]
        asset_file_name =  new_nft["file_name"]
        asset_event_name =  split_into_64chars(new_nft["event_name"])
        asset_cert_of_authenticity =  split_into_64chars(new_nft["certificate_of_authenticity"])


        #thumbnails
        response = requests.get(asset_image)
        img = io.BytesIO(response.content)
        files = {'file': img.getvalue()}
        # print(f"Uploading {asset_image} to IPFS")
        res = requests.post("https://ipfs.blockfrost.io/api/v0/ipfs/add", headers= custom_header, files=files)
        hashed = res.json()['ipfs_hash']

        mime = magic.from_buffer(img.read(), mime=True)

        #video
        response = requests.get(asset_video)
        video = io.BytesIO(response.content)
        files = {'file': video.getvalue()}
        # print(f"Uploading {asset_image} to IPFS")
        res = requests.post("https://ipfs.blockfrost.io/api/v0/ipfs/add", headers= custom_header, files=files)
        video_hashed = res.json()['ipfs_hash']


        video_mime = magic.from_buffer(video.read(), mime=True)

        file_array = [{
            "name": asset_file_name,
            "src": f"ipfs://{video_hashed}",
            "mediaType": video_mime
        }]

        metadata[721][policy_id_hex][asset_name] = {
                                "2023 Event Name": asset_event_name,
                                "Product Description": asset_description,
                                "name": asset_name,
                                "image": f"ipfs://{hashed}",
                                "mediaType": mime,
                                "Apparel": asset_product,
                                "Limited Quantity": asset_limited_quantity,
                                "Date": asset_date,
                                "Official Event Website": asset_official_event_website,
                                "Location": asset_location,
                                "Apparel Company": asset_apparel_company,
                                "2023 Men's World Championship Venue": asset_championship_venue,
                                "2023 Championship Venue Location": asset_venue_location,
                                "2023 Secondary Competition Venue": asset_secondary_venue,
                                "2023 Tertiary Competition Venue": asset_tertiary_venue,
                                "2023 Presenting Sponsor of the World Lacrosse Men's Championship": asset_presenting_sponsor,
                                "2023 Official Merchandising Partner & Sponsor": asset_merchandising_partner,
                                "Apparel Technology Partner": asset_technology_partner,
                                "Blockchain development supported by": asset_blockchain_partner,
                                "2023 Official Championship Game Ball": asset_championship_game_ball,
                                "2023 Participating Countries": asset_participating_countries,
                                "Certificate of Authenticity": asset_cert_of_authenticity,
                                "files": file_array
                                
                            }

        payment_signing_key = PaymentSigningKey.load(f"keys/{asset_name}.skey")
        payment_verification_key = PaymentVerificationKey.load(f"keys/{asset_name}.vkey")

        result = cip8.sign(message= asset_name, signing_key= payment_signing_key, network=cardano_network, attach_cose_key=True)


        public_key = result['key'][-64:]
        signature = split_into_64chars(result['signature'])

        merchadise_result = cip8.sign(message= asset_name, signing_key= merchadise_signing_key, network=cardano_network, attach_cose_key=True)

        merchadise_public_key = merchadise_result['key'][-64:]
        merchadise_signature = split_into_64chars(merchadise_result['signature'])

        metadata[721][policy_id_hex][asset_name]['Signature'] = signature
        metadata[721][policy_id_hex][asset_name]['Issuer'] = {}

        metadata[721][policy_id_hex][asset_name]['Issuer']['Signature'] = merchadise_signature
        metadata[721][policy_id_hex][asset_name]['Issuer']['Public Key'] = merchadise_public_key

        nft1 = AssetName(asset_name_bytes)
        my_asset[nft1] = 1


    my_nft[policy_id] = my_asset



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

        for shirt in shirts:
            shirt_id = shirt["id"]
            sql = f"UPDATE shirts set status=1 where id = {shirt_id}"
            mycursor.execute(sql)
            mydb.commit()
            print(f"updated status for shirt {shirt_id}")
        
    except Exception as e:   
        print("Transaction faild, sleeping 10")
        print(str(e))
        time.sleep(10)  

    query = "select * from shirts where status = 0 limit 5"
    mycursor.execute(query)
    shirts = mycursor.fetchall()

print(f"Finished minting all NFT's")
