# IR-tfidf

A Multiprocessing Information Retrieval System from Texts in Python

## Getting Started

```
python multi_tfidf.py 20_newsgroup -max 15 -q query1.txt
```

## Requirement

multiprocess library can be installed with pip or easy_install:
```
$ pip install multiprocess
```

## Overview

A TF-IDF based ranking algorithm finds top 10 documents from given large collection of text files in the following steps.

1. Mapping text files into multi-processes to calculate Term Frequency (TF) per text file.
2. Computing Document Frequency (DF) per term based on the given entire text files.
3. Parsing user queries and find associated text files.
4. For each query, reducing the TF-IDF score by accumulating the TF-IDF values among search terms.
5. Getting top 10 documents based on the reduced TF-IDF score.

## Algorithm

### Step 1

Mapping text files into 50 multi-processes in order to calculate Term Frequency per text file. Word cleaning is performed to reduce the number of terms. The mapping is done in a functional programming fashion.

```python
def multi_tf(doclist,max_word_length):
    pool = multiprocessing.Pool(processes=50)
    stops=[]
    return pool.map(wrap_getTF,itertools.izip(doclist,itertools.repeat(max_word_length),itertools.repeat(stops)))
```

During the TF calculation, words are filtered by applying stop-words and word-length conditions.

```python
list_terms=filter(lambda x: (1 < len(x) <= max_w_length) and (x not in stopwords), word_clean(re.split(r'\s+', line)))
```

Term-Frequency is log-normalised as follows.
```python
tf[map_id_term[k]]=1+math.log(wfreq[k],2)
```
### Step 2

Document Frequency (DF) is computed for each valid term using all the given data in this step. The motivation is to separate the two tasks: document search and TF-IDF calculation.

The algorithm is explained using the "science" OR "religion" query.

- DF['science'] = ['d1','d2','d3']
- DF('religion') = ['d11','d12']

The query, "science" OR "religion", finds the associated documents:
- ['d1','d2','d3','d11','d12']

To compute TF-IDF for 'science' we take the set intersection operation between set(['d1','d2','d3']) \intersect set(['d1','d2','d3','d11','d12'])

This looks redundant, however, applying further filtering (ex. temporal filtering) over ['d1','d2','d3','d11','d12'] may be efficiently realised.

### Step 3

