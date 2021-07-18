from unissw import *
from pathlib import Path
import sys
import getopt
import os
import json
from multiprocessing import Pool


class TaskObj():
    def __init__(self, config, messageType, variantMode, variantFile, task, logLevel=3):
        self.config = config

        self.logLevel = logLevel

        self.messageType = messageType
        self.variantMode = variantMode
        self.variantFile = variantFile
        self.task = task


def usage():
    print("usage: python3 unissw_dila.py  [-c config FILE] -t task FILE")


def resolveSentRange(segsDict, idRange):
    """
        segsDict 區段字典, key:text
        idRange id 區段，可能為x 或 x..y  ex: (10 or 11..13)
    """
    """
        
    """
    if (".." in idRange):
        s, e = idRange.split("..")
        r = ""
        # print ("------")
        # print("[{}]{}".format(s,segsDict[s]))
        # print("[{}]{}".format(e,segsDict[e]))
        # 考慮到最後一段才可能不滿...
        r = segsDict[e]  # 最後拿滿
        for n in range(int(e)-1, int(s)-1, -1):
            # print("n="+str(n))
            L = len(segsDict[str(n)])/2
            # print("Length={}".format(L))
            r = segsDict[str(n)][:int(L)]+r  # 其他拿前半

        return r
    else:
        # print ("------")
        # print("[{}]{}".format(idRange,segsDict[idRange]))
        return segsDict[idRange]


def process_task_record(tr, config, logLevel=3):
    r = []
    output_file = None
    logMessages = []

    # 檢查 file_base 設定
    file_base = os.path.dirname(__file__)
    if ("data_folder" in tr):
        file_base = tr["data_folder"]

    # Task ID 設定
    trid = tr["task_id"] if "task_id" in tr else "Unknown"

    # 檢查 output_file 設定
    if ("output_file" in tr):
        output_file = os.path.join(file_base,  tr["output_file"])

    if logLevel >= 1:
        logMessages.append("[#TID:{}][#TaskStart]".format(trid))
        # print(logMessages[-1])

    #  開始進行各 task record 細節比對
    if (tr["data_type"] == "s" or tr["data_type"] == "sc"):  # (S)eperate mode: id, sentence 分開檔案儲存

        CCCTH = -1  # common_char_count_th

        if not ("pair_file" in tr):
            raise SystemExit(
                "Error: 11 Task FILE ERROR: must set pair_file when data_type set to s. \n Occucrs in{}".format(tr))
        if not ("sent_file1" in tr):
            raise SystemExit(
                "Error: 12 Task FILE ERROR: must set sent_file1 when data_type set to s. \n Occucrs in{}".format(tr))
        if not ("sent_file2" in tr):
            raise SystemExit(
                "Error: 13 Task FILE ERROR: must set sent_file2 when data_type set to s. \n Occucrs in{}".format(tr))

        if not ("sent_fileo1" in tr):
            raise SystemExit(
                "Error: 14 測試檔案位址沒發現: must set sent_fileo1 \n Occucrs in{}".format(tr))

        if not ("sent_fileo2" in tr):
            raise SystemExit(
                "Error: 14 測試檔案位址沒發現: must set sent_fileo2 \n Occucrs in{}".format(tr))

        if tr["data_type"] == "s":
            if logLevel >= 2:
                logMessages.append(
                    "[#TID:{}][#DataMode]資料模式：pair, sentence 分離模式".format(trid))

        if tr["data_type"] == "sc":
            if logLevel >= 2:
                logMessages.append(
                    "[#TID:{}][#DataMode]資料模式：pair, sentence 分離模式 (有common character count)".format(trid))

        if logLevel >= 3:
            print(logMessages[-1])

        sent_file1 = os.path.join(file_base,  tr["sent_file1"])
        sent_file2 = os.path.join(file_base,  tr["sent_file2"])
        pair_file = os.path.join(file_base,  tr["pair_file"])
        sent_fileo1 = os.path.join(file_base,  tr["sent_fileo1"])
        sent_fileo2 = os.path.join(file_base,  tr["sent_fileo2"])

        with open(sent_file1, 'r') as sfile1, open(sent_file2, 'r') as sfile2, open(pair_file, 'r') as pfile:
            if logLevel >= 2:
                logMessages.append(
                    "[#TID:{}][#SentFILE-1]讀取資料檔：{}".format(trid, sent_file1))
            s1 = dict([(line.strip().split("\t")) for line in sfile1])

            if logLevel >= 2:
                logMessages.append(
                    "[#TID:{}][#SentFILE-2]讀取資料檔：{}".format(trid, sent_file2))
                print("[#TID:{}][#SentFILE-2]讀取資料檔：{}".format(trid, sent_file2))
            # for d in [ (line.strip().split("\t")) for line in sfile2]:
            #     print ("d[0]={},d[1]={}".format(d[0],d[1]))
            s2 = dict([(line.strip().split("\t")) for line in sfile2])

            if logLevel >= 3:
                print("\n".join(logMessages[-2:]))

            plines = [line.strip().split("\t") for line in pfile]

            ErrorCounts = 0

            # 開始測試
            with open(sent_fileo1, 'r') as sofile1, open(sent_fileo2, 'r') as sofile2:
                so1 = dict([(line.strip().split("\t")) for line in sofile1])
                so2 = dict([(line.strip().split("\t")) for line in sofile2])

            # ----- Test data consistency -----

                for sid1, sid2, ccc in plines:
                    if int(ccc) >= CCCTH:
                        sent1 = s1[sid1]
                        sent2 = s2[sid2]
                        sentR1 = resolveSentRange(so1, sid1)
                        sentR2 = resolveSentRange(so2, sid2)

                        if (sent1 != sentR1):
                            ErrorCounts += 1
                            print("比對不符")
                            print("S1({}).{}".format(sid1, sent1))
                            print("S1({}).{}".format(sid1, sentR1))
                            print("--------")
                        if (sent2 != sentR2):
                            ErrorCounts += 1
                            print("比對不符")
                            print("S2({}).{}".format(sid2, sent2))
                            print("S2({}).{}".format(sid2, sentR2))
                            print("--------")
                print("比對完成，共有{}筆不符!".format(ErrorCounts))
            # ---------------

    else:
        raise SystemExit("Error: 1X unsupported data type:{}. \n Occucrs in{}".format(
            tr["data_type"], tr))

    return output_file, r, logMessages


