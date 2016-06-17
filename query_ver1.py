#
# Title: Query handling from a picle dump file.
#
# 

import os,math,re,operator,time,pickle,argparse,sys
from collections import defaultdict
from datetime import datetime
from pyparsing import *

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

    parser = argparse.ArgumentParser(description='Generating search queries for texts.')
    parser.add_argument('path_pickle_file',type=str,action='store',help='Path to pickle dump file')
    parser.add_argument('-q','--path_queries',nargs='?',default='query1.txt',const='query1.txt',type=str,action='store',help='Path to query file')
    
    #read user inputs 
    args = parser.parse_args(sys.argv[1:])
    path_pickle=args.path_pickle_file
    path_query=args.path_queries
    
    #load pickle file
    g=file(path_pickle,'r')
    (tf0,docFreq0,map_id_doc0)=pickle.load(g)

    #making query
    query(tf0,docFreq0,map_id_doc0,path_query)