Query parsing was implemented by referring the pyparsing textbook (http://shop.oreilly.com/product/9780596514235.do).

### Step 4

TF-IDF-base scoring function is implemented by accumulating TF-IDF values for search terms in a functional programming fashion.

```python
for doc in matched_docs:
	scores[doc]=reduce(lambda sum,x: sum + tf[map_id_doc[doc]][x] * math.log(1.0+1.0*(len(matched_docs))/(len(matched_doc_freq[x])+1),2),set(list_terms),0)
```
Note that Inverse DF is defined with 'smoothing'.

```python
math.log(1.0+1.0*(len(matched_docs))/(len(matched_doc_freq[x])+1),2)
```
### Step 5

Top 10 documents are shown based on the accumulated TF-IDF scores.

## Future Work

- Applying further filtering (ex. temporal filtering) can be implemented by extracting further informatin from documents.
- A multi-processing versino of MapReduce is implemented on a single machine. Mapping the data into clusters can be realised by replacing the multiprosses part.
- Exporting indexed result to local file is sometimes useful. We developed this idea by using 'pickle' dump model (multiindex_ver1.py and query_ver1.py in the git). Since exporting/loading model is slow, we did not report the details.
- TF-IDF is not suited for CSV files. Z-score is an alternative measure for finding uncommonly common keywords. Depending on the data set, but we often observe the document frequency per term can be estimated in Normal distribution.




## Example
```
python multi_tfidf.py 20_newsgroup -max 15 -q query1.txt
```
where
```
'20_newsgroup'
```
is the path to your data,
```
-max 15 
```
is the max length of word to be processed, and
```
-q query1.txt
```
is the path to your query file.

Top10 ranking is shown for each query.

```
$ python multi_tfidf.py 20_newsgroups -max 15 -q query1.txt
file size: 19997
Indexing Done. Processed 19997 files. elapsed_time:37.9550001621 [sec]
DF Done. elapsed_time:2.60599994659 [sec]

-----------------

Search Query:     "science" OR "religion"
Search Query Logic: (set(docFreq['science']) | set(docFreq['religion']))
Search Terms: ['science', 'religion']
Search Result: Found 2143 documents in elapsed_time:0.0 [sec]

Search Result Ranking (document name, score)
20_newsgroups\alt.atheism\51060,        16.0583847685
20_newsgroups\alt.atheism\52499,        14.0917466264
20_newsgroups\alt.atheism\53429,        12.9665890919
20_newsgroups\alt.atheism\53404,        12.2400397811
20_newsgroups\alt.atheism\53545,        11.8648852919
20_newsgroups\talk.religion.misc\83908, 11.8648852919
20_newsgroups\talk.religion.misc\84323, 11.7300890362
20_newsgroups\alt.atheism\53340,        11.4521927307
20_newsgroups\alt.atheism\53567,        10.5989503169
20_newsgroups\talk.religion.misc\83925, 10.5989503169
Searched in:0.0160000324249[sec]

-----------------

Search Query:     "science" AND "religion"
Search Query Logic: (set(docFreq['science']) & set(docFreq['religion']))
Search Terms: ['science', 'religion']
Search Result: Found 114 documents in elapsed_time:0.0 [sec]

Search Result Ranking (document name, score)
20_newsgroups\alt.atheism\51060,        9.01975634839
20_newsgroups\alt.atheism\52499,        7.94970989722
20_newsgroups\talk.religion.misc\84323, 7.70613824097
20_newsgroups\alt.atheism\53429,        7.41253967079
20_newsgroups\talk.religion.misc\83908, 7.12485296829
20_newsgroups\alt.atheism\53545,        7.12485296829
20_newsgroups\alt.atheism\53404,        6.65831899288
20_newsgroups\talk.religion.misc\84558, 6.5435676956
20_newsgroups\alt.atheism\53340,        6.28218679318
20_newsgroups\talk.religion.misc\83925, 6.28218679318
Searched in:0.0[sec]

-----------------

Search Query: "science" AND "religion"
Search Query Logic: (set(docFreq['science']) & set(docFreq['religion']))
Search Terms: ['science', 'religion']
Search Result: Found 114 documents in elapsed_time:0.0 [sec]

Search Result Ranking (document name, score)
20_newsgroups\alt.atheism\51060,        9.01975634839
20_newsgroups\alt.atheism\52499,        7.94970989722
20_newsgroups\talk.religion.misc\84323, 7.70613824097
20_newsgroups\alt.atheism\53429,        7.41253967079
20_newsgroups\talk.religion.misc\83908, 7.12485296829
20_newsgroups\alt.atheism\53545,        7.12485296829
20_newsgroups\alt.atheism\53404,        6.65831899288
20_newsgroups\talk.religion.misc\84558, 6.5435676956
20_newsgroups\alt.atheism\53340,        6.28218679318
20_newsgroups\talk.religion.misc\83925, 6.28218679318
Searched in:0.0[sec]

-----------------

Search Query: "science" OR "religion"
Search Query Logic: (set(docFreq['science']) | set(docFreq['religion']))
Search Terms: ['science', 'religion']
Search Result: Found 2143 documents in elapsed_time:0.0 [sec]

Search Result Ranking (document name, score)
20_newsgroups\alt.atheism\51060,        16.0583847685
20_newsgroups\alt.atheism\52499,        14.0917466264
20_newsgroups\alt.atheism\53429,        12.9665890919
20_newsgroups\alt.atheism\53404,        12.2400397811
20_newsgroups\alt.atheism\53545,        11.8648852919
20_newsgroups\talk.religion.misc\83908, 11.8648852919
20_newsgroups\talk.religion.misc\84323, 11.7300890362
20_newsgroups\alt.atheism\53340,        11.4521927307
20_newsgroups\alt.atheism\53567,        10.5989503169
20_newsgroups\talk.religion.misc\83925, 10.5989503169
Searched in:0.0350000858307[sec]

-----------------

Search Query: ("science" OR "religion") AND "book"
Search Query Logic: ((set(docFreq['science']) | set(docFreq['religion'])) & set(docFreq['book']))
Search Terms: ['science', 'religion', 'book']
Search Result: Found 183 documents in elapsed_time:0.0 [sec]

Search Result Ranking (document name, score)
20_newsgroups\alt.atheism\51060,        15.7946379128
20_newsgroups\alt.atheism\52499,        15.5795061954
20_newsgroups\talk.politics.mideast\76013,      11.6083718646
20_newsgroups\talk.religion.misc\84314, 11.099801697
20_newsgroups\alt.atheism\54256,        11.0376519479
20_newsgroups\sci.space\61244,  10.7361400352
20_newsgroups\talk.religion.misc\84449, 10.7361400352
20_newsgroups\alt.atheism\53497,        10.0763556017
20_newsgroups\talk.politics.mideast\76276,      9.60021899911
20_newsgroups\alt.atheism\49960,        9.52873041658
Searched in:0.0[sec]

-----------------

Search Query: "cancer" AND "food"
Search Query Logic: (set(docFreq['cancer']) & set(docFreq['food']))
Search Terms: ['cancer', 'food']
Search Result: Found 15 documents in elapsed_time:0.0 [sec]

Search Result Ranking (document name, score)
20_newsgroups\sci.med\59284,    10.2999917925
20_newsgroups\sci.med\59126,    8.65082885517
20_newsgroups\sci.med\59125,    6.80273555047
20_newsgroups\sci.med\59488,    5.88731967174
20_newsgroups\sci.med\58152,    5.72517786232
20_newsgroups\sci.med\59283,    4.93312336135
20_newsgroups\talk.politics.guns\55484, 4.37495430145
20_newsgroups\sci.med\58965,    3.42075799106
20_newsgroups\sci.med\58941,    3.42075799106
20_newsgroups\sci.med\59009,    3.42075799106
Searched in:0.0[sec]
```



## Authors
* **Hiroaki Watanabe** - *Initial work* - (https://github.com/hxxw/IR-TFIDF)
