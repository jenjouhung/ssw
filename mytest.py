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
	refString,qryString,
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
			msg=alignReport(alignment,crString,cqString,comInterval,msgType=2,nturn=num_turns)

			#若 multipleAlignment == True 則進行切割與加入Queue
			#這部份考慮要廢掉了
			if (multipleAlignment):
				if ((arBegin-crBegin)>=minCompStrLen and (aqBegin-cqBegin)>=minCompStrLen):
					compareTaskQueue.append((crBegin,arBegin,cqBegin,aqBegin))

				if ((cqEnd-aqEnd)>=minCompStrLen and (crEnd-arEnd)>=minCompStrLen):
					compareTaskQueue.append((arEnd,crEnd,aqEnd,cqEnd))
	
	return msg

def alignReport(alignment, crString,cqString,compareInterval,nturn=-1,msgType=2):
	# msgType = 1, 正式輸出訊息
	# msgType = 2, Debug 訊息
	# msgType = 3, 原程式Report
	crBegin,crEnd,cqBegin,cqEnd=compareInterval

	arBegin=alignment.reference_begin+crBegin
	arEnd=alignment.reference_end+crBegin
	# aqBegin 可理解為 align_qry_begin
	aqBegin=alignment.query_begin+cqBegin
	aqEnd=alignment.query_end+cqBegin

	arScore=alignment.score
	arLen=alignment.reference_end-alignment.reference_begin
	aqLen=alignment.query_end-alignment.query_begin

	msg =[]
# class Alignment(object):
#     def __init__ (self, alignment, query, reference, matrix=None):
	if (msgType ==1): #判斷 1 的bit 是否有set 
		pass
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
	print("usage: mytest.py [-o output FILE ] [-pv] FILE1 [FILE2] ")


# main function starts here:

#重要的流程控制參數，與外來參數有關
OUTPUT_filename=None
inputFormat="fullText"  # 選項為：fullText  與 sentencePair
variantMode = False # Ture/False 控制是否進行異體字比對
variantFileLocation ="data/variants.txt"

try:
	opts, args = getopt.getopt(sys.argv[1:], "pvo:")
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

if inputFormat == "fullText":
	#開檔, reference & query
	with open(args[0],'r') as ifile1, open(args[1],'r') as ifile2:
		refString=ifile1.read().strip()
		qryString=ifile2.read().strip()
		compareStringArray.append((refString,qryString))
elif inputFormat == "sentencePair":
	#開檔，依序讀入需要分割的字串
	with open(args[0],'r') as ifile1:
		for s in ifile1:
			compareStringArray.append(tuple(s.strip().split("\t")))


vt=None
if variantMode:
	vt=VariantTable(variantCSVFile=variantFileLocation)


loop=0

t0 = datetime.datetime.now()

while (len(compareStringArray)):
	# starttime = datetime.datetime.now()
	refString,qryString = compareStringArray.pop()
	loop+=1
	#print("{},".format(loop),end="")
	# endtime = datetime.datetime.now()
	# print ("執行完成，花費：{:.6f} 秒".format((endtime-starttime).microseconds*0.000001))
	alignMessges = align(refString,qryString,variantTable=vt)
	for m in alignMessges:
		print(m)


t1= datetime.datetime.now()
print ("執行完成，花費：{} 秒".format((t1-t0).seconds))
print ("-"*40)

#取得內建 report 字串
# r=alignment.alignment_report()

# #先用簡單作法，讓字元能夠正確對應，之後會修正
# r=r.replace("|","｜").replace("*","＊").replace("-","〇")

if (OUTPUT_filename):
	with open(OUTPUT_filename,'w') as ofile:
		ofile.write("\r\n".join(alignMessges))