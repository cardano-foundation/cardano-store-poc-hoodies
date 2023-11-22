import binascii

DERIVE_MODE="legacy"

# used for derivation of per-tag keys
SDM_MASTER_KEY = binascii.unhexlify("7481B1102F7C8D3D80291512F2F067AB")

# for encrypted mirroring
ENC_PICC_DATA_PARAM = "picc_data"
ENC_FILE_DATA_PARAM = "enc"

# for plaintext mirroring
UID_PARAM = "uid"
CTR_PARAM = "ctr"

# always applied
SDMMAC_PARAM = "cmac"

# accept only SDM using LRP, disallow usage of AES
REQUIRE_LRP = False
