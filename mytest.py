import datetime
from src import *
import sys,getopt

def align_init(allSymbols,variantTable=None):

	if variantTable:
		#設定使用 UnicodeTextScoreMatrix
		# 帶入異體字表
		mUTSM=UnicodeTextScoreMatrix(alphabet=allSymbols,variantTable=variantTable)
	else:
		#設定使用 UnicodeTextScoreMatrix
		mUTSM=UnicodeTextScoreMatrix(alphabet=allSymbols)

	# 初始化比對物件，帶入UnicodeTextScoreMatrix
	# 尚待處理：加入分數門檻。
	alignerObject = Aligner(matrix=mUTSM)

	return alignerObject

def align(
	refID,refString,qryID,qryString,
	msgType = 2, # 可能值為 1: 正式輸出, 2: Debug 輸出
	minCompLen=10,  #欲比對之字串低於此門檻，便停止
	distinctChars=None, #預輸入的不重複字 (optional)
	variantTable=None, # 異體字比對表，有傳值進來就會啟動異體字比對 (optional)
	multipleAlignment=False  #是否要進行多次比對
	):

	#輸出訊息用
	num_turns=0
	compareTaskQueue=[]  #用來存放比較工作的Queue
	msg =[] #累計Report

	t0 = datetime.datetime.now()
	
	#不重複字元清單
	dcs = distinctChars if distinctChars else "".join(set(list(refString)+list(qryString)))
	# if distinctChars:
	# 	dcs=distinctChars
	# else:
	# 	dcs="".join(set(list(refString)+list(qryString)))

	#處始化比對器
	aligner = align_init(dcs,variantTable)

	#比較句長於MIN_COMP_LENGTH，放入比較範圍Queue
	if (len(refString)>=minCompLen and len(qryString)>=minCompLen):
		compareTaskQueue=[(0,len(refString),0,len(qryString))]

	while(len(compareTaskQueue)>0):
		num_turns+=1 #迴圈記數
		#由Queue中，取出比較範圍
		# crBegin 可理解為 compare_ref_begin
		# cqBegin 可理解為 compare_qry_begin
		comInterval=compareTaskQueue.pop()
		crBegin,crEnd,cqBegin,cqEnd=comInterval
		#找出本次比較字串
		crString=refString[crBegin:crEnd]
		cqString=qryString[cqBegin:cqEnd]

		# t2 = datetime.datetime.now()
		
		#進行比對，不進行反向比對 (dna 比對專用)
		alignment = aligner.align(reference=crString, query=cqString,revcomp=False)
		# t3 = datetime.datetime.now()
		#print ("第{}次比對，花費：{:.7f} 秒".format(num_turns,(t3 - t2).microseconds*0.000001))

		#取得分數與長度
		arScore=alignment.score
		arLen=alignment.reference_end-alignment.reference_begin
		aqLen=alignment.query_end-alignment.query_begin
		
		#比對成果大於需求，表示有找到有效區段
		if 	((arLen  >=minCompLen)  and (aqLen >=minCompLen)): 
			msg=alignReport(alignment,refID,crString,qryID,cqString,comInterval,msgType,nturn=num_turns)

			#若 multipleAlignment == True 則進行切割與加入Queue
			#這部份考慮要廢掉了
			# 2020/03/09 先封存
			# if (multipleAlignment):
			# 	if ((arBegin-crBegin)>=minCompStrLen and (aqBegin-cqBegin)>=minCompStrLen):
			# 		compareTaskQueue.append((crBegin,arBegin,cqBegin,aqBegin))

			# 	if ((cqEnd-aqEnd)>=minCompStrLen and (crEnd-arEnd)>=minCompStrLen):
			# 		compareTaskQueue.append((arEnd,crEnd,aqEnd,cqEnd))
	
	return msg

def alignReport(alignment, refID,crString,qryID,cqString,compareInterval,
									msgType=2,nturn=-1):
	# msgType = 1, 正式輸出訊息
	# msgType = 2, Debug 訊息
	# msgType = 3, 原程式Report
	crBegin,crEnd,cqBegin,cqEnd=compareInterval

	# arBegin=alignment.reference_begin+crBegin
	# arEnd=alignment.reference_end+crBegin
	# aqBegin 可理解為 align_qry_begin
	# aqBegin=alignment.query_begin+cqBegin
	# aqEnd=alignment.query_end+cqBegin

	arScore=alignment.score
	# arLen=alignment.reference_end-alignment.reference_begin
	# aqLen=alignment.query_end-alignment.query_begin

	msg =[]
