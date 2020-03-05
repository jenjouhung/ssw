import six
from six.moves import range
from . import libssw
from . import iupac
from ctypes import *
import datetime

__all__ = ["ScoreMatrix", "NucleotideScoreMatrix", "UnicodeTextScoreMatrix","VariantTable","Aligner", "Alignment"]

class VariantTable(object):
    def __init__(self,variantCSVFile=None,variantList=None):
        self._variantDict= None
        self._variantList = variantList  # 可給定variants 群組list, [[v1,v2,v3],[v2,v4,v6]...] 初始化
        self._variantCSVFile=variantCSVFile #或給定CSV檔案，內容無檔頭為一行一群組

        if (self._variantList):
            #若給定 variantList 則以 variantList 進行_variantDict建構
            self.readList(variantList)
            if (self._variantCSVFile):
                print("[Warning] variantList is given,  variantCSVFile will be ingore. ")
        elif (self._variantCSVFile):
             #若給定 variantCSVFile，則讀取variantCSVFile， 進行_variantDict建構
            self.readCSV(variantCSVFile)
        
    def readCSV(self,variantCSVFile):
        """
                Read varaint CSV file
                Output to  self._variantList, and proceed to self.readList for next step
        """
        self._variantCSVFile=variantCSVFile
        self._variantList = []
        try:
            with open(variantCSVFile,'r') as vfile:
                for s in vfile:
                    vlist=s.strip().split(",")
                    self._variantList.append(vlist)
        except IOException as e:
            print("[Fail] fail in reading variant file: ({})".format(variantCSVFile))
            exit(2)
        
        self.readList(self._variantList)

    def readList(self,variantList):
        """
               Build _variantList by reading self._variantList
        """
        self._variantList = variantList
        self._variantDict={}

        for record in self._variantList:
            for v in record:
                if v in  self._variantDict:
                    self._variantDict[v]=list(set( self._variantDict[v]+ record[:]))
                else:
                    self._variantDict[v]= record[:]
    
    def get_table(self):
        return self._variantDict
    
    def set_table(self,val):
        self._variantDict = val

    table = property(get_table, set_table)


