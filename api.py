# pylint: disable=unused-import

import argparse
import binascii
import io

from flask import Flask, jsonify, render_template, request, make_response, send_from_directory
from flask_cors import CORS

from werkzeug.exceptions import BadRequest
import os
from os.path import exists
import mysql.connector
from pycardano import *
from blockfrost import BlockFrostApi, ApiError, ApiUrls,BlockFrostIPFS
from dotenv import load_dotenv

from derive import derive_tag_key, derive_undiversified_key
from config import SDMMAC_PARAM, ENC_FILE_DATA_PARAM, ENC_PICC_DATA_PARAM, SDM_MASTER_KEY, UID_PARAM, CTR_PARAM, REQUIRE_LRP
from libsdm import decrypt_sun_message, validate_plain_sun, InvalidMessage, EncMode


app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
CORS(app)

load_dotenv()

network = os.getenv('network')
mysql_host = os.getenv('mysql_host')
mysql_user = os.getenv('mysql_user')
mysql_password = os.getenv('mysql_password')
mysql_database = os.getenv('mysql_database')
blockfrost_apikey = os.getenv('blockfrost_apikey')
blockfrost_ipfs = os.getenv('blockfrost_ipfs')
policy_id_hex = "65da4fc679cb48187f1e72387526bb899c4b9fa8c746ce070f85d58f"
base_name = "HOODIE"
vkey_prefix = "a4010103272006215820"
placeholder_paymentkey = '{"type": "PaymentSigningKeyShelley_ed25519", "description": "PaymentSigningKeyShelley_ed25519", "cborHex": "5820PLACEHOLDER"}'

if network=="testnet":
    base_url = ApiUrls.preprod.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET

api = BlockFrostApi(project_id=blockfrost_apikey, base_url=base_url)        
cardano = BlockFrostChainContext(project_id=blockfrost_apikey, base_url=base_url)


def connect_to_db():
    global mydb 
    mydb = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database,
        auth_plugin="mysql_native_password"
    )


def parse_parameters():
    

    param_mode = "ParamMode.SEPARATED"
    posted_data = request.get_json()

    print(posted_data)

    enc_picc_data = posted_data[ENC_PICC_DATA_PARAM]
    enc_file_data = posted_data[ENC_FILE_DATA_PARAM]
    sdmmac = posted_data[SDMMAC_PARAM]
    asset_name = posted_data['asset_name']


    # breakpoint()

    if not enc_picc_data:
        raise BadRequest(f"Parameter {ENC_PICC_DATA_PARAM} is required")

    if not sdmmac:
        raise BadRequest(f"Parameter {SDMMAC_PARAM} is required")

    try:
        enc_file_data_b = None
        enc_picc_data_b = binascii.unhexlify(enc_picc_data)
        sdmmac_b = binascii.unhexlify(sdmmac)

        if enc_file_data:
            enc_file_data_b = binascii.unhexlify(enc_file_data)
    except binascii.Error:
        raise BadRequest("Failed to decode parameters.") from None


    return param_mode, enc_picc_data_b, enc_file_data_b, sdmmac_b, asset_name


@app.route('/video/hoodie')
def show_hoodie():
    return send_from_directory('assets', 'rotating_hoodie.mp4')


@app.route('/api/tag',methods = ['POST', 'GET', 'OPTIONS'])
def sdm_api_info():


    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "POST": 
        try:
            return _internal_sdm(with_tt=False, force_json=True)
        except BadRequest as err:
            return jsonify({
                "status": "NOK",
                "message": err
            })
        except Exception as err:
            return jsonify({
                "status": "NOK",
                "message": err
            })            
    else:
        return jsonify({
                "status": "NOK",
                "message": "Something went wrong"
            }) 



def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "https://store.cardano.org")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def joinall(value):
    s = ''.join(value)
    return s