# 多共用Task 處理函式
def processTask(taskobj):
    #print("開始進行Task:  {}/{}".format(i+1,len(tasks)))

    trid = taskobj.task["task_id"] if "task_id" in taskobj.task else "Unknown"

    logLevel = taskobj.logLevel
    OUTPUT_filename, compareStringArray, logMessages = process_task_record(
        taskobj.task, taskobj.config, logLevel)
    print_to_file = True if OUTPUT_filename else False

    if len(compareStringArray) == 0:
        return logMessages

    # if (print_to_file):
    #     print("開始執行比對：")

    t1 = datetime.datetime.now()

    # 進行資料比較
    alignMessges = run_align_task(compareStringArray, taskobj.config,
                                  taskobj.messageType, taskobj.variantMode,
                                  taskobj.variantFile, print_to_file, batch_mode=True)

    t2 = datetime.datetime.now()

    if logLevel >= 2:
        logMessages.append(
            "[#TID:{}][#Info]執行完成，花費：{} 秒".format(trid, (t2-t1).seconds))
        if logLevel >= 3:
            print(logMessages[-1])

    if (OUTPUT_filename):
        # 確保有資料夾可以輸出
        outdir = os.path.dirname(OUTPUT_filename)
        Path(outdir).mkdir(parents=True, exist_ok=True)
        if len(alignMessges) > 1:  # 輸出結果, 1筆是檔頭

            if logLevel >= 2:
                logMessages.append("[#TID:{0}][#Output][#c:{2}]結果輸出於：{1}, 共{2}筆".format(
                    trid, OUTPUT_filename, len(alignMessges)-1))

            with open(OUTPUT_filename, 'w') as ofile:
                ofile.write("\r\n".join(alignMessges))

        else:  # 沒有結果, 不輸出
            if logLevel >= 2:
                logMessages.append(
                    "[#TID:{}][#Output][#c:0]沒有比對結果，不輸出。".format(trid))

    return logMessages
    # if ("log_file" in taskobj.config):
    #     logfile = open(os.path.join(".",taskobj.config["log_file"]),"a")
    #     logfile.write("\r\n".join(logMessages))
    #     logfile.write("\r\n")
    #     logfile.close()


