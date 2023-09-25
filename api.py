# pylint: disable=unused-import

import argparse
import binascii
import io

from flask import Flask, jsonify, render_template, request, make_response
from flask_cors import CORS

from werkzeug.exceptions import BadRequest
import os
from os.path import exists
import mysql.connector
from pycardano import *
from blockfrost import BlockFrostApi, ApiError, ApiUrls,BlockFrostIPFS
from dotenv import load_dotenv

from config import (
    CTR_PARAM,
    ENC_FILE_DATA_PARAM,
    ENC_PICC_DATA_PARAM,
    SDMMAC_PARAM,
    MASTER_KEY,
    UID_PARAM,
    DERIVE_MODE,
)

if DERIVE_MODE == "legacy":
    from libsdm.legacy_derive import derive_tag_key, derive_undiversified_key
elif DERIVE_MODE == "standard":
    from libsdm.derive import derive_tag_key, derive_undiversified_key
else:
    raise RuntimeError("Invalid DERIVE_MODE.")

from libsdm.sdm import (
    EncMode,
    InvalidMessage,
    ParamMode,
    decrypt_sun_message,
    validate_plain_sun,
)

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
    

    param_mode = ParamMode.SEPARATED
    posted_data = request.get_json()

    enc_picc_data = posted_data[ENC_PICC_DATA_PARAM]
    enc_file_data = posted_data[ENC_FILE_DATA_PARAM]
    sdmmac = posted_data[SDMMAC_PARAM]



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


    return param_mode, enc_picc_data_b, enc_file_data_b, sdmmac_b



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
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


# pylint:  disable=too-many-branches, too-many-statements, too-many-locals
def _internal_sdm(with_tt=False, force_json=False):
    param_mode, enc_picc_data_b, enc_file_data_b, sdmmac_b = parse_parameters()
    
    try:
        res = decrypt_sun_message(param_mode=param_mode,
                                  sdm_meta_read_key=derive_undiversified_key(MASTER_KEY, 1),
                                  sdm_file_read_key=lambda uid: derive_tag_key(MASTER_KEY, uid, 2),
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
            if param_mode == ParamMode.BULK:
                file_data_len = file_data[2]
                file_data_unpacked = file_data[3:3 + file_data_len]
            else:
                file_data_unpacked = file_data

            file_data_utf8 = file_data_unpacked.decode('utf-8', 'ignore')

        # try:
            sql = "INSERT INTO scanned_keys (device_uid, counter) VALUES (%s, %s)"
            values = (uid, read_ctr_num)
            mycursor.execute(sql, values)
            mydb.commit()


        # except Exception as e:


        return jsonify({
            "status": "OK",
            "uid": uid.hex().upper(),
            "file_data": file_data.hex() if file_data else None,
            "read_ctr": read_ctr_num,
            "enc_mode": encryption_mode
        })

    except InvalidMessage:
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
