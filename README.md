# isptutor_dataprocessor

## Instructions for installation

1. Run 'pip3 install --upgrade firebase-admin'

2. Go to https://console.cloud.google.com/iam-admin/serviceaccounts?authuser=0 in the Cloud Platform Console. Generate a new private key and save the JSON file. Then use the file to initialize the SDK:
```
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
cred = credentials.Certificate('path/to/serviceAccount.json')
firebase_admin.initialize_app(cred)

db = firestore.client()
```
Replace 'path/to/serviceAccount.json' with the path to your json file.

3. Run 'python3 process.py'


Reference: https://firebase.google.com/docs/firestore/quickstart?authuser=0