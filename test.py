import os
from os.path import exists
from dotenv import load_dotenv
import mysql.connector
from pycardano import *

load_dotenv()
network = os.getenv('network')
mysql_host = os.getenv('mysql_host')
mysql_user = os.getenv('mysql_user')
mysql_password = os.getenv('mysql_password')
mysql_database = os.getenv('mysql_database')
wallet_mnemonic = os.getenv('wallet_mnemonic')
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


connect_to_db()
mycursor = mydb.cursor(dictionary=True)

if not exists(f"keys/policy.skey") and not exists(f"keys/policy.vkey"):
    policy_key_pair = PaymentKeyPair.generate()
    policy_signing_key = policy_key_pair.signing_key
    policy_verification_key = policy_key_pair.verification_key
    policy_signing_key.save(f"keys/policy.skey")
    policy_verification_key.save(f"keys/policy.vkey")

for i in range(1, 251):
    if not exists(f"keys/{i}.skey") and not exists(f"keys/{i}.vkey"):
        payment_key_pair = PaymentKeyPair.generate()
        payment_signing_key = payment_key_pair.signing_key
        payment_verification_key = payment_key_pair.verification_key
        payment_signing_key.save(f"keys/{i}.skey")
        payment_verification_key.save(f"keys/{i}.vkey")

    payment_signing_key = PaymentSigningKey.load(f"keys/{i}.skey")
    payment_verification_key = PaymentVerificationKey.load(f"keys/{i}.vkey")

    str_payment_part = str(payment_signing_key).split('"5820')[
        1].replace('"}', '')
    print(f"{str_payment_part} \t\t {len(str_payment_part)}")

    sql = f"INSERT INTO assets (private_key) VALUES ('{str_payment_part}')"
    values = (str_payment_part)
    mycursor.execute(sql)
    mydb.commit()
