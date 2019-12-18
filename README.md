# isptutor_dataprocessor

## Installation Instructions

1. type: `python3 -m venv venv`
2. type: `source venv/bin/activate`
3. type `pip install -r requirements.txt`
4. if you get a message (either now, or at any point in the future) that a new version of pip is available,
    type: `pip install --upgrade pip`
5. generate the keyfile

## Generating the keyfile
1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts?authuser=0 in the Cloud Platform Console. Generate a new private key and save the JSON file. 
2. name this file `privatekey.json` and place it in this directory 
    
    Reference: https://firebase.google.com/docs/firestore/quickstart?authuser=0

## Running the Script
1. if your command-line prompt doesn't begin with `(venv)`, type: `source venv/bin/activate`
2. type: `python3 process2.py CLASS_CODE
3. the generated output files will reside in `output/CLASS_CODE`
   