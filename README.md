# cf-merchstore-api

## Hardware

An NFC reader/writer is required to write information on the chips. [This reader/writer](https://www.shopnfc.com/en/nfc-readers-writers/212-utrust-3700-f-nfc-writer.html) works well with the used NTAG 424 DNA chips. The chips can be [ordered here](https://www.nfc-tag-shop.de/NFC-Sticker-PET-25-mm-NTAG424-DNA-416-Byte-weiss/68984).

## Software

### TagXplorer

[TagXplorer](https://www.nxp.com/products/no-longer-manufactured/tagxplorer-pc-based-nfc-tag-reader-writer-tool:TAGXPLORER) can be used to read/write the chips.

- [Download](https://www.nxp.com/downloads/en/apps/SW4883.zip) TagXplorer.
- Extract the zip to, for example, `~/Software/sw488312/`.
- Try to execute it by double-clicking or by running `java -jar ~/Software/sw488312/TagXplorer-v1.2.jar` in a terminal.
- If it does not work, make sure your Java environment has been set up correctly.
- In case you see the error `java.lang.NoClassDefFoundError: javafx/application/Application`, please [download JavaFX](https://gluonhq.com/products/javafx/).
- Extract it to, for example, `~/Software/javafx-sdk-21.0.1/` and add the following lines to your .zshrc / .bashrc file:

```zsh
export JAVAFX_PATH="/Users/fabianbormann/Software/javafx-sdk-21.0.1/lib"
export PATH=$PATH:JAVAFX_PAT
```

- Run TagXplorer using  `java --module-path $JAVAFX_PATH --add-modules javafx.controls --add-modules javafx.fxml -jar ~/Software/sw488312/TagXplorer-v1.2.jar`.

### Decryption and Verification

This repository includes files from the MIT project [smd-backend](https://github.com/nfc-developer/sdm-backend) by nfc-developer, which are used for decryption and verification.

## Known Issues

For a new chip, the default keys are set to `0000000000000000`. The smd-backend code works fine only with this standard key and seems to have issues if the key is changed.

See:
-  [CAN NOT VALIDATE NON ZERO KEY SIGNED MESSAGES #39](https://github.com/nfc-developer/sdm-backend/issues/39)
-  [Server does not work with tagXplorer custom key ? #34](https://github.com/nfc-developer/sdm-backend/issues/34)

These issues require running the verification part of this project based on [an old smd-backend version from 2022](https://github.com/icedevml/sdm-backend/tree/a89a8381a7b680abff721f006085ec4d15f8c543). 
Furthermore, a special process for key generation/derivation must be followed.

## Key Generation

## Instructions
