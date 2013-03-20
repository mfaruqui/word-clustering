import sys
from collections import Counter
from operator import itemgetter

def printClusters(outputFileName, en, de, fr=None, fourth=None, fifth=None):
    
    outFileEn = open(outputFileName+'.en', 'w')
    outFileDe = open(outputFileName+'.de', 'w')
    if fr != None:
        outFileFr = open(outputFileName+'.fr', 'w')
    if fourth != None:
        outFileFourth = open(outputFileName+'.fourth', 'w')
    if fifth != None:
        outFileFifth = open(outputFileName+'.fifth', 'w')
    
    for clus in sorted(en.wordsInClusDict.keys()):
        
        wordListEn = en.wordsInClusDict[clus]
        wordListDe = de.wordsInClusDict[clus]
        if fr != None:
            wordListFr = fr.wordsInClusDict[clus]
        if fourth != None:
            wordListFourth = fourth.wordsInClusDict[clus]
        if fifth != None:
            wordListFifth = fifth.wordsInClusDict[clus]
        
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
                
        if fourth != None:
            sortedFourthDict = {}
            for word in wordListFourth:
                sortedFourthDict[word] = fourth.wordDict[word]
        
            sortedFourthList = []    
            for (word, val) in sorted(sortedFourthDict.items(), key = itemgetter(1), reverse = True):
                sortedFourthList.append(word)
                
        if fifth != None:
            sortedFifthDict = {}
            for word in wordListFifth:
                sortedFifthDict[word] = fifth.wordDict[word]
        
            sortedFifthList = []    
            for (word, val) in sorted(sortedFifthDict.items(), key = itemgetter(1), reverse = True):
                sortedFifthList.append(word)
        
        for word in sortedEnList:
            outFileEn.write(word+'\t'+str(clus)+'\n')
            
        for word in sortedDeList:
            outFileDe.write(word+'\t'+str(clus)+'\n')
            
        if fr != None:
            for word in sortedFrList:
                outFileFr.write(word+'\t'+str(clus)+'\n')
        
        if fourth != None:
            for word in sortedFourthList:
                outFileFourth.write(word+'\t'+str(clus)+'\n')
                
        if fifth != None:
            for word in sortedFifthList:
                outFileFifth.write(word+'\t'+str(clus)+'\n')
                    
    outFileEn.close()
    outFileDe.close()
    if fr != None:
        outFileFr.close()
    if fourth != None:
        outFileFourth.close()
    if fifth != None:
        outFileFifth.close()

def readBilingualData(fileLength, bilingualFileName, alignFileName, mono1FileName, mono2FileName,\
                     enWordDict, enBigramDict, frWordDict, frBigramDict):
    
    alignDict = Counter()
    
    sys.stderr.write('\nReading parallel and alignment file...')
    
    lineNum = 0
    errorLines = 0
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
	    try:
              enWord = enWords[int(en)]
              frWord = frWords[int(fr)]
              alignDict[(enWord, frWord)] += 1.0
        except:
              pass
	          errorLines += 1
            
    sys.stderr.write(' Completed with '+str(errorLines)+' erroneous lines!\n')
            
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

def readMonoFile(inputFileName):
    
    wordDict = {}
    bigramDict = {}
    
    sys.stderr.write('\nReading input file...')
    
    for en in open(inputFileName,'r'):
        
        en = en.strip()
        enWords = en.split()
        
        prevWord = ''
        for word in enWords:
            
            if word in wordDict:
                wordDict[word] += 1.0
            else:
                wordDict[word] = 1.0

            if prevWord != '':
                if (prevWord, word) in bigramDict:
                    bigramDict[(prevWord, word)] += 1.0
                else:
                    bigramDict[(prevWord, word)] = 1.0
            prevWord = word
     
    sys.stderr.write('  Complete!\n')
    return wordDict, bigramDict
    
def readWordAlignments(inputFileName):
    
    sys.stderr.wrtie('\nReading alignment File...')
    alignDict = Counter()
    for line in open(inputFileName, 'r'):
        enWord, frWord = line.strip().split()
        alignDict[(enWord, frWord)] += 1
        
    sys.stderr.write(' Complete!\n')
    return alignDict