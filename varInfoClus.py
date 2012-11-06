import sys
from math import log

f1 = sys.argv[1]
f2 = sys.argv[2]

clusDict1 = {}
vocabLen1 = 0
for line in open(f1, 'r'):
    line = line.strip()
    things = line.split('|||')
    
    clusNum = things[0]
    words = things[1:]
    
    clusDict1[clusNum] = words
    vocabLen1 += len(words)
    
clusDict2 = {}
vocabLen2 = 0
for line in open(f2, 'r'):
    line = line.strip()
    things = line.split('|||')
    
    clusNum = things[0]
    words = things[1:]
    
    clusDict2[clusNum] = words
    vocabLen2 += len(words)
    
if vocabLen1 != vocabLen2:
    print 'Dissimilar word collection'
    print vocabLen1, vocabLen2
    print 'Making vocabulory same'
    wordsLost = 0
    v1 = []
    v2 = []
    for clus, wL in clusDict1.iteritems():
	v1 += wL
    for clus, wL in clusDict2.iteritems():
	v2 += wL

    for clus, wL in clusDict1.iteritems():
	for word in set(v1) - set(v2):
		if word in wL:
			clusDict1[clus].remove(word)
			wordsLost += 1
    for clus, wL in clusDict2.iteritems():
	for word in set(v2) - set(v1):
		if word in wL:
			clusDict2[clus].remove(word)
			wordsLost += 1

    print "Words lost:", wordsLost

# VI(C, C') = H(C) + H(C') - 2*I(C, C')
# H(C) = Sum over all k(clusters), P(k) log P(K)
# I(C, C') = Sum over all K ( (Sum over all K')  P(K, K') * log( P(K, K') / ( P(K)*P(K') ) )
# P(K) = n_k / n , where n_k <- no. words in clus k, n <- no. of words in vocab

h1 = 0.0
for key in clusDict1.keys():
    p = 1.0*len(clusDict1[key]) / vocabLen1
    if p != 0:
        h1 += p * log(p)
        
h1 = -1*h1
        
h2 = 0.0
for key in clusDict2.keys():
    p = 1.0*len(clusDict2[key]) / vocabLen2
    if p != 0:
        h2 += p * log(p)
        
h2 = -1*h2
        
i = 0.0
for key1 in clusDict1.keys():
    pk1 = 1.0 * len(clusDict1[key1]) / vocabLen1
    for key2 in clusDict2.keys():
        common = 1.0 * len(list(set(clusDict1[key1]) & set(clusDict2[key2])))
        if common != 0:
            pk1k2 = common/vocabLen1
            pk2 = 1.0 * len(clusDict2[key2]) / vocabLen2
            i += pk1k2 * log( pk1k2 / (pk1 * pk2) )
            
vi = h1 + h2 - 2 * i
print vi
