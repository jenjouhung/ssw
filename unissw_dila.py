from unissw import *

import sys,getopt
import os
import json

def usage():
	print("usage: python3 unissw_dila.py  [-c config FILE] -t task FILE")


def process_task_record(tr):
    r =[]
    output_file=None

    #檢查 file_base 設定
    file_base=os.path.dirname(__file__)
    if ("data_folder" in tr):
        file_base = tr["data_folder"]

    #檢查 output_file 設定
    if ("output_file" in tr):
        output_file = os.path.join(file_base,  tr["output_file"])

    if (tr["data_type"] =="p"):  # (P)air Mode, pair 檔案內含比對文字
        if not ("pair_file" in tr ):
            raise SystemExit("Error: 11 Task FILE ERROR: must set pair_file when data_type set to p. \n Occucrs in{}".format(tr))

        pair_file = os.path.join(file_base,  tr["pair_file"])

        print("Reading File：{}".format(pair_file))
        print("資料模式：Sentence Pair")
        with open(pair_file,'r') as ifile1:
            for s in ifile1:
                # 內容格式為：id1 \tab text1 \tab id2 \tab text2
                r.append(tuple(s.strip().split("\t")))
        return output_file,r


    elif (tr["data_type"] =="s"):  #  (S)eperate mode: id, sentence 分開檔案儲存
        pass
    # "data_folder": "/data/5_GitArea/ssw/batch-data",
    # "data_type": "s",
    # "sent-file1":"a-sentences.tsv",
    # "sent-file2":"a-sentences.tsv",
    # "pair-file": "sentence-pairs.tsv",
    # "output_file":  "out/a-b.dat"

    elif (tr["data_type"] =="t"):  # (T)wo texts mode: 兩個文字檔，各自內含一句。
        if not ("sent_file1" in tr ):
            raise SystemExit("Error: 12 Task FILE ERROR: must set sent_file1 when data_type set to t. \n Occucrs in{}".format(tr))

        if not ("sent_file2" in tr ):
            raise SystemExit("Error: 13 Task FILE ERROR: must set sent_file2 when data_type set to t. \n Occucrs in{}".format(tr))

        sent_file1 = os.path.join(file_base,  tr["sent_file1"])
        sent_file2 = os.path.join(file_base,  tr["sent_file2"])

        with open(sent_file1,'r') as ifile1, open(sent_file2,'r') as ifile2:
            print("資料模式：兩全文檔比對")
            print("Reading Files：\n [1] {} \n [2] {}".format(sent_file1,sent_file2))
            ref=ifile1.read().strip().split("\t")
            qry=ifile2.read().strip().split("\t")
            r.append((ref[0],ref[1],qry[0],qry[1]))
        return output_file,r
    else:
        raise SystemExit("Error: 1X unsupported data type:{}. \n Occucrs in{}".format(tr["data_type"],tr))

    return output_file,r


def unissw_dila_main():
    FILE_PATH=os.path.dirname(__file__)
    task_file=None
    config_file="config.json"

    #重要的流程控制參數，與外來參數有關
    OUTPUT_filename=None
    variantMode = False # Ture/False 控制是否進行異體字比對
    variantFile =os.path.join(FILE_PATH,"data","variants.txt")
    config_file=os.path.join(FILE_PATH,"config.json")
    messageType=1 # 1: 正式輸出, 2: Debug輸出 (可由command line 加上-d 來控制)
    compareStringArray=[]  #紀錄用來的字串的Array

    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:c:")
    except getopt.GetoptError as err:
        # print help information and exit:
        usage()
        sys.exit(2)

    for opt,value in opts:
        if "-c" in opt: config_file = value
        if "-t" in opt: task_file = value

    if not task_file:
        print ("You have to specify the path of the taskfile.")
        usage()
        exit()
    elif not os.path.isfile(task_file):
        print("Error: Task FILE ({}) does not exist.".format(task_file))
        exit() 

    #讀入 config檔
    config=read_config(config_file)

    #讀入 task檔
    tasks=[]
    with open(task_file,"r") as tfile:
        tasks = json.load(tfile)

    for t in tasks:
        OUTPUT_filename,compareStringArray= process_task_record(t)
        print_to_file = True if OUTPUT_filename else False

        if len(compareStringArray)==0:
            continue
    
        if (print_to_file): print("開始執行比對：")

        t0 = datetime.datetime.now()

        #進行資料比較
        alignMessges= run_align_task(compareStringArray,config,
                                messageType,variantMode, variantFile, print_to_file)

        t1= datetime.datetime.now()

        print ("\n執行完成，花費：{} 秒".format((t1-t0).seconds))

        if (OUTPUT_filename):
            print ("結果輸出於：{}".format(OUTPUT_filename))
            with open(OUTPUT_filename,'w') as ofile:
                ofile.write("\r\n".join(alignMessges))



if __name__ == '__main__':
    unissw_dila_main()