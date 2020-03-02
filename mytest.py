from src import *
import sys,getopt

# 低於此門檻，便不進行比較
min_comp_length=10

def usage():
	print("usage: mytest.py [-o output FILE ] FILE1 FILE2 ")

try:
	opts, args = getopt.getopt(sys.argv[1:], "o:")
except getopt.GetoptError as err:
	# print help information and exit:
	print(err)  # will print something like "option -a not recognized"
	usage()
	sys.exit(2)

#測試始否給定 FILE1 與 FILE2
if len(args) !=2 :
	print ("Please specify FILE1 and FILE2 for comparsion.")
	usage()
	sys.exit(2)

OUTPUT_filename=None

#抓取 -o 的選項與值
for opt,value in opts:
	if "-o" in opt:
		OUTPUT_filename = value

#設定兩檔案名稱
INPUT_filename1=args[0]
INPUT_filename2=args[1]

#開檔1
with open(INPUT_filename1,'r') as ifile:
	refString=ifile.read().strip()

#開檔2
with open(INPUT_filename2,'r') as ifile:
	qryString=ifile.read().strip()

distinctChars="".join(set(list(refString)+list(qryString)))

#設定使用 UnicodeTextScoreMatrix
mUTSM=UnicodeTextScoreMatrix(alphabet=distinctChars)

# 初始化比對物件，帶入UnicodeTextScoreMatrix
# 尚待處理：加入分數門檻。
aligner = Aligner(matrix=mUTSM)

num_turns=0

#輸出訊息用
outputMessage=[]


#比較句長於MIN_COMP_LENGTH，放入比較範圍Queue
if (len(refString)>=min_comp_length and len(qryString)>=min_comp_length):
	compareTaskQueue=[(0,len(refString),0,len(qryString))]

while(len(compareTaskQueue)>0):
	num_turns+=1 #迴圈記數
	#由Queue中，取出比較範圍
	# crBegin 可理解為 compare_ref_begin
	# cqBegin 可理解為 compare_qry_begin
	crBegin,crEnd,cqBegin,cqEnd=compareTaskQueue.pop()
	#找出本次比較字串
	crString=refString[crBegin:crEnd]
	cqString=qryString[cqBegin:cqEnd]
	
	outputMessage.append("========   My Report #{}  ========== ".format(num_turns))
	if(not OUTPUT_filename): print(outputMessage[-1])
	outputMessage.append(" 比對對象：Ref[{}:{}] ::  Query[{}:{}] ".format(crBegin,crEnd,cqBegin,cqEnd))
	if(not OUTPUT_filename): print(outputMessage[-1])

	"""
	print("------------- 本次 Ref ------------ ")
	print("[{}:{}] {}".format(crBegin,crEnd,crString))
	print("------------- 本次 Qry ------------ ")
	print("[{}:{}] {}".format(cqBegin,cqEnd,cqString))
	"""

	#進行比對，不進行反向比對 (dna 比對專用)
	alignment = aligner.align(
		reference=crString, 
		query=cqString,
		revcomp=False
		)

	#以比對起點，還原比較結果
	# arBegin 可理解為 align_ref_begin
	# cqBegin 可理解為 align_qry_begin
	arBegin=alignment.reference_begin+crBegin
	arEnd=alignment.reference_end+crBegin
	aqBegin=alignment.query_begin+cqBegin
	aqEnd=alignment.query_end+cqBegin

	arScore=alignment.score
	arLen=arEnd-arBegin
	aqLen=aqEnd-aqBegin

	outputMessage.append(" 比對結果：score={}".format(arScore))
	if (not OUTPUT_filename): print(outputMessage[-1])

	outputMessage.append(" "*4+"Ref [{}:{}]({}) {}".format(arBegin,arEnd,arLen,refString[arBegin:arEnd]))
	if (not OUTPUT_filename): print(outputMessage[-1])

	outputMessage.append(" "*4+"Qry [{}:{}]({}) {}".format(aqBegin,aqEnd,aqLen,qryString[aqBegin:aqEnd]))
	if (not OUTPUT_filename): print(outputMessage[-1])

	#比對成果大於需求，表示有找到有效區段
	if 	((arLen  >=min_comp_length)  and (aqLen >=min_comp_length)): 
		if ((arBegin-crBegin)>=min_comp_length and (aqBegin-cqBegin)>=min_comp_length):
			outputMessage.append("前區段:[{}:{}] :: [{}:{}] 可放入比較".format(crBegin,arBegin,cqBegin,aqBegin))
			if (not OUTPUT_filename): print(outputMessage[-1])
			compareTaskQueue.append((crBegin,arBegin,cqBegin,aqBegin))
		else:
			outputMessage.append("前區段:[{}:{}] :: [{}:{}] XXXXX".format(crBegin,arBegin,cqBegin,aqBegin))
			print(outputMessage[-1])

		if ((cqEnd-aqEnd)>=min_comp_length and (crEnd-arEnd)>=min_comp_length):
			outputMessage.append("後區段:[{}:{}] :: [{}:{}] 可放入比較".format(arEnd,crEnd,aqEnd,cqEnd))
			compareTaskQueue.append((arEnd,crEnd,aqEnd,cqEnd))
			if (not OUTPUT_filename): print(outputMessage[-1])
		else:
			outputMessage.append("後區段:[{}:{}] :: [{}:{}] XXXXX".format(arEnd,crEnd,aqEnd,cqEnd))	
			if (not OUTPUT_filename): print(outputMessage[-1])
	else:
		if (not OUTPUT_filename): print("本次比對成果長度過短(ref:{},qry:{})，停止比對".format(arEnd-arBegin,aqEnd-aqBegin ))



		


"""
#取得內建 report 字串
r=alignment.alignment_report()

#先用簡單作法，讓字元能夠正確對應，之後會修正
r=r.replace("|","｜").replace("*","＊").replace("-","〇")

#測試是否需要輸出檔案
"""

if (OUTPUT_filename):
	with open(OUTPUT_filename,'w') as ofile:
		ofile.write("\r\n".join(outputMessage))
#else:
	#print("\n".join(outputMessage))