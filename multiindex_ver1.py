#-------------------------------------------------------------------------------
# Title: Term Frequency by Map  
#
# Description:
#  Term Frequency (TF) is computed using 'multiprocessing' library
#  for (1) realising 'speed-up' and (2) demonstrating the usage of 'map' function.
#  The resulted model is exported into a pickle file.

import os,math,re,time,multiprocessing,itertools,pickle,argparse,sys
from collections import defaultdict

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
def main(data_path,max_word,out_file):
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
    
    #
    #Step4: Save as pickle fild
    #
    with open(out_file,'wb') as f:
        pickle.dump((tf_fin,doc_freq,map_id_doc),f)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Example: python multiindex_ver1.py 20_newsgroups -max 15 -o index.dump')
    parser.add_argument('-i','--path_data_file',nargs='?',default='20_newsgroups',const='20_newsgroups',type=str,action='store',help='Path to data file')
    parser.add_argument('-max','--word_length',nargs='?',default=15,const=15,type=int,action='store',help='Max Word Length')
    parser.add_argument('-o','--output_file',nargs='?',default='index.dump',const='index.dump',type=str,action='store',help='Output file in pickle')
    
    args = parser.parse_args(sys.argv[1:])
    data_path=args.path_data_file
    max_word=args.word_length
    out_file=args.output_file

    main(data_path,max_word,out_file)
