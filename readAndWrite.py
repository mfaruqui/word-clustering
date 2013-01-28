import sys
from collections import Counter
from operator import itemgetter

def printClusters(outputFileName, en, de, fr):
    
    outFileEn = open(outputFileName+'.en', 'w')
    outFileDe = open(outputFileName+'.de', 'w')
    if fr != None:
        outFileFr = open(outputFileName+'.fr', 'w')
    
    #clusSimDict = {}
    #for ((clus1, wordListEn), (clus2, wordListFr)) in zip(en.wordsInClusDict.iteritems(), fr.wordsInClusDict.iteritems()):
    #    if enFr.common.alignedWordsInClusPairDict.has_key((clus1, clus2)):
    #        clusSimDict[(clus1, clus2)] = 1.0*len(enFr.common.alignedWordsInClusPairDict[(clus1, clus2)])/(len(wordListEn)+len(wordListFr))
    #    else:
    #        clusSimDict[(clus1, clus2)] = 0.0
    #    
    #for (clus1, clus2), val in sorted(clusSimDict.items(), key=itemgetter(1), reverse=True):
    
    for clus in sorted(en.wordsInClusDict.keys()):
        
        wordListEn = en.wordsInClusDict[clus]
        wordListDe = de.wordsInClusDict[clus]
        if fr != None:
            wordListFr = fr.wordsInClusDict[clus]
        
        sortedEnDict = {}
        for word in wordListEn:
            sortedEnDict[word] = en.wordDict[word]
        
        sortedEnList = []    
        for (word, val) in sorted(sortedEnDict.items(), key = itemgetter(1), reverse = True):
            sortedEnList.append(word)
            
        sortedDeDict = {}
        for word in wordListDe:
            sortedDeDict[word] = de.wordDict[word]
        
        sortedDeList = []    
        for (word, val) in sorted(sortedDeDict.items(), key = itemgetter(1), reverse = True):
            sortedDeList.append(word)
         
        if fr != None:
            sortedFrDict = {}
            for word in wordListFr:
                sortedFrDict[word] = fr.wordDict[word]
        
            sortedFrList = []    
            for (word, val) in sorted(sortedFrDict.items(), key = itemgetter(1), reverse = True):
                sortedFrList.append(word)
        
        for word in sortedEnList:
            outFileEn.write(word+'\t'+str(clus)+'\n')
            
        for word in sortedDeList:
            outFileDe.write(word+'\t'+str(clus)+'\n')
            
        if fr != None:
            for word in sortedFrList:
                outFileFr.write(word+'\t'+str(clus)+'\n')
                    
    outFileEn.close()
    outFileDe.close()
    if fr != None:
        outFileFr.close()

def readBilingualData(fileLength, bilingualFileName, alignFileName, mono1FileName, mono2FileName,\
                     enWordDict, enBigramDict, frWordDict, frBigramDict):
    
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
                frWordDict[word] += 1.0
                if prevWord != '':
                    frBigramDict[(prevWord, word)] += 1.0
                prevWord = word
                
        sys.stderr.write(' Complete!\n')

    return alignDict, enWordDict, enBigramDict, frWordDict, frBigramDict