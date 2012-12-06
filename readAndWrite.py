import sys
from collections import Counter
from operator import itemgetter

def printClusters(outputFileName, en, fr, enFr):
    
    outFileEn = open(outputFileName+'.en', 'w')
    outFileFr = open(outputFileName+'.fr', 'w')
    
    clusSimDict = {}
    for ((clus1, wordListEn), (clus2, wordListFr)) in zip(en.wordsInClusDict.iteritems(), fr.wordsInClusDict.iteritems()):
        if enFr.common.alignedWordsInClusPairDict.has_key((clus1, clus2)):
            clusSimDict[(clus1, clus2)] = 1.0*len(enFr.common.alignedWordsInClusPairDict[(clus1, clus2)])/(len(wordListEn)*len(wordListFr))
        else:
            clusSimDict[(clus1, clus2)] = 0.0
        
    for (clus1, clus2), val in sorted(clusSimDict.items(), key=itemgetter(1), reverse=True):
        
        wordListEn = en.wordsInClusDict[clus1]
        wordListFr = fr.wordsInClusDict[clus2]
        
        sortedEnDict = {}
        for word in wordListEn:
            sortedEnDict[word] = en.wordDict[word]
        
        sortedEnList = []    
        for (word, val) in sorted(sortedEnDict.items(), key = itemgetter(1), reverse = True):
            sortedEnList.append(word)
            
        sortedFrDict = {}
        for word in wordListFr:
            sortedFrDict[word] = fr.wordDict[word]
        
        sortedFrList = []    
        for (word, val) in sorted(sortedFrDict.items(), key = itemgetter(1), reverse = True):
            sortedFrList.append(word)
        
        outFileEn.write(str(clus1)+' ||| ')       
        for word in sortedEnList:
            outFileEn.write(word+' ')
        outFileEn.write('\n')
        
        outFileFr.write(str(clus2)+' ||| ')       
        for word in sortedFrList:
            outFileFr.write(word+' ')
        outFileFr.write('\n')
        
    outFileEn.close()
    outFileFr.close()

def readBilingualData(fileLength, bilingualFileName, alignFileName, mono1FileName, mono2FileName):
    
    enWordDict = Counter()
    enBigramDict = Counter()
    frWordDict = Counter()
    frBigramDict = Counter()
    alignDict = Counter()
    sys.stderr.write('\nReading parallel and alignment file...')
    
    lineNum = 0
    
    for wordLine, alignLine in zip(open(bilingualFileName,'r'), open(alignFileName, 'r')):
        
        lineNum += 1
        
        if lineNum > fileLength:
            break
        
        en, fr = wordLine.split('|||')
        en = en.strip()
        fr = fr.strip()
        
        enWords = en.split()
        prevWord = ''
        for word in enWords:
            word = word
            enWordDict[word] += 1.0
            if prevWord != '':
                enBigramDict[(prevWord, word)] += 1.0
            prevWord = word
        
        frWords = fr.split()   
        prevWord = ''
        for word in frWords:
            word = word
            frWordDict[word] += 1.0
            if prevWord != '':
                frBigramDict[(prevWord, word)] += 1.0
            prevWord = word
            
        for alignments in alignLine.split():
            en, fr = alignments.split('-')
            enWord = enWords[int(en)]
            frWord = frWords[int(fr)]
            alignDict[(enWord, frWord)] += 1.0
            
    sys.stderr.write(' Complete!\n')
            
    if mono1FileName != '':
        sys.stderr.write("\nReading monolingual file of L1...")        
        for line in open(mono1FileName, 'r'):
            line = line.strip()
            for word in line.split():
                #word = "e|||"+word
                enWordDict[word] += 1.0
                if prevWord != '':
                    enBigramDict[(prevWord, word)] += 1.0
                prevWord = word
                
        sys.stderr.write(' Complete!\n')
                
    if mono2FileName != '':
        sys.stderr.write("\nReading monolingual file of L2...")    
        for line in open(mono2FileName, 'r'):
            line = line.strip()
            for word in line.split():
                #word = "f|||"+word
                frWordDict[word] += 1.0
                if prevWord != '':
                    frBigramDict[(prevWord, word)] += 1.0
                prevWord = word
                
        sys.stderr.write(' Complete!\n')

    # Filtering out alignment pairs by their counts
    #threshCount = 3
    #alignDictEnFr = {key:value for (key, value) in alignDictEnFr.iteritems() if value >= threshCount}
    #alignDictFrEn = {key:value for (key, value) in alignDictFrEn.iteritems() if value >= threshCount}
           
    return alignDict, enWordDict, enBigramDict, frWordDict, frBigramDict