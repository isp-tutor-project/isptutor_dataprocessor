import os
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
cred = credentials.Certificate('privatekey.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

if not os.path.exists("steps"):
    os.mkdir("steps")

# constants
MAX_NUM_NODES = 5
COLLECTION_ID = "study2"

# making title line
csv = "HPMOD,Student User Name,initPredict,finalPredict,"
for i in range(MAX_NUM_NODES):
    csv += "node_" + str(i+1) + ","
for i in range(MAX_NUM_NODES):
    csv += "arrowLabel_" + str(i+1) + ","
for i in range(MAX_NUM_NODES):
    csv += "direction_" + str(i+1) + ","
csv += "\n"

# filling in data
docs = db.collection(COLLECTION_ID).get()
for doc in docs:
    docDict = doc.to_dict()
    if "hypo" in docDict:
        hypoDict = json.loads(docDict["hypo"])
        csv += "HPMOD,"
        csv += doc.id + ","
        csv += hypoDict["initialPrediction"] + ","
        nodes = hypoDict["nodes"]
        arrowLabels = hypoDict["arrowLabels"]
        directions = hypoDict["directions"]
        csv += directions[-1] + ","
        for i in range(MAX_NUM_NODES):
            if i >= len(nodes):
                csv += "N/A,"
            else:
                csv += nodes[i] + ","
        for i in range(MAX_NUM_NODES):
            if i >= len(arrowLabels):
                csv += "N/A,"
            else:
                csv += arrowLabels[i] + ","
        for i in range(MAX_NUM_NODES):
            if i >= len(directions):
                csv += "N/A,"
            else:
                csv += directions[i] + ","
        csv += "\n"
        # For recording steps in steps folder
        stepCsv = "action,object,index,info,date,time\n"
        steps = hypoDict["steps"]
        for step in steps:
            stepCsv += step["action"] + ","
            stepCsv += step["object"] + ","
            stepCsv += str(step["index"]) + ","
            stepCsv += step["info"] + ","
            stepCsv += step["timestamp"] + ","
            stepCsv += "\n"
        stepFile = open("steps/" + doc.id + ".csv", "w")
        stepFile.write(stepCsv)
        stepFile.close()

f = open("hypo.csv", "w")
f.write(csv)
f.close()