class ScoreMatrix(object):
    #程式預設 alphabet 是A~N的DNA可能值字串
    def __init__(self, alphabet=None, match=3, mismatch=-3,varmatch=2,variantTable=None):
        self._match = match
        self._mismatch = mismatch
        self._varmatch = varmatch  #異體字比對分數
        self._varTable = None
        if variantTable:
            self._varTable = variantTable.table

        # 一旦設定，就會重算score 矩陣，因此必須在 self._varTable  才進行 alphabet 設定
        self.alphabet = alphabet 

    def __getstate__(self):
        state = (self._match, self._mismatch, self.alphabet)
        return state

    def __setstate__(self, state):
        (self._match, self._mismatch, self.alphabet) = state

    def __eq__(self, other):
        return \
            (self._match == other._match) and \
            (self._mismatch == other._mismatch) and \
            (self._alphabet == other._alphabet)

    def get_mismatch(self):
        return self._mismatch
    def set_mismatch(self, val):
        self._mismatch = val
        self._init_matrix()
    mismatch = property(get_mismatch, set_mismatch)

    def get_match(self):
        return self._match
    def set_match(self, val):
        self._match = val
        self._init_matrix()
    match = property(get_match, set_match)

    def get_alphabet(self):
        return self._alphabet

    def set_alphabet(self, alphabet):
        #alphabet 輸入值為一連續字串，之後用tuple()分成各字元一筆
        self._alphabet = tuple(alphabet) if alphabet else tuple()

        #將分筆後的資料建立
        self.symbol_map = {symbol.upper(): idx for (idx, symbol) in enumerate(self._alphabet)}
       
       # 順便初始化match 與 dismatch 矩陣
        self._init_matrix()
       

    #這裡設定 alphabet 的讀寫需經過  get_alphabet, set_alphabet 兩函式
    alphabet = property(get_alphabet, set_alphabet)

    def _init_matrix(self):
        # libssw.matrix_type = cint_8
        # 初始化match 與 dismatch 矩陣，大小為 alphabet 長度的平方 * cint_8
        _matrix_type = libssw.matrix_type * (len(self.alphabet) ** 2)

        # 以上述大小產生矩陣空間
        #然後利用iter_matrix() 產生得分矩陣
        #因過慢而改用 memset 
        # self._matrix = _matrix_type(*self.iter_matrix())
     
        self._matrix = _matrix_type()

        #利用ctypes 的memset 與 addressof 函式，初始化比對array
        memset(addressof(self._matrix),self.mismatch,(len(self.alphabet) ** 2))
        
        # t0 = datetime.datetime.now()

        # L=len(self.alphabet)
        # for i, data in enumerate(self.alphabet):
        #     self._matrix[i*L+i]=self.match

        t1 = datetime.datetime.now()
        #print ("memory fill[原]，花費：{:.7f} 秒".format((t1-t0).microseconds*0.00001))

        if self._varTable:
            L=len(self.alphabet)
            for i, ch in enumerate(self.alphabet):
                self._matrix[i*L+i]=self.match
                if ch in self._varTable:
                    for j in range(i+1,L):
                        chx=self.alphabet[j]
                        if chx in self._varTable[ch]:
                            #print("({}({}),{}({}))".format(ch,i,chx,j),end="")
                            self._matrix[i*L+j]=self._varmatch

            t2 = datetime.datetime.now()
            #print ("memory fill[with異體字]，花費：{:.7f} 秒".format((t2-t1).microseconds*0.00001))


    def iter_matrix(self):
        for row_symbol in self.alphabet:
            for col_symbol in self.alphabet:
                #遞迴兩圈，透過_get_score 取得分數，並建立得分矩陣
                yield self._get_score(row_symbol, col_symbol)

    def _get_score(self, symbol_1, symbol_2):
        #預設的得分方式，一致得match分，不一致得mismatch分
        return (self.match if self.test_match(symbol_1, symbol_2) else self.mismatch)

    def test_match(self, symbol_1, symbol_2):
        return symbol_1.upper() == symbol_2.upper()

    def convert_sequence_to_ints(self, seq):
        seq = seq.upper()
        # libssw::#35  symbol_type = c_int16 (2020/02/23 修)
        # c_int16 由 ctypes module 定義, 表達c 型態
        # 以下兩行應該是來產生足量(=seq長度)的 _seq_instance 空間
        _seq_type = libssw.symbol_type * len(seq)
        _seq_instance = _seq_type()
        for (idx, symbol) in enumerate(seq):
            #self.symbol_map, 設定內部alphabet 時產生
            #這邊改用 c_int 16 (2020/02/23 修), 也就是能使用32768個不重複字
            #就是將sequence 內容，套入利用 alphabet產生的symbol_map, 轉換為數字
            _seq_instance[idx] = self.symbol_map[symbol]
        return _seq_instance

#ScoreMatrix 為父類別
#我們需要仿製這個部份，自訂需要的ScoreMatrix
class NucleotideScoreMatrix(ScoreMatrix):
    #預設範例中，aplphabet = None, 表示未給定外來alphabet, 但後續會產生
    def __init__(self, alphabet=None, **kw):
        #iupac.py:44, iupac.NucleotideAlphabet = T-N
        #設定這個alphabet 的目的：1. 產生後續的match/dismatch Table, 2. 用來決定n
        alphabet = alphabet if alphabet is not None else iupac.NucleotideAlphabet
        #初始化父類別, #9-#13 設定 alphabet, 
        # **kw 效果，尚未釐清！！！
        # 父層init 只設定 match 與  mismatch 分數
        #產生父類別後，順便呼叫父類別初始化函式，其中會設定到alphabet, 觸發set_alphabet 函式(#45)
        #這個函式會順便產生一個由這些alphabet 產生對應int的 內部symbol_map
        super(NucleotideScoreMatrix, self).__init__(alphabet=alphabet, **kw)

    def test_match(self, symbol_1, symbol_2):
        _sym_1 = symbol_1.upper()
        _sym_2 = symbol_2.upper()
        if _sym_1 == _sym_2:
            return True
        if _sym_1 in iupac.NucleotideTable:
            matches = iupac.NucleotideTable[_sym_1]["matches"]
            return (_sym_2 in matches)
        return super(NucleotideScoreMatrix, self).test_match(symbol_1, symbol_2)