# pylint:  disable=too-many-branches, too-many-statements, too-many-locals
def _internal_sdm(with_tt=False, force_json=False):
    param_mode, enc_picc_data_b, enc_file_data_b, sdmmac_b, asset_name = parse_parameters()
    

    try:
        res = decrypt_sun_message(
                                  sdm_meta_read_key=derive_undiversified_key(SDM_MASTER_KEY, 1),
                                  sdm_file_read_key=lambda uid: derive_tag_key(SDM_MASTER_KEY, uid, 2),
                                  picc_enc_data=enc_picc_data_b,
                                  sdmmac=sdmmac_b,
                                  enc_file_data=enc_file_data_b)


        connect_to_db()
        mycursor = mydb.cursor(dictionary=True)

        picc_data_tag = res['picc_data_tag']
        uid = res['uid']
        read_ctr_num = res['read_ctr']
        file_data = res['file_data']
        encryption_mode = res['encryption_mode'].name

        file_data_utf8 = ""

        

        if res['file_data']:
            file_data_unpacked = file_data

            file_data_utf8 = file_data_unpacked.decode('utf-8', 'ignore')

        # breakpoint()

        try:
            print("bypassing insert into DB")
            # sql = "INSERT INTO scanned_keys (device_uid, counter) VALUES (%s, %s)"
            # values = (uid.hex().upper(), read_ctr_num)
            # mycursor.execute(sql, values)
            # mydb.commit()


        except mysql.connector.errors.IntegrityError:
            return jsonify({
                "status": "NOK",
                "message": "Key already scanned"
            })


        file_data_utf8 = file_data_utf8.lower()
        payment_key = placeholder_paymentkey.replace('PLACEHOLDER', file_data_utf8)
        payment_signing_key = PaymentSigningKey.from_json(payment_key)
        payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)
        payment_verification_key = str(payment_verification_key).split('"5820')[1].replace('"}','')

        asset_id = int(asset_name.replace('asset',''))
        asset_name = f"{base_name}{asset_id:04d}"
        asset_name_hex = asset_name.encode("utf-8").hex()

        subject = f"{policy_id_hex}{asset_name_hex}"


        vkey = f"{vkey_prefix}{payment_verification_key}"
        asset_data = api.asset(asset=subject)

        signature = joinall(asset_data.onchain_metadata.Signature)
        signed_message = {
            "signature": signature,
            "key": vkey,
        }

        # print(asset_data)

        result = cip8.verify(signed_message=signed_message, attach_cose_key=True)

        if result["verified"]:
            return jsonify({
                "status": "OK",
                "message": "Verification succesful",
                "asset": {
                    "name": asset_data.onchain_metadata.name,
                    "image": asset_data.onchain_metadata.files[0].src,
                    "color": asset_data.onchain_metadata.color,
                    "product": asset_data.onchain_metadata.product,
                    "description": asset_data.onchain_metadata.description,
                    "disclaimer": ''.join(asset_data.onchain_metadata.disclaimer),
                    "detailed_product_description" : "Cardano Foundation Proof of Concept Hoodie - NFC Enabled",
                    "certificate_authenticity" : "This NFT represents a Certificate of Authenticity for the Cardano Foundation Proof of Concept Hoodie by linking the physical product to this digital asset on the Cardano blockchain leveraging an NFC chip embedded inside the hoodie.",                    
                    "limited_quantity" : "1 of 250",
                    "production_country" : "India",
                    "sustainability_certificate" : "GOTS Certification licence number 015389",
                    "apparel_technology" : "Cardano Foundation",
                    "about_authenticated_products" : "https://store.cardano.org/pages/authenticated-products"
                }
            })

        else:
            return jsonify({
                "status": "NOK",
                "message": "Verification failed"
            })




    except InvalidMessage as e:
        print(str(e))
        return jsonify({
                "status": "NOK",
                "message": "Invalid signature"
            }) 
    except Exception as e:
        print(str(e))
        return jsonify({
                "status": "NOK",
                "message": "Something went wrong"
            })






if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OTA NFC Server')
    parser.add_argument('--host', type=str, nargs='?', help='address to listen on')
    parser.add_argument('--port', type=int, nargs='?', help='port to listen on')


    print(network)

    args = parser.parse_args()

    app.run(host=args.host, port=args.port)
