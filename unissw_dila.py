from unissw import *

import sys,getopt
import os
import json

def usage():
	print("usage: python3 unissw_dila.py  [-c config FILE] -t task FILE")

def main():

    FILE_PATH=os.path.dirname(__file__)
    task_file=None
    config_file="config.json"

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
        print("Error: taskfile ({}) does not exist.".format(task_file))
        exit()

    if not os.path.isfile(config_file):
        print("No config file been found, will use system default config.")       


if __name__ == '__main__':
    main()  # 或是任何你想執行的函式