#自訂 UnicodeTextScoreMatrix 類別
class UnicodeTextScoreMatrix(ScoreMatrix):
    def __init__(self, alphabet, variantTable=None,**kw):
        if alphabet == None:
             raise ValueError("UnicodeTextScoreMatrix needs alphabet value." )
        
        #交由父類別初始化
        super(UnicodeTextScoreMatrix, self).__init__(alphabet=alphabet, variantTable=variantTable,**kw)

    def test_score(self, symbol_1, symbol_2):
        return self._get_score(symbol_1, symbol_2)
    
    #為了新增異體字的partial match, 需要在這個ScoreMatrix中新增
    # 1. pMatch 參數 (get, set函式)
    # 2. overwrite _get_score 函式
    # 3. overwrite _test_match 函式，這個函式跟列印有關，可能需要改line 270



#初始點
class Aligner(object):
    def __init__(self, reference=None, matrix=None, datatype="dna", gap_open=3, gap_extend=1):
        #gap_open 與 gap_extend 定義：
        #就是Insert 與 Delete 分數。雖然給的是正分，但系統中是減分作用
        #gap_open 應該是在最前面與最後面，扣分大
        #gap_extend 是在中間的insert/delete，扣分小
        #如果參考基準需要被多次使用，可以藉由下面這行先定義參考基準(A)。
        #但可能有 score matrix 的前提，需注意，尚未釐清！！
        self.reference = reference
        self.matrix = matrix
        self.datatype = datatype
        if not(self.matrix)  and datatype != None:
            #這裡我們需要仿製這個程序，產生我們需要的ScoreMatrix obj, 以便
            # 1. 初始化alphabet的, 之後便可以通過 convert to Int, n 值 設定 
            # 2. 由alphabet產生score Matrix 
            if datatype == "dna":
                #若無給定matrix 且有設定 molecule 為 "dna" (函式預設值), 進入此段
                #預設評分產生器, 物件型態, NucleotideScoreMatrix, 父類別為ScoreMatrix
                self.matrix = NucleotideScoreMatrix()
            else:
                raise ValueError("Unrecognized molecule type '%s'" % molecule)
        self.gap_open = gap_open
        self.gap_extend = gap_extend
        if self.gap_open <= self.gap_extend:
            raise ValueError("gap_open must always be greater than gap_extend")

    def align(self, query='', reference=None, revcomp=True):
        # query(B) , reference(A), 比較對象(B)與參考基準(A)
        # revcomp 是否進行互補DNA Sequence比較，見#135- #139，若為True, 
        # 則在進行完正向後，會將refernce 字串進行互補轉換後，再進行一次比對
        # 互補轉換有點類似 A --> T,  T--> A, C-->G,  G-->C 但是似乎有更複雜的組合
        # 這點進行純內容比較時，一定要設為False

        # XXX: I really don't find this part of SSW useful, which
        # is why i broke alignment into two stages, so you can use 
        # the low level interface if you wish.
        #以下參數意義，尚未釐清！！
        # flags, 用來控制哪些path需要回傳
        # 因為是用bit控制，細節可參閱 ssw.c 的 ssw_align 輸入定義部份
        # 總和來說：
        # flags =0, 不回傳任何路徑
        # flags = 1, 總是回傳路徑
        # flags = 2, 只回傳分數 > filter的路徑
        # flags = 4, 只回傳 alignment部份大於filter_distance的比對結果 (ref,query 任一滿足即可)
        # flags = 6, (2,4 都 on ) 上述兩條件都需成立才回傳
        flags = 1  
        # filter score 與 flags 有關，在某些情況下，filter score 會擔負起過濾最低分數的責任。
        filter_score = 0
        # filter filter_distance 與 flags filter_distance  會擔負起過濾最低match長度的責任。
        filter_distance = 0

        #mask_length = max(15, len(query) // 2)
        #mask_length < = 15 時，系統不會去找second best
        #最佳結束點的 加減 mask_length, 不會用來找 second best, 但也只找second best
        mask_length = 16
        # 若在Aligner 初始化時有設定過參考基準(A)，在此可以不用給
        reference = reference if reference != None else self.reference
        #呼叫底層_align函式進行比較
        res = self._align(query, reference, flags, filter_score, filter_distance, mask_length)
        #若上層關掉此選項，之後不會進去。
        if revcomp:
            query_rc = iupac.nucleotide_reverse_complement(query)
            res_rc = self._align(query_rc, reference, flags, filter_score, filter_distance, mask_length)
            if res_rc.score > res.score:
                res = res_rc
        return res
    
    #確實如同上一手註解，我們比較字串時，可以直接呼叫這個底層函式
    #
    def _align(self, query, reference, flags, filter_score, filter_distance, mask_length, score_size=2): 
        # convert_sequence_to_ints, #66
        # matrix 是 score 物件, score 物件 內有 convert_sequence_to_ints 轉換為數字對應
        # 目前數字大小為 c_int16 #2020/02/23 修正
        # 總結來說，需要的工作為：
        # 1. 自訂一種符合我們需要的matrix函式, 並產生alphabet 表 與 ScoreMatrix [必要]
        # 2. 關掉 reverse [必要]
        # 3. 關掉 sw_sse2_by_byte 的執行 [次要]
        _query = self.matrix.convert_sequence_to_ints(query)
        _reference = self.matrix.convert_sequence_to_ints(reference)

        #利用query(B) 產生profile
        #ssw_profile_init = libssw.ssw_init (in ssw.c)
        #n值 = len(self.matrix.alphabet),  所以讓matrix.alphabet = 比較過程中所需的可能值，即可解問題
        profile = libssw.ssw_profile_init(
                        _query,  #POINTER(c_int16) #2020/02/23 修正
                        len(query), # c_int32
                        self.matrix._matrix, #POINTER(c_int8)
                        len(self.matrix.alphabet),  # n值所在地
                        score_size #c_int8
                    )
        if self.gap_open <= self.gap_extend:
            raise ValueError("gap_open must always be greater than gap_extend")
        alignment = libssw.ssw_align_init(
            profile, #ssw_profile_p
            _reference, #POINTER(c_int16) #2020/02/23 修正
            len(_reference), #c_int32
            self.gap_open, #c_uint8
            self.gap_extend,  #c_uint8
            flags,#c_uint8
            filter_score, # c_uint16
            filter_distance, #c_int32
            mask_length) #c_int32

        #alignment 收到的回傳值，是s_align結構，在ssw.h : #48-#58 定義
        #內容為: ssw.c 中的 ssw_align 在取得 best物件後，再加上trace path後，包裝的結果
        #將結果包裝成較為容易使用的物件
        alignment_instance = Alignment(alignment, query, reference, self.matrix)
        
        #釋放記憶體
        libssw.ssw_profile_del(profile)
        libssw.ssw_align_del(alignment)
        return alignment_instance

