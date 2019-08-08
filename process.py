import os
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
cred = credentials.Certificate('privatekey.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

if not os.path.exists("hypo"):
    os.mkdir("hypo")
if not os.path.exists("hypo/steps"):
    os.mkdir("hypo/steps")
if not os.path.exists("brm"):
    os.mkdir("brm")
if not os.path.exists("brm/steps"):
    os.mkdir("brm/steps")

# constants
MAX_NUM_HYPO_NODES = 5
COLLECTION_ID = "STUDY2"

# making title line
hypoCsv = "HPMOD,Student User Name,firstPredict,secondPredict,finalPredict,"
for i in range(MAX_NUM_HYPO_NODES):
    hypoCsv += "node_" + str(i+1) + ","
for i in range(MAX_NUM_HYPO_NODES):
    hypoCsv += "arrowLabel_" + str(i+1) + ","
for i in range(MAX_NUM_HYPO_NODES):
    hypoCsv += "direction_" + str(i+1) + ","
hypoCsv += "\n"

# brm title line
brmCsv = "BRMMOD,Student User Name,type,info\n"

# filling in data
docs = db.collection(COLLECTION_ID).get()
for doc in docs:
    docDict = doc.to_dict()
    if "hypo" in docDict:
        hypoDict = json.loads(docDict["hypo"])
        hypoCsv += "HPMOD,"
        hypoCsv += doc.id + ","
        hypoCsv += hypoDict["firstPrediction"] + ","
        hypoCsv += hypoDict["secondPrediction"] + ","
        nodes = hypoDict["nodes"]
        arrowLabels = hypoDict["arrowLabels"]
        directions = hypoDict["directions"]
        hypoCsv += directions[-1] + ","
        for i in range(MAX_NUM_HYPO_NODES):
            if i >= len(nodes):
                hypoCsv += "N/A,"
            else:
                hypoCsv += nodes[i] + ","
        for i in range(MAX_NUM_HYPO_NODES):
            if i >= len(arrowLabels):
                hypoCsv += "N/A,"
            else:
                hypoCsv += arrowLabels[i] + ","
        for i in range(MAX_NUM_HYPO_NODES):
            if i >= len(directions):
                hypoCsv += "N/A,"
            else:
                hypoCsv += directions[i] + ","
        hypoCsv += "\n"
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
        stepFile = open("hypo/steps/" + doc.id + ".csv", "w")
        stepFile.write(stepCsv)
        stepFile.close()

    if "brm" in docDict:
        brmDict = json.loads(docDict["brm"])
        stepCsv = "type,title,selected,isCorrect\n"
        steps = brmDict
        for step in steps:
            stepCsv += step["type"] + ","
            if step["type"] == "LINK":
                stepCsv += step["link"] + ","
                stepCsv += "\n"
            elif step["type"] == "QUIZ":
                stepCsv += step["title"] + ","
                stepCsv += step["selected"] + ","
                stepCsv += str(step["isCorrect"]) + ","
                stepCsv += "\n"
            else:
                print("error: type doesn't exist")
            stepFile = open("brm/steps/" + doc.id + ".csv", "w")
            stepFile.write(stepCsv)
            stepFile.close()

f = open("hypo/hypo.csv", "w")
f.write(hypoCsv)
f.close()
