#!/usr/bin/python3

from pn532.api import PN532


if __name__== "__main__":
    print('\nCTRL-C to quit. Place NFC tag near PN532 and copy the ID')
    print('Copy the ID to the NFC_KEY variable in bottender.py')
    nfc = PN532()

    # setup the device
    nfc.setup()

    # keep reading until a value is returned
    while True:
        read = nfc.read(1)
        print(read)
