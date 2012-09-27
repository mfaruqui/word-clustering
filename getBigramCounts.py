import sys
from operator import itemgetter

wordDict = {}
bigramDict = {}

prevWord = ''
for line in sys.stdin:
        line = line.strip()
        fr, en = line.split('|||')

        words = en.split()
        
        for word in words:
            if word != '':
                try:
                        wordDict[word] += 1
                except:
                        wordDict[word] = 1

            if prevWord != '' and word != '':
                try:
                    bigramDict[(prevWord, word)] += 1
                except:
                    bigramDict[(prevWord, word)] = 1
            
            prevWord = word
            
for word, val in sorted(wordDict.iteritems(), key=itemgetter(1), reverse=True): 
    print word, val
            
for key, val in sorted(bigramDict.iteritems(), key=itemgetter(1), reverse=True): 
    w1, w2 = key
    print w1, w2, val