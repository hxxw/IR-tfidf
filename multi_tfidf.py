#-------------------------------------------------------------------------------
# Title: Document Search by TF-IDF ranking
#
# Description:
#  - Term Frequency (TF) is computed using map and filter.
#  - Document Frequency (DF) is computed using map and reduce.
#  - Query parsing is based on a non-functional programming fashion.
#  - TF-IDF is computed using map and reduce.

import os,math,re,time,multiprocessing,itertools,argparse,sys
from collections import defaultdict
import operator
from pyparsing import *

#-----------------------------
# Term Frequency
#-----------------------------
# Wrapper for handling multi arguments
# Reference: http://stackoverflow.com/questions/5442910/python-multiprocessing-pool-map-for-multiple-arguments
def wrap_getTF(a_b_c):
    return getTF(*a_b_c)

# TF calculation for the given document. Log-normalisation is applied for TF.
# Doc -> Words
def getTF(doc,max_w_length,stopwords):
    term_id=0
    tf=defaultdict(float)
    map_term_id=defaultdict(int)
    map_id_term=defaultdict(str)

    wfreq=defaultdict(int)
    with open(doc,'r') as f:
        for line in f:
            if len(line.strip()) > 0:
                list_terms=filter(lambda x: (1 < len(x) <= max_w_length) and (x not in stopwords), word_clean(re.split(r'\s+', line)))
                for w in list_terms:
                    if not w in map_term_id.keys():
                        map_term_id[w]=term_id
                        map_id_term[term_id]=w
                    wfreq[map_term_id[w]]+=1
                    term_id+=1
    for k in set(wfreq.keys()):
        # Term Frequency: 1 + log(tf)
        tf[map_id_term[k]]=1+math.log(wfreq[k],2)
    return (doc,tf)

# Word Cleaning
def word_clean(words):
    return map(lambda x: x.lower(), map(lambda x: re.sub("([^a-zA-Z]+$|^[^a-zA-Z]+)", "", x), words))

#-----------------------------
# Document Frequency
#-----------------------------
def addto(d,l):
    for (x,y) in l:
        d[y].append(x)
    return d

def get_tf_dic(pair_doc_tf):
    dic_ft=defaultdict(dict)
    for (d,tf) in pair_doc_tf:
        dic_ft[d]=tf
    return dic_ft

#-----------------------------
# Query Parsing
#-----------------------------
#Classes for Query Parsing
class Unary(object):
    def __init__(self, t):
        self.op, self.a = t[0]
class Binary(object):
    def __init__(self, t):
        self.op = t[0][1]
        self.operands = t[0][0::2]
class SearchAnd(Binary):
    def generateSetExpression(self,docFreq):
        return "(%s)" % " & ".join(oper.generateSetExpression(docFreq) for oper in self.operands)
    def __repr__(self):
        return "AND:(%s)" % (",".join(str(oper) for oper in self.operands))
class SearchOr(Binary):
    def generateSetExpression(self,docFreq):
        return "(%s)" % " | ".join(oper.generateSetExpression(docFreq) for oper in self.operands)
    def __repr__(self):
        return "OR:(%s)" % (",".join(str(oper) for oper in self.operands))
class SearchNot(Unary):
    def generateSetExpression(self,docFreq):
        return "(set(recipes) - %s)" % self.a.generateSetExpression(docFreq)   
    def __repr__(self):
        return "NOT:(%s)" % str(self.a)
class SearchTerm(object):
    def __init__(self, tokens):
        self.term = tokens[0]
    def __repr__(self):
        return self.term
    def generateSetExpression(self,docFreq):
        if self.term in docFreq:
            return "set(docFreq['%s'])" % self.term
        else:
            return "set()"

def query_parsing(path_query):
    # define the grammar
    and_=CaselessLiteral("and")
    or_=CaselessLiteral("or")
    not_=CaselessLiteral("not")
    searchTerm=Word(alphas) | quotedString.setParseAction(removeQuotes)
    searchTerm.setParseAction(SearchTerm)
    searchExpr=operatorPrecedence(searchTerm,
                                     [
                                         (not_, 1, opAssoc.RIGHT, SearchNot),
                                         (or_, 2, opAssoc.LEFT, SearchOr),                                     
                                         (Optional(and_,default="and"), 2, opAssoc.LEFT,SearchAnd),
                                         #(and_, 2, opAssoc.LEFT, SearchAnd),
                                     ])

    test_query=list()
    try:
        with open(path_query,'rb') as f:
            for line in f:
                if len(line.strip()) > 0:
                    test_query.append(line.strip())
    except:
        print 'cannot find the query file. Use the default query:', test_query
        pass
    
    return (test_query,searchExpr)

