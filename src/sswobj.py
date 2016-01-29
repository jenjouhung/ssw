import libssw

__all__ = ["ScoreMatrix", "DNA_Matrix", "Aligner", "Alignment"]

def build_compliment_table():
    cmap = ((ord('G'), ord('C')), (ord('A'), ord('T')))
    _ctable = [chr(idx) for idx in xrange(0xff + 1)]
    case_delta = ord('a') - ord('A')
    for (base1, base2) in cmap:
        _ctable[base1] = chr(base2)
        _ctable[base2] = chr(base1)
        _ctable[base1 + case_delta] = chr(base2 + case_delta)
        _ctable[base2 + case_delta] = chr(base1 + case_delta)
    return str.join('', _ctable)
ComplimentTable = build_compliment_table()

class ScoreMatrix(object):
    def __init__(self, alphabet=None, match=2, mismatch=-2):
        self._match = match
        self._mismatch = mismatch
        self.alphabet = alphabet

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
        self._alphabet = tuple(alphabet) if alphabet else tuple()
        self.symbol_map = {symbol.upper(): idx for (idx, symbol) in enumerate(self._alphabet)}
        self._init_matrix()
    alphabet = property(get_alphabet, set_alphabet)

    def _init_matrix(self):
        _matrix_type = libssw.matrix_type * (len(self.alphabet) ** 2)
        self._matrix = _matrix_type(*self.iter_matrix())

    def iter_matrix(self):
        for row_symbol in self.alphabet:
            for col_symbol in self.alphabet:
                yield self._get_score(row_symbol, col_symbol)

    def _get_score(self, symbol_1, symbol_2):
        if symbol_1.upper() == symbol_2.upper(): return self.match
        return self.mismatch

    def convert_sequence_to_ints(self, seq):
        _seq_type = libssw.symbol_type * len(seq)
        seq_generator = (self.symbol_map[symbol.upper()] for symbol in seq)
        return _seq_type(*seq_generator)

class DNA_Matrix(ScoreMatrix):
    def __init__(self, alphabet='AGTCN', **kw):
        super(DNA_Matrix, self).__init__(alphabet=alphabet, **kw)

    def _get_score(self, symbol_1, symbol_2):
        if symbol_1.upper() == 'N' or symbol_2.upper() == 'N':
            return 0
        return super(DNA_Matrix, self)._get_score(symbol_1, symbol_2)

class Aligner(object):
    def __init__(self, reference=None, matrix=None, molecule="dna", gap_open=3, gap_extend=1):
        self.reference = reference
        self.matrix = matrix
        self.molecule = molecule
        if self.matrix == None and molecule != None:
            if molecule == "dna":
                self.matrix = DNA_Matrix()
            else:
                raise ValueError, "Unrecognized molecule type '%s'" % molecule
        self.gap_open = gap_open
        self.gap_extend = gap_extend

    def align(self, query='', reference=None, revcomp=True):
        # XXX: I really don't find this part of SSW useful, which
        # is why i broke alignment into two stages, so you can use 
        # the low level interface if you wish.
        filter_score = 0
        filter_distance = 0
        flags = 1
        mask_length = max(15, len(query) / 2)
        reference = reference if reference != None else self.reference
        res = self._align(query, reference, flags, filter_score, filter_distance, mask_length)
        if revcomp:
            query_rc = query[::-1].translate(ComplimentTable)
            res_rc = self._align(query_rc, reference, flags, filter_score, filter_distance, mask_length)
            if res_rc.score > res.score:
                res = res_rc
        return res
    
    def _align(self, query, reference, flags, filter_score, filter_distance, mask_length, score_size=2): 
        _query = self.matrix.convert_sequence_to_ints(query)
        _reference = self.matrix.convert_sequence_to_ints(reference)
        profile = libssw.ssw_profile_init(_query, len(query), self.matrix._matrix, len(self.matrix.alphabet), score_size)
        alignment = libssw.ssw_align_init(profile, _reference, len(_reference), self.gap_open, self.gap_extend, flags, filter_score, filter_distance, mask_length) 
        alignment_instance = Alignment(alignment, query, reference)
        libssw.ssw_profile_del(profile)
        libssw.ssw_align_del(alignment)
        return alignment_instance

class Alignment(object):
    def __init__ (self, alignment, query, reference):
        self.score = alignment.contents.score
        self.score2 = alignment.contents.score2
        self.reference = reference
        self.reference_begin = alignment.contents.ref_begin
        self.reference_end = alignment.contents.ref_end
        self.query = query
        self.query_begin = alignment.contents.query_begin
        self.query_end = alignment.contents.query_end
        self._cigar_string = [alignment.contents.cigar[idx] for idx in range(alignment.contents.cigarLen)]

    @property
    def iter_cigar(self):
        for val in self._cigar_string:
            op_len = libssw.cigar_int_to_len(val)
            op_char = libssw.cigar_int_to_op(val)
            yield (op_len, op_char)

    @property
    def cigar(self):
        cigar = ""
        if self.query_begin > 0:
            cigar += str(self.query_begin) + "S"
        cigar += str.join('', [str.join('', map(str, cstr)) for cstr in self.iter_cigar])
        end_len = len(self.query) - self.query_end - 1
        if end_len != 0:
            cigar += str(end_len) + "S"
        return cigar

    @property
    def alignment(self):
        def seqiter(seq, start=None, end=None):
            seq = iter(seq[start:end])
            def getseq(cnt):
                return str.join('', (seq.next() for x in range(cnt)))
            return getseq
        r_seq = seqiter(self.reference, self.reference_begin, self.reference_end + 1)
        q_seq = seqiter(self.query, self.query_begin, self.query_end + 1)
        r_line = m_line = q_line = ''
        for (op_len, op_char) in self.iter_cigar:
            op_len = int(op_len)
            if op_char.upper() == 'M':
                for (r_base, q_base) in zip(r_seq(op_len), q_seq(op_len)):
                    r_line += r_base
                    q_line += q_base
                    # XXX: ambiguity codes? matrix match?
                    if r_base.upper() == q_base.upper():
                        m_line += '|'
                    else:
                        m_line += '*'
            elif op_char.upper() == 'I':
                # insertion into reference
                r_line += '-' * op_len
                m_line += ' ' * op_len
                q_line += q_seq(op_len)
            elif op_char.upper() == 'D':
                # deletion from reference
                r_line += r_seq(op_len)
                m_line += ' ' * op_len
                q_line += '-' * op_len
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

    def alignment_report(self, width=80, header=True):
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
