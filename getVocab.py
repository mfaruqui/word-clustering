import sys
from operator import itemgetter

wordDict = {}

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

for word, val in sorted(wordDict.iteritems(), key=itemgetter(1), reverse=True):
    print word, val