#-----------------------------
# Search, TF-IDF, and Ranking
#-----------------------------
def query(tf,docFreq,pathquery):

    # parsing the given queries
    (list_queries,searchExpr)=query_parsing(pathquery)

    # searching queries
    for t in list_queries:
        #
        # Parse the given query
        #
        print "-----------------"
        print "Search Query:", t
        try:
            evalStack = (searchExpr+stringEnd).parseString(t)[0]
        except ParseException, pe:
            print "Invalid search string", t
            continue

        #
        # Search Documents
        #
        evalExpr = evalStack.generateSetExpression(docFreq)
        list_terms=evalExpr.split("'")[1::2]
        print "Search Query Logic:", evalExpr
        print "Search Terms:", list_terms
        
        start = time.time()
        matched_docs = eval(evalExpr)
        if not matched_docs:
             print " (none)"
        elapsed_time=time.time()-start
        print 'Search Result: Found',len(matched_docs),'documents in', ("elapsed_time:{0}".format(elapsed_time)),'[sec]'

        print "\nSearch Result Ranking (document name, score)"
        matched_doc_freq=defaultdict(list)
        start = time.time()

        #
        # Document Frequency
        #
        # Calculating Doc Freq for each query term. The intersection of the logically
        # matched docs and the pre-computed ground document frequency is computed using 'set' intersection.
        for t in set(list_terms):
            matched_doc_freq[t]=list(set(docFreq[t]).intersection(matched_docs))
            
        #
        # Scoring Algorithm: Accumulate TF-IDF scores for given query terms
        #
        scores=defaultdict(float)
        for doc in matched_docs:
            scores[doc]=reduce(lambda sum,x: sum + tf[doc][x] * math.log(1.0+1.0*(len(matched_docs))/(len(matched_doc_freq[x])+1),2),set(list_terms),0)

        #
        # Top 10 Documents
        #
        sorted_tfidf = sorted(scores.items(), key=operator.itemgetter(1),reverse=True)
        for (doc_id,s) in sorted_tfidf[:10]:
            print doc_id+'\t'+str(s)
            
        elapsed_time = time.time() - start
        print ("Searched in:{0}".format(elapsed_time)) + "[sec]"

#-----------------------------
# Main
#-----------------------------
if __name__ == "__main__":

    #(Step1) User Input
    parser = argparse.ArgumentParser(description='Example: python multi_tfidf.py 20_newsgroups -max 15 -q query1.txt')
    parser.add_argument('path_data_file',type=str,action='store',help='Path to data file')
    parser.add_argument('-max','--word_length',nargs='?',default=15,const=15,type=int,action='store',help='Max Word Length')
    parser.add_argument('-q','--path_queries',nargs='?',default='query1.txt',const='query1.txt',type=str,action='store',help='Path to query file')
    
    args = parser.parse_args(sys.argv[1:])
    data_path=args.path_data_file
    max_word=args.word_length
    path_query=args.path_queries

    #(Step2) Read Doc Path
    files=map(lambda x: zip([x[0]]*len(x[2]),x[2]), os.walk(data_path))
    files=[y for x in files for y in x]
    path_docs=map(lambda x: [os.path.join(x[0],x[1])][0] if len(x)==2 else None,files)
    
    #(Step3) Term Frequency by multiprocessing
    stops=[]
    pool=multiprocessing.Pool(processes=50)
    DOC_TF=pool.map(wrap_getTF,itertools.izip(path_docs,itertools.repeat(max_word),itertools.repeat(stops)))
    
    #(Step4) Document Frequency
    DOC_Term=map(lambda x: zip([x[0]]*len(x[1]),x[1]),DOC_TF)
    document_freq=defaultdict(list)
    document_freq=reduce(addto,DOC_Term,document_freq)

    #(Step5) Making query and computing TF-IDF per query
    query(get_tf_dic(DOC_TF),document_freq,path_query)
