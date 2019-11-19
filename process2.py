#!/usr/bin/env python3
import argparse
import os
import json
import re
import sys

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# constants
MAX_NUM_HYPO_NODES = 7
CONDITIONS = ["cond1", "cond2", "cond3"]
CONDITION_HYPOS = {
    "cond1": ["initial", "final"],
    "cond2": ["initial", "opposite", "final"],
    "cond3": ["final"]
}


def mkdirs(class_code):
    if not os.path.exists(class_code):
        os.mkdir(class_code)
    for curr_cond in CONDITIONS:
        curr_cond_dir = os.path.join(class_code, curr_cond)
        if not os.path.exists(curr_cond_dir):
            os.mkdir(curr_cond_dir)
        for hypo in CONDITION_HYPOS[curr_cond]:
            curr_hypo_steps = "%sHypo_steps" % hypo
            curr_hypo_steps_dir = os.path.join(curr_cond_dir, curr_hypo_steps)
            if not os.path.exists(curr_hypo_steps_dir):
                os.mkdir(curr_hypo_steps_dir)
        brm_cond = os.path.join(curr_cond_dir, "brm")
        if not os.path.exists(brm_cond):
            os.mkdir(brm_cond)


def write_stud_file_rec(fp, data):
    fields = ['userID', 'preTestScore', 'condition', 'firstPrediction', 'secondPrediction']
    numeric_flds = ["preTestScore"]
    line = ""
    for fld in fields:
        if fld in numeric_flds:
            val = data.get(fld, "N/A")
            if "N/A" == val:
                line += '"%s",' % val
            else:
                line += "%s," % val
        else:
            line += '"%s",' % data.get(fld, "N/A")
    line = line.rstrip(',')
    line += "\n"
    fp.write(line)

def write_rq_rec(fp, data):
    fields = ['selectedArea', 'selectedTopic', 'selectedVariable']
    line = '"RQMOD","%s",' % data['userID']
    for fld in fields:
        try:
            line += '"%s",' % data['rqted']['moduleState'][fld]['index']
        except KeyError:
            line += '"N/A",'
    line = line.rstrip(',')
    line += "\n"
    fp.write(line)

def write_brm_steps(class_code, condition, data):
    brm = data['brm']
    brm_hdr = "type,title,selected,isCorrect\n"
    step_file_name = os.path.join(class_code, condition, "brm", "%s.csv" % data['userID'])
    with open(step_file_name, "w") as fh:
        for step in brm:
            stepCsv = step["type"] + ","
            if step["type"] == "LINK":
                stepCsv += step["link"] + ","
                stepCsv += "\n"
            elif step["type"] == "QUIZ":
                stepCsv += '"' + re.sub("\s+", " ", step["title"].replace('"', "'")) + '"' + ","
                stepCsv += '"' + step["selected"].replace('"', '""') + '"' + ","
                stepCsv += str(step["isCorrect"]) + ","
                stepCsv += "\n"
            else:
                print("error: type doesn't exist")
            fh.write(stepCsv)

def mk_hypo_hdr():
    hypo_hdr = "HPMOD,Student User Name,prediction,predictionValue,"
    for i in range(MAX_NUM_HYPO_NODES):
        hypo_hdr += "node_" + str(i+1) + ","
    for i in range(MAX_NUM_HYPO_NODES):
        hypo_hdr += "arrowLabel_" + str(i+1) + ","
    for i in range(MAX_NUM_HYPO_NODES):
        hypo_hdr += "direction_" + str(i+1) + ","
    hypo_hdr += "notes\n"
    return hypo_hdr


def write_hypo_data(fp, class_code, which_hypo, data):
    userID = data['userID']
    condition = data['condition']
    hypo_data = data[which_hypo + 'Hypo']
    line = '"HPMOD","%s","%s","%s",' % \
        (userID, hypo_data["currentPrediction"], hypo_data["currentPredictionValue"]) 
    nodes = hypo_data['nodes']
    arrow_labels = hypo_data['arrowLabels']
    directions = hypo_data['directions']
    # print(len(nodes), nodes)
    # print(len(arrow_labels), arrow_labels)
    # print(len(directions), directions)
    # sys.exit(0)
    for i in range(MAX_NUM_HYPO_NODES):
        if i >= len(nodes):
            line += '"N/A",'
        else:
            line += '"%s",' % nodes[i]
    for i in range(MAX_NUM_HYPO_NODES):
        if i >= len(arrow_labels):
            line += '"N/A",'
        else:
            line += '"%s",' % arrow_labels[i]
    for i in range(MAX_NUM_HYPO_NODES):
        if i >= len(directions):
            line += '"N/A",'
        else:
            line += '"%s",' % directions[i]
    notes = hypo_data.get('notes', 'N/A')
    line += '"%s"\n' % notes.replace('\n', ' ')
    # line = line.rstrip(',')
    # line += '\n';
    fp.write(line)

    # create a seperate *hypo_steps/userID.csv file for the student
    steps_file = os.path.join(class_code, condition, "%sHypo_steps" % which_hypo, "%s.csv" % userID)
    steps_hdr = "action,object,index,info,date,time\n"

    with open(steps_file, "w") as fh:
        fh.write(steps_hdr)
        for step in hypo_data.get('steps', []):
            line = ""
            for fld in ["action", "object", "index", "info", "timestamp"]:
                line += '"%s",' % step[fld]
            line = line.rstrip(',')
            line += "\n"        
            fh.write(line)

def get_collection(private_key_file, class_code):
    # Use a service account
    cred = credentials.Certificate(private_key_file)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    class_ref = db.collection(class_code)
    return class_ref

