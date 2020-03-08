import datetime
import sys,getopt

variantFileLocation ="data/variants.txt"

try:
	opts, args = getopt.getopt(sys.argv[1:],"-pv")
except getopt.GetoptError as err:
	# print help information and exit:
	print(err)  # will print something like "option -a not recognized"
	usage()
	sys.exit(2)

if (len(args) !=1) :
	print ("Please specify Sentence Pair FILE  for comparsion.")

print("-"*25+"Method 1, varDict[v]=[v,v1,v2,v3]..."+"-"*25)

T0 = datetime.datetime.now()

# 1: Line by Line
# 2: CSV Style
MESSAGE_TYPE=2
variant_dict = {}
variant_dict2 = {}

#開啟異體字表 (M1)
try:
    with open(variantFileLocation,'r') as vfile:
        for s in vfile:
            vlist=s.strip().split(",")
            for v in vlist:
                if v in variant_dict:
                    variant_dict[v]=list(set(variant_dict[v]+ vlist[:]))
                else:
                     variant_dict[v] = vlist[:]
except OSError as e:
    print("異體字資料檔 ({}) 開啟失敗，請確認檔案是否存在".format(variantFileLocation))


#開啟異體字表 (M3)
vgrpNo=0 # Variant Group Number = Line No.
try:
    with open(variantFileLocation,'r') as vfile:
        for s in vfile:
            vgrpNo+=1
            vlist=s.strip().split(",")
            for v in vlist:
                if v in variant_dict2:
                    variant_dict2[v].append(vgrpNo)
                else:
                     variant_dict2[v] = [vgrpNo]
except OSError as e:
    print("異體字資料檔 ({}) 開啟失敗，請確認檔案是否存在".format(variantFileLocation))


T1= datetime.datetime.now()
# print ("[1]讀取異體字表，花費：{:.6f} 秒".format((T1-T0).microseconds*0.000001))

loop=1
#開啟比對字串檔

with open(args[0],'r') as ifile1:
    loop+=1
    for s in ifile1:
        t0 = datetime.datetime.now()
        refString,qryString=(s.strip().split("\t"))
        #print("[{}] \nr:{}\nq:{}".format(loop,refString,qryString))
        t1 = datetime.datetime.now()
        # print ("  [2.1]讀取入字串：{:.6f} 秒".format((t1-t0).microseconds*0.000001))
        dcs="".join(set(list(refString)+list(qryString)))
        t2 = datetime.datetime.now()
        # print ("  [2.2]製作不重複字串，花費：{:.6f} 秒".format((t2-t1).microseconds*0.000001))
        
        st = datetime.datetime.now()
        for i,v in enumerate(dcs):
            if v in variant_dict:
                for vc in dcs[i+1:]:
                    if vc in variant_dict[v]:
                        pass
                        print("({},{})".format(v,vc),end="")
        print()

        timedata =[]

        et = datetime.datetime.now()
        timedata.append("{:.6f}".format((et-st).microseconds*0.000001))
        if (MESSAGE_TYPE == 1): print ("  [2.3](important) 尋找是否在vairant 中[M1]，花費：{:.6f} 秒".format((et-st).microseconds*0.000001))

        st = datetime.datetime.now()
        for i,v in enumerate(dcs):
            if v in variant_dict:
                for vc in variant_dict[v]: 
                    if vc in dcs[i+1:]:
                        print("({},{})".format(v,vc),end="")
        print()

        et = datetime.datetime.now()
        timedata.append("{:.6f}".format((et-st).microseconds*0.000001))
        if (MESSAGE_TYPE == 1): print ("  [2.3](important) 尋找是否在vairant 中[M2]，花費：{:.6f} 秒".format((et-st).microseconds*0.000001))

        groupMatchDict={}
        MatchList=[]
        st = datetime.datetime.now()
        for i,v in enumerate(dcs):  
            if v in variant_dict2:
                for vgno in variant_dict2[v]:
                    if vgno in groupMatchDict:
                        groupMatchDict[vgno].append((i,v))
                        if (len(groupMatchDict[vgno])==2):
                            MatchList.append(groupMatchDict[vgno])
                    else:
                        groupMatchDict[vgno]=[(i,v)]
                
        for grp in MatchList:
            for inx, dataX in enumerate(grp[:-1]):
                for dataY in grp[inx+1:]:
                    print("({}({}),{}({}))".format(dataX[1],dataX[0],dataY[1],dataY[0]))

        et = datetime.datetime.now()
        timedata.append("{:.6f}".format((et-st).microseconds*0.000001))
        if (MESSAGE_TYPE == 1): print ("  [2.3](important) 尋找是否在vairant 中[M3]，花費：{:.6f} 秒".format((et-st).microseconds*0.000001))

        if (MESSAGE_TYPE == 2):
            print("timedata,"+",".join(timedata))

        #print(dcs)

T2= datetime.datetime.now()
# print ("[2] 讀取字串與處理共費：{:.6f} 秒".format((T2-T1).microseconds*0.000001))

T2= datetime.datetime.now()
print ("[1+2]全部執行費時：{:.6f} 秒".format((T2-T0).microseconds*0.000001))
print ("-"*40)