class Alignment(object):
    def __init__ (self, alignment, query, reference, matrix=None):
        self.score = alignment.contents.score
        self.score2 = alignment.contents.score2
        self.reference = reference
        self.reference_begin = alignment.contents.ref_begin
        self.reference_end = alignment.contents.ref_end
        self.query = query
        self.query_begin = alignment.contents.query_begin
        self.query_end = alignment.contents.query_end
        self.query_coverage = (self.query_end - self.query_begin + 1) / len(self.query)
        self.reference_coverage = (self.reference_end - self.reference_begin + 1) / len(self.reference)
        self.matrix = matrix
        self._cigar_string = [alignment.contents.cigar[idx] for idx in range(alignment.contents.cigarLen)]

    @property
    def iter_cigar(self):
        for val in self._cigar_string:
            op_len = libssw.cigar_int_to_len(val)
            op_char = libssw.cigar_int_to_op(val).decode("latin")
            yield (op_len, op_char)

    @property
    def cigar(self):
        cigar = ""
        if self.query_begin > 0:
            cigar += str(self.query_begin) + "S"
        cigar += str.join('', (str.join('', map(str, cstr)) for cstr in self.iter_cigar))
        end_len = len(self.query) - self.query_end - 1
        if end_len != 0:
            cigar += str(end_len) + "S"
        return cigar

    @property
    def alignment(self):
        r_index = 0
        q_index = 0
        r_seq = self.reference[self.reference_begin: self.reference_end + 1]
        q_seq = self.query[self.query_begin: self.query_end + 1]
        r_line = m_line = q_line = ''
        match_flag = lambda rq: '|' if self.matrix.test_match(*rq) else '*'
        for (op_len, op_char) in self.iter_cigar:
            op_len = int(op_len)
            if op_char.upper() == 'M':
                # match between reference and query
                ref_chunk = r_seq[r_index: r_index + op_len]
                query_chunk = q_seq[q_index: q_index + op_len]
                r_line += ref_chunk
                q_line += query_chunk
                match_seq = str.join('', map(match_flag, zip(ref_chunk, query_chunk)))
                m_line += match_seq
                r_index += op_len
                q_index += op_len
            elif op_char.upper() == 'I':
                # insertion into reference
                r_line += '-' * op_len
                m_line += ' ' * op_len
                q_line += q_seq[q_index: q_index + op_len]
                #  only query index change
                q_index += op_len
            elif op_char.upper() == 'D':
                # deletion from reference
                r_line += r_seq[r_index: r_index + op_len]
                m_line += ' ' * op_len
                q_line += '-' * op_len
                #  only ref index change
                r_index += op_len
        return (r_line, m_line, q_line)

    # XXX: all of these count functions are ineffecient

    @property
    def match_count(self):
        return self.alignment[1].count('|')

    @property
    def mismatch_count(self):
        return self.alignment[1].count('*')

    @property
    def insertion_count(self):
        cnt = 0
        for (op_len, op_char) in self.iter_cigar:
            if op_char.upper() == 'I':
                cnt += op_len
        return cnt

    @property
    def deletion_count(self):
        cnt = 0
        for (op_len, op_char) in self.iter_cigar:
            if op_char.upper() == 'D':
                cnt += op_len
        return cnt

    def alignment_report(self, width=60, header=True):
        def window(lines, width):
            idx = 0
            while 1:
                res = []
                for line in lines:
                    res.append(line[idx:idx+width])
                if not any(res):
                    break
                yield (res, idx)
                idx += width

        margin_width = len(str(max(self.query_end, self.reference_end))) + 8
        rpt = ''
        if header:
            rpt += "Score = %s, Matches = %s, Mismatches = %s, Insertions = %s, Deletions = %s\n" % (self.score, self.match_count, self.mismatch_count, self.insertion_count, self.deletion_count)
            rpt += '\n'
        for (lines, offset) in window(self.alignment, width - margin_width):
            for (name, seq_offset, line) in zip(["ref", "", "query"], [self.reference_begin, None, self.query_begin], lines):
                if name:
                    line_offset = seq_offset + offset + 1
                    left_margin = "%s %s" % (name.ljust(5), line_offset)
                else:
                    left_margin = ""
                rpt += "%s%s\n" % (left_margin.ljust(margin_width), line)
            rpt += '\n'
        return rpt