# class Alignment(object):
#     def __init__ (self, alignment, query, reference, matrix=None):
#sid1,sid2,score,align1,align2,s1_start,s1_end,s2_start,s2_end
#P1618_001_0007,T1799_001_0034,38,眾生---生死相續皆由不知常住真心,眾生無始生-死相續皆由不知常住真心,23,36,2,17
	if (msgType ==1): #判斷 1 的bit 是否有set
		m=alignment.alignment
		r = [refID,qryID,arScore,m[0].replace("〇","-"),m[2].replace("〇","-"),crBegin,crEnd,cqBegin,cqEnd]
		s="\t".join(str(d) for d in r)
		msg.append(s)
	
	elif (msgType==2): #判斷 2 的bit 是否有set 
		msg.append("========   My Report #{}  ========== ".format(nturn))
		msg.append("比對對象：Ref[{}:{}] ::  Query[{}:{}] ".format(crBegin,crEnd,cqBegin,cqEnd))
		msg.append("結果：score={}, 比對句：".format(arScore))
		msg.append("")
		msg+=alignment.alignment
		msg.append("")
		# msg.append(" "*4+"Ref [{}:{}]({}) {}".format(arBegin,arEnd,arLen,refString[arBegin:arEnd]))
		# msg.append(" "*4+"Qry [{}:{}]({}) {}".format(aqBegin,aqEnd,aqLen,qryString[aqBegin:aqEnd]))
	
	elif (msgType==3):
		r=alignment.alignment_report()
		#r=alignment.alignment
		msg.append(r)

	return msg

def usage():
	print("usage: mytest.py [-o output FILE ] [-dpv] FILE1 [FILE2] ")


# main function starts here:

#重要的流程控制參數，與外來參數有關
OUTPUT_filename=None
inputFormat="fullText"  # 選項為：fullText  與 sentencePair
variantMode = False # Ture/False 控制是否進行異體字比對
variantFileLocation ="data/variants.txt"
mssageType=1 # 1: 正式輸出, 2: Debug輸出 (可由command line 加上-d 來控制)

try:
	opts, args = getopt.getopt(sys.argv[1:], "dpvo:")
except getopt.GetoptError as err:
	# print help information and exit:
	print(err)  # will print something like "option -a not recognized"
	usage()
	sys.exit(2)

#抓取 -o 的選項與值
for opt,value in opts:
	if "-o" in opt:
		OUTPUT_filename = value
	if "-p" in opt:
		inputFormat = "sentencePair"
	if "-v" in opt:
		variantMode = True
	if "-d" in opt:
		mssageType=2

#一般讀檔，需要兩個檔
#測試始否給定 FILE1 與 FILE2
if (inputFormat=="fullText" and len(args) !=2) :
	print ("Please specify FILE1 and FILE2 for comparsion.")
	usage()
	sys.exit(2)
elif (inputFormat=="sentencePair" and len(args) !=1) :
	print ("Please specify Sentence Pair FILE  for comparsion.")
	usage()
	sys.exit(2)

compareStringArray=[]  #紀錄用來比較的Array

print("開始執行比對：")

if inputFormat == "fullText":
	#開檔, reference & query
	# 2020/03/09 輸入格式改為：id \tab text
	with open(args[0],'r') as ifile1, open(args[1],'r') as ifile2:
		print("資料模式：兩全文檔比對")
		print("Reading Files：{},{}".format(args[0],args[1]))
		ref=ifile1.read().strip().split("\t")
		qry=ifile2.read().strip().split("\t")
		compareStringArray.append((ref[0],ref[1],qry[0],qry[1]))
elif inputFormat == "sentencePair":
	# 2020/03/09 輸入格式改為：id1 \tab text1 \tab id2 \tab text2
	#開檔，依序讀入需要分割的字串
	print("Reading File：{}".format(args[0]))
	print("資料模式：Sentence Pair")
	with open(args[0],'r') as ifile1:
		for s in ifile1:
			compareStringArray.append(tuple(s.strip().split("\t")))

vt=None
if variantMode:
	vt=VariantTable(variantCSVFile=variantFileLocation)
	print("異體字比對：On")


loop=0

t0 = datetime.datetime.now()

alignMessges=[]
task_length=len(compareStringArray)
while (len(compareStringArray)):
	if (loop%1000)==0:
		tnow = datetime.datetime.now()
		tms=(tnow-t0).microseconds
		progress = loop/task_length*100
		speed = (tms)/(loop+1)
		expTime = speed*(task_length-loop)*0.000001
		#print("\r開始比對... {:.0f}% ({:.2f} ms/pair) (剩餘時間:{:.2} sec)".format(progress,speed,expTime),end="",flush=True)
		print("\r開始比對... {:.0f}% ".format(progress),end="",flush=True)

	refID,refString,qryID,qryString = compareStringArray.pop()
	loop+=1
	#print("{},".format(loop),end="")
	# endtime = datetime.datetime.now()
	# print ("執行完成，花費：{:.6f} 秒".format((endtime-starttime).microseconds*0.000001))
	rMsg = align(refID,refString,qryID,qryString,mssageType,variantTable=vt)
	alignMessges.extend(rMsg)
	if (not OUTPUT_filename):
		for m in rMsg:
			print(m)


t1= datetime.datetime.now()
print ("")
print ("執行完成，花費：{} 秒".format((t1-t0).seconds))

#取得內建 report 字串
# r=alignment.alignment_report()

# #先用簡單作法，讓字元能夠正確對應，之後會修正
# r=r.replace("|","｜").replace("*","＊").replace("-","〇")

if (OUTPUT_filename):
	print ("結果輸出於：{}".format(OUTPUT_filename))
	with open(OUTPUT_filename,'w') as ofile:
		ofile.write("\r\n".join(alignMessges))