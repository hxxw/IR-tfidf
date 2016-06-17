#-------------------------------------------------------------------------------
# Title: Term Frequency by Map  
#
# Description:
#  Term Frequency (TF) is computed using 'multiprocessing' library
#  for (1) realising 'speed-up' and (2) demonstrating the usage of 'map' function.

import os,math,re,time,multiprocessing,itertools,argparse,sys
from collections import defaultdict
import operator
from datetime import datetime
from pyparsing import *

# Map documents into multi-processes
def multi_tf(doclist,max_word_length):
    pool = multiprocessing.Pool(processes=50)
    stops=[]
    return pool.map(wrap_getTF,itertools.izip(doclist,itertools.repeat(max_word_length),itertools.repeat(stops)))

# Wrapper for handling multi arguments
# Reference: http://stackoverflow.com/questions/5442910/python-multiprocessing-pool-map-for-multiple-arguments
def wrap_getTF(a_b_c):
    return getTF(*a_b_c)

# TF calculation for the given document. Log-normalisation is applied for TF.
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

# Get File Pathes
def get_filepath(path):
    path_docs=list()
    for root, dirs, files in os.walk(path):
        for file in files:
            path_docs.append(os.path.join(root,file))
    return path_docs

# Document frequency (DF) per term
def get_docfreq(RED):
    #(Example: doc_freq['hello']=[file1,file2,...]).
    # Note: this DF is based on the entire data files. Since TF-IDF is computed for a given query,
    # we should make a subset of the [file1,file2,...] per query.

    doc_freq0=defaultdict(list)
    map_id_doc0=defaultdict(list)

    #Document Frequency per term
    for i,(doc,tf) in enumerate(RED):
        map_id_doc0[i]=doc
        for t in set(tf.keys()):
            doc_freq0[t].append(i) #i is the doc id    
    return (doc_freq0,map_id_doc0)

# Main
def multi(data_path,max_word):
    #
    #Step1: Get file path
    #
    path_docs=list()
    try:
        path_docs=get_filepath(data_path)
    except Except,e1:
        print 'cannot find the file path. exit.'
        sys.exit(1)
    print 'file size:', len(path_docs)

    #
    #Step2: Distribute TF task using multiprocess
    #
    LEN=len(path_docs)
    #LEN=2000
    start=time.time()
    #list of (doc,tf)
    INDEXED=multi_tf(path_docs[:LEN],max_word)
    doc_size=len(INDEXED)
    elapsed_time=time.time() - start
    print 'Indexing Done. Processed',doc_size,'files.',("elapsed_time:{0}".format(elapsed_time)),'[sec]'

    #
    #Step3: Compute Data Frequency from Term Frequency
    #
    start = time.time()
    #DF per term
    (doc_freq,map_id_doc)=get_docfreq(INDEXED)
    elapsed_time=time.time()-start
    print 'DF Done.',("elapsed_time:{0}".format(elapsed_time)),'[sec]'

    tf_fin=defaultdict(dict)
    for (doc,tf) in INDEXED:
        tf_fin[doc]=tf

    return (tf_fin,doc_freq,map_id_doc)


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

    # test the grammar and selection logic
    test_query='''
    "science" OR "religion"
    "science" AND "religion"'''.splitlines()

    try:
        with open(path_query,'r') as f:
            for line in f:
                test_query.append(line.strip())
    except:
        print 'cannot find the query file. Use the default query:', test_query
        pass
    
    return (test_query,searchExpr)
        
# Making query
def query(tf,docFreq,map_id_doc,pathquery):

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
            print "Invalid search string"
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
            scores[doc]=reduce(lambda sum,x: sum + tf[map_id_doc[doc]][x] * math.log(1.0+1.0*(len(matched_docs))/(len(matched_doc_freq[x])+1),2),set(list_terms),0)

        #
        # Top 10 Documents
        #
        sorted_tfidf = sorted(scores.items(), key=operator.itemgetter(1),reverse=True)
        for (doc_id,s) in sorted_tfidf[:10]:
            print map_id_doc[doc_id]+',\t'+str(s)
            
        elapsed_time = time.time() - start
        print ("Searched in:{0}".format(elapsed_time)) + "[sec]"

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Example: python multi_tfidf.py 20_newsgroups -max 15 -q query1.txt')
    parser.add_argument('path_data_file',type=str,action='store',help='Path to data file')
    parser.add_argument('-max','--word_length',nargs='?',default=15,const=15,type=int,action='store',help='Max Word Length')
    parser.add_argument('-q','--path_queries',nargs='?',default='query1.txt',const='query1.txt',type=str,action='store',help='Path to query file')
    
    args = parser.parse_args(sys.argv[1:])
    data_path=args.path_data_file
    max_word=args.word_length
    path_query=args.path_queries
    
    (tf,doc_freq,map_id_docs)=multi(data_path,max_word)

    #making query
    query(tf,doc_freq,map_id_docs,path_query)