def unissw_dila_main():
    FILE_PATH = os.path.dirname(__file__)
    task_file = None
    config_file = "config.json"

    # 重要的流程控制參數，與外來參數有關
    OUTPUT_filename = None
    variantMode = False  # Ture/False 控制是否進行異體字比對
    variantFile = os.path.join(FILE_PATH, "data", "variants.txt")
    config_file = os.path.join(FILE_PATH, "config.json")
    messageType = 1  # 1: 正式輸出, 2: Debug輸出 (可由command line 加上-d 來控制)
    compareStringArray = []  # 紀錄用來的字串的Array

    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:c:")
    except getopt.GetoptError as err:
        # print help information and exit:
        usage()
        sys.exit(2)

    for opt, value in opts:
        if "-c" in opt:
            config_file = value
        if "-t" in opt:
            task_file = value

    if not task_file:
        print("You have to specify the path of the taskfile.")
        usage()
        exit()
    elif not os.path.isfile(task_file):
        print("Error: Task FILE ({}) does not exist.".format(task_file))
        exit()

    # 讀入 config檔
    config = read_config(config_file)

    if ("log_file" in config):
        print("log將輸出於：{}".format(config["log_file"]))

    # log_message_level = 0, 完全不顯示Log Message
    # log_message_level = 1, 僅顯示總體訊息 (上有多少卷)
    # log_message_level = 2,
    # log_message_level = 3, 包含各卷比對細節 Default

    if "log_message_level" in config:
        logLevel = int(config["log_message_level"])
    else:
        logLevel = 3

    # 讀入 task.json檔
    task_json = []
    with open(task_file, "r") as tfile:
        task_json = json.load(tfile)

    t0 = datetime.datetime.now()

    # 準備工作項目
    taskObjList = [TaskObj(config, messageType, variantMode,
                           variantFile, t, logLevel) for t in task_json]

    # 進行多工設定
    if ("num_of_max_process" in config):
        pool = Pool(config["num_of_max_process"])  # Pool() 不放參數則默認使用電腦核的數量
    else:
        pool = Pool()

    msg = "程式運行開始，全部共有：{} 比對工作待進行。".format(len(taskObjList))
    print(msg)
    if ("log_file" in config):
        logfile = open(os.path.join(".", config["log_file"]), "w")
        logfile.write("{}\r\n".format(msg))
        logfile.close()

    # 進行多工處理
    task_done = 0
    tx = datetime.datetime.now()
    for msgs in pool.imap(processTask, taskObjList):
        tr = taskObjList[task_done].task

        trid = tr["task_id"] if "task_id" in tr else "Unknown"

        now = datetime.datetime.now()
        task_done += 1
        if logLevel >= 1:
            msgs.append("[#TID:{}][#TaskDone]已完成：{}/{} [Time:{}(秒)]".format(trid,
                        task_done, len(taskObjList), (now-tx).seconds))
            print(msgs[-1])

            if logLevel >= 2:
                msgs.append("-"*60)
                if logLevel >= 3:
                    print(msgs[-1])

        if ("log_file" in config):
            logfile = open(os.path.join(".", config["log_file"]), "a")
            logfile.write("\r\n".join(msgs))
            logfile.write("\r\n")
            logfile.close()

        tx = now

    # for taskobj in taskObjList:
    #     processTask(taskobj)

    t = datetime.datetime.now()
    msg = "執行完成，全部花費：{} 秒".format((t-t0).seconds)
    print(msg)
    if ("log_file" in config):
        logfile = open(os.path.join(".", config["log_file"]), "a")
        logfile.write("{}\r\n".format(msg))
        logfile.close()


if __name__ == '__main__':
    unissw_dila_main()