def get_condition_data(class_ref, class_code, condition):
    print("condition: {}".format(condition))
    cond_dir = os.path.join(class_code, condition)
    stud_file = os.path.join(cond_dir, "students.csv")
    rq_file = os.path.join(cond_dir, "rqted.csv")
    initial_hypo_file = os.path.join(cond_dir, "initialHypo.csv")
    opposite_hypo_file = os.path.join(cond_dir, "oppositeHypo.csv")
    final_hypo_file = os.path.join(cond_dir, "finalHypo.csv")
    stud_hdr = "Student User Name,preTestScore,condition,firstPrediction,secondPrediction\n"
    rq_hdr = "RQMOD,Student User Name,selectedArea,selectedTopic,selectedVariable\n"
    hypo_hdr = mk_hypo_hdr()
    initial_hypo_fp = None
    opposite_hypo_fp = None
    final_hypo_fp = open(final_hypo_file, "w")
    with open(stud_file, "w") as stud_fp, \
         open(rq_file, "w") as rq_fp:
        if "initial" in CONDITION_HYPOS[condition]:
            initial_hypo_fp = open(initial_hypo_file, "w")
            initial_hypo_fp.write(hypo_hdr)
        if "opposite" in CONDITION_HYPOS[condition]:
            opposite_hypo_fp = open(opposite_hypo_file, "w")
            opposite_hypo_fp.write(hypo_hdr)
        stud_fp.write(stud_hdr)
        rq_fp.write(rq_hdr)
        query = class_ref.where('condition', '==', condition)
        for doc in query.stream():
            user_id = doc.id
            data = doc.to_dict()
            print('\tuserID: {}'.format(user_id))
            updates = {
                'userID': user_id,
                'rqted': json.loads(data.pop('rqted', '{}')),
                'brm': json.loads(data.pop('brm', '[]'))
            }
            for curr_hypo in CONDITION_HYPOS[condition]:
                updates[curr_hypo+'Hypo'] = json.loads(data.pop(curr_hypo+'Hypo', '{}'))
            # throw away kruft
            data.pop('hypo', '')
            # throw away stuff which shouldn't be there
            data.pop('oppositeHypo', '')
            data.update(updates)
            write_stud_file_rec(stud_fp, data)
            write_rq_rec(rq_fp, data)
            write_brm_steps(class_code, condition, data)
            if initial_hypo_fp:
                write_hypo_data(initial_hypo_fp, class_code, "initial", data)
            if opposite_hypo_fp:
                write_hypo_data(opposite_hypo_fp, class_code, "opposite", data)
            # all conditions have a final hypo
            write_hypo_data(final_hypo_fp, class_code, "final", data)
        if initial_hypo_fp:
            initial_hypo_fp.close()
        if opposite_hypo_fp:
            opposite_hypo_fp.close()
    final_hypo_fp.close()

# for which_hypo in CONDITION_HYPOS[condition]:
    #     hypo_file = "%sHypo.csv"


    # # hypo title line
    # 
    
    # # filling in data
    # docs = db.collection(COLLECTION_ID).get()
    # for doc in docs:
    #     docDict = doc.to_dict()
    #     # rq
    #     if "rqted" in docDict:
    #         rqDict = json.loads(docDict["rqted"])
    #         rqCsv += "RQMOD,"
    #         rqCsv += doc.id + ","
    #         rqCsv += str(rqDict["moduleState"]["selectedArea"]["index"]) + ","
    #         rqCsv += str(rqDict["moduleState"]["selectedTopic"]["index"]) + ","
    #         rqCsv += str(rqDict["moduleState"]["selectedVariable"]["index"]) + ","
    #         rqCsv += "\n"

    #     # hypo
    #     if "hypo" in docDict:
    #         hypoDict = json.loads(docDict["hypo"])
    #         hypoCsv += "HPMOD,"
    #         hypoCsv += doc.id + ","
    #         hypoCsv += hypoDict["firstPrediction"] + ","
    #         hypoCsv += hypoDict["secondPrediction"] + ","
    #         nodes = hypoDict["nodes"]
    #         arrowLabels = hypoDict["arrowLabels"]
    #         directions = hypoDict["directions"]
    #         hypoCsv += directions[-1] + ","
    #         for i in range(MAX_NUM_HYPO_NODES):
    #             if i >= len(nodes):
    #                 hypoCsv += "N/A,"
    #             else:
    #                 hypoCsv += nodes[i] + ","
    #         for i in range(MAX_NUM_HYPO_NODES):
    #             if i >= len(arrowLabels):
    #                 hypoCsv += "N/A,"
    #             else:
    #                 hypoCsv += arrowLabels[i] + ","
    #         for i in range(MAX_NUM_HYPO_NODES):
    #             if i >= len(directions):
    #                 hypoCsv += "N/A,"
    #             else:
    #                 hypoCsv += directions[i] + ","
    #         hypoCsv += "\n"
    

    # f = open("rqted/rq.csv", "w")
    # f.write(rqCsv)
    # f.close()
    # f = open("hypo/hypo.csv", "w")
    # f.write(hypoCsv)
    # f.close()

def main(private_key_file, class_code):
    mkdirs(class_code)
    class_ref = get_collection(private_key_file, class_code)
    for cond in CONDITIONS:
        get_condition_data(class_ref, class_code, cond)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-k",
                        action="store",
                        dest="keyfile",
                        help='private key file',
                        required=True)
    parser.add_argument("-c",
                        action="store",
                        dest="class_code",
                        required=True)
    args = parser.parse_args()
    print('keyfile: {}'.format(args.keyfile))
    print('class_code: {}'.format(args.class_code))
    main(args.keyfile, args.class_code)
