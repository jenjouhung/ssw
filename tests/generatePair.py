import os
import csv,json


PAIR_FILE =  "tests/P185n1618_T39n1799_Pair.txt"
SENTENCE_FOLDER="tests/sentences"
OUTPUT_FILE = "tests/P185n1618_T39n1799_IDText.tsv"
task_queue =[]

#Read Sentence FILE
#結構必須是 ： SENTENCE_FOLDER/經號/xxx.json

print ("開始讀入Sentence 資料")
sentences_data ={}

for jing in os.listdir(SENTENCE_FOLDER):
    for sentFile in os.listdir(os.path.join(SENTENCE_FOLDER,jing)):
        #進入兩層目錄，開啟sentence 檔案
        filePath=os.path.join(SENTENCE_FOLDER,jing,sentFile)
        print("Loading ... " + filePath)
        with open(filePath, "r") as sjfile:
            #讀入json資料，變成 dict 結構
            data = json.loads(sjfile.read())
            # merge two dictionaries, python > 3.5
            sentences_data = {**sentences_data, **data} 

print ("開始讀入Pair 資料，並整合輸出")

#Read Pair File
try:
    with open (PAIR_FILE, "r") as csvfile,  open (OUTPUT_FILE, "w") as ofile:
        print("Processing ... " + PAIR_FILE)
        rows = csv.reader(csvfile)
        #讀入比對對象ID
        for rowX,rowY in rows:
            #參照行號資訊
            ofile.write("{}\t{}\t{}\t{}\r\n".format(
               rowX,sentences_data[rowX]["text"],
               rowY,sentences_data[rowY]["text"])
               )
except FileNotFoundError as e:
    print("[Fail] Pair File (csv): ({})".format(PAIR_FILE))
    exit(2)

print ("檔案輸出完成，檔案位置: "+OUTPUT_FILE)
