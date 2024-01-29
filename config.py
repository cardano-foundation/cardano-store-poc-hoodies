import binascii

DERIVE_MODE = "legacy"

# Used for derivation of per-tag keys
SDM_MASTER_KEY = binascii.unhexlify("7481B1102F7C8D3D80291512F2F067AB")

# For encrypted mirroring
ENC_PICC_DATA_PARAM = "picc_data"
ENC_FILE_DATA_PARAM = "enc"

# For plaintext mirroring
UID_PARAM = "uid"
CTR_PARAM = "ctr"

SDMMAC_PARAM = "cmac"

# Accept only SDM using LRP, disallow usage of AES
REQUIRE_LRP = False
