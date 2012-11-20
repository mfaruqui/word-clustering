# Type python ochClustering.py -h for information on how to use
import sys
from operator import itemgetter
from math import log
import argparse
from collections import Counter
import os

# Return the nlogn value if its already computed and stored in logValues
# else computes it, stores it and then returns it
logValues = {}    
def nlogn(x):
    if x == 0:
        return x
    else:
        if x in logValues:
            return logValues[x]
        else:
            logValues[x] = x * log(x)
            return logValues[x]
        
def getNextPrevWordDict(bigramDict):
    
    nextWordDict = {}
    prevWordDict = {}
    for (w1, w2) in bigramDict.iterkeys():
        if w1 in nextWordDict:
            if w2 in nextWordDict[w1]:
                pass
            else:
                nextWordDict[w1].append(w2)
        else:
            nextWordDict[w1] = [w2]
            
        if w2 in prevWordDict:
            if w1 in prevWordDict[w2]:
                pass
            else:
                prevWordDict[w2].append(w1)
        else:
            prevWordDict[w2] = [w1]
              
    return nextWordDict, prevWordDict

def readBilingualData(bilingualFileName, alignFileName, enWordToClusDict, frWordToClusDict):
    
    enWordDict = Counter()
    enBigramDict = Counter()
    frWordDict = Counter()
    frBigramDict = Counter()
    alignDict = Counter()
    sys.stderr.write('\nReading parallel and alignment file...\n')
    
    lineNum = 0
    enWordVocab = []
    frWordVocab = []
    
    for wordLine, alignLine in zip(open(bilingualFileName,'r'), open(alignFileName, 'r')):
        
        lineNum += 1
        
        if lineNum > fileLength:
            break
        
        en, fr = wordLine.split('|||')
        en = en.strip()
        fr = fr.strip()
        enWords = en.split()
        frWords = fr.split()
        
        prevWord = ''
        for word in enWords:
            if word in enWordToClusDict:
                enWordDict[word] += 1.0
                if prevWord != '':
                    enBigramDict[(prevWord, word)] += 1.0
                prevWord = word
            else:
                prevWord = ''
            if word not in enWordVocab:    
                enWordVocab.append(word)
            
        prevWord = ''
        for word in frWords:
            if word in frWordToClusDict:
                frWordDict[word] += 1.0
                if prevWord != '':
                    frBigramDict[(prevWord, word)] += 1.0
                prevWord = word
            else:
                prevWord = ''
            
            if word not in frWordVocab:
                frWordVocab.append(word)
            
        for alignments in alignLine.split():
            en, fr = alignments.split('-')
            enWord = enWords[int(en)]
            frWord = frWords[int(fr)]
            if enWord in enWordToClusDict and frWord in frWordToClusDict:
                alignDict[(enWord, frWord)] += 1.0
            
    enNextWordDict, enPrevWordDict = getNextPrevWordDict(enBigramDict)    
    frNextWordDict, frPrevWordDict = getNextPrevWordDict(frBigramDict)
    
    # Filtering out alignment pairs by their counts
    threshCount = 3
    alignDict = {key:value for (key, value) in alignDict.iteritems() if value >= threshCount}
           
    return alignDict, enWordDict, enBigramDict, enNextWordDict, enPrevWordDict, \
    frWordDict, frBigramDict, frNextWordDict, frPrevWordDict, enWordVocab, frWordVocab
    
def readPOSClusters(POSFileName):
    
    wordsInClusDict = {}
    wordToClusDict = {}
    
    for line in open(POSFileName, 'r'):
        line = line.strip()
        pos, allWords = line.split('|||')
        pos = pos.strip()
        
        for word in allWords.split():
            if pos in wordsInClusDict:
                wordsInClusDict[pos].append(word)
            else:
                wordsInClusDict[pos] = [word]
            
            wordToClusDict[word] = pos
            
    return wordToClusDict, wordsInClusDict
    
def getClusterCounts(wordToClusDict, wordsInClusDict, wordDict, bigramDict):
    
    # Get initial cluster unigram [n(C)] 
    clusUniCount = Counter()
    # Get initial bigram counts [n(C2,C1)]   
    clusBiCount = Counter()
    
    for word in wordDict.iterkeys():
        clusNum = wordToClusDict[word]
        clusUniCount[clusNum] += wordDict[word]
    
    for (w1, w2) in bigramDict.iterkeys():
        c1 = wordToClusDict[w1]
        c2 = wordToClusDict[w2]
        clusBiCount[(c1, c2)] += bigramDict[(w1, w2)]
            
    return clusUniCount, clusBiCount
    
def getAllAlignedWordsInClusPair(enWordToClusDict, frWordToClusDict):
    
    alignedWordsInClusPair = {}
    sumAlignedWordsInClusPair = Counter()#multiDimensionalDict(2, Counter)
    sys.stderr.write("\nMaking an word-alignment info dictionary of clusters...\n")
    
    for (w_en, w_fr) in alignDict.iterkeys():
        c_en = enWordToClusDict[w_en]
        c_fr = frWordToClusDict[w_fr]
        
        if (c_en, c_fr) in alignedWordsInClusPair:
            alignedWordsInClusPair[(c_en, c_fr)].append((w_en, w_fr))
        else:
            alignedWordsInClusPair[(c_en, c_fr)] = [(w_en, w_fr)]
            
        sumAlignedWordsInClusPair[(c_en, c_fr)] += alignDict[(w_en, w_fr)]
                            
    return alignedWordsInClusPair, sumAlignedWordsInClusPair
    
def getInitialEdgeInCluster(enWordsInClusDict, frWordsInClusDict):
    
    enEdgeSumInClus = Counter()
    frEdgeSumInClus = Counter()
    
    for c_en, enWordList in enWordsInClusDict.iteritems():
        for w_en in enWordList:
            if w_en in enToFrAlignedDict:
                for w_fr in enToFrAlignedDict[w_en]:
                    enEdgeSumInClus[c_en] += alignDict[(w_en, w_fr)]
                    
    for c_fr, frWordList in frWordsInClusDict.iteritems():
        for w_fr in frWordList:
            if w_fr in frToEnAlignedDict:
                for w_en in frToEnAlignedDict[w_fr]:
                    frEdgeSumInClus[c_fr] += alignDict[(w_en, w_fr)]
                    
    return enEdgeSumInClus, frEdgeSumInClus
    
def calcPerplexity(enWordToClusDict, frWordToClusDict, enWordsInClusDict, frWordsInClusDict,\
                   enWordDict, frWordDict, enUniCount, enBiCount, frUniCount, frBiCount):
    
    sum1 = 0
    sum2 = 0
    
    for (c1, c2), nC1C2 in enBiCount.iteritems():
        if nC1C2 != 0 and c1 != c2:
            sum1 += nlogn( nC1C2/sizeLang["en"] )
    
    for c, n in enUniCount.iteritems():
        if n != 0:
            sum2 += nlogn( n/sizeLang["en"] )
            
    for (c1, c2), nC1C2 in frBiCount.iteritems():
        if nC1C2 != 0 and c1 != c2:
            sum1 += nlogn( nC1C2/sizeLang["fr"] )
    
    for c, n in frUniCount.iteritems():
        if n != 0:
            sum2 += nlogn( n/sizeLang["fr"] )
            
    perplex = 2 * sum2 - sum1
    
    sumClusEntrop = 0.0
    for (c_en, c_fr), sumCountPair in sumAlignedWordsInClusPairDict.iteritems():
        pxy = sumCountPair/sumAllAlignLinks
        px = enEdgeSumInClus[c_en]/sumAllAlignLinks
        py = frEdgeSumInClus[c_fr]/sumAllAlignLinks
        sumClusEntrop += pxy*log(pxy/px) + pxy*log(pxy/py)
        
    return perplex, -power*sumClusEntrop
           
def getBothWaysAlignment():
    
    enToFr = {}
    frToEn = {}
    for (w_en, w_fr) in alignDict:
        if w_en not in enToFr:
            enToFr[w_en] = [w_fr]
        else:
            enToFr[w_en].append(w_fr)
            
        if w_fr not in frToEn:
            frToEn[w_fr] = [w_en]
        else:
            frToEn[w_fr].append(w_en)
            
    return enToFr, frToEn
    
def main(inputFileName, alignFileName, enPOSFileName, frPOSFileName):
    
    # All the bilingual data structures are global
    global alignDict, frToEnAlignedDict, enToFrAlignedDict, alignedWordsInClusPairDict, clusSimilarityDict
    global sizeLang, sumAlignedWordsInClusPairDict
    #global enWordAlignedClusDict, frWordAlignedClusDict
    #global enClusAlignedClusDict, frClusAlignedClusDict
    #global enWordToFrClusCount, frWordToEnClusCount
    global enEdgeSumInClus, frEdgeSumInClus
    #global enWordEdgeCount, frWordEdgeCount
    global sumAllAlignLinks
    global sizeLang
    
    global enWordVocab, frWordVocab
    
    enWordToClusDict, enWordsInClusDict = readPOSClusters(enPOSFileName)
    frWordToClusDict, frWordsInClusDict = readPOSClusters(frPOSFileName)
    
    # Read the input file and get word counts
    alignDict, enWordDict, enBigramDict, enNextWordDict, enPrevWordDict, \
    frWordDict, frBigramDict, frNextWordDict, frPrevWordDict, enWordVocab, frWordVocab\
     = readBilingualData(inputFileName, alignFileName, enWordToClusDict, frWordToClusDict)
    
    sizeLang = {}
    sizeLang['en'] = sum(val for word, val in enWordDict.iteritems())
    sizeLang['fr'] = sum(val for word, val in frWordDict.iteritems())
    
    sumAllAlignLinks = 1.0*sum(val for (w1, w2), val in alignDict.iteritems())
    
    enDeleteWords = []
    num = 0
    for word in enWordToClusDict:
        if word not in enWordVocab:
            enDeleteWords.append(word)
            num += 1
            
    print num
    
    frDeleteWords = []      
    num = 0  
    for word in frWordToClusDict:
        if word not in frWordVocab:
            frDeleteWords.append(word)
            num += 1
            
    print num
    
    for word in enDeleteWords:
        del enWordToClusDict[word]
        
        
    for word in frDeleteWords:
        del frWordToClusDict[word]
        
    print len(enWordToClusDict), len(frWordToClusDict), len(enWordDict), len(frWordDict)
    
    # Get counts of the initial cluster configuration
    enClusUniCount, enClusBiCount = getClusterCounts(enWordToClusDict, enWordsInClusDict, enWordDict, enBigramDict)
    frClusUniCount, frClusBiCount = getClusterCounts(frWordToClusDict, frWordsInClusDict, frWordDict, frBigramDict)
    
    # Get a dictionary of aligned word pairs in a cluster pair
    alignedWordsInClusPairDict, sumAlignedWordsInClusPairDict = getAllAlignedWordsInClusPair(enWordToClusDict, frWordToClusDict)
    enToFrAlignedDict, frToEnAlignedDict = getBothWaysAlignment()
    
    enEdgeSumInClus, frEdgeSumInClus = getInitialEdgeInCluster(enWordsInClusDict, frWordsInClusDict)
    
    origMono, origBi = calcPerplexity(enWordToClusDict, frWordToClusDict, enWordsInClusDict, frWordsInClusDict,\
                   enWordDict, frWordDict, enClusUniCount, enClusBiCount, frClusUniCount, frClusBiCount)
    
    print origMono, origBi
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", type=str, help="Joint parallel file of two languages; sentences separated by |||")
    parser.add_argument("-a", "--alignfile", type=str, help="alignment file of the parallel corpus")
    parser.add_argument("-l", "--filelength", type=int, default=10000000, help="max number of lines to be read")
    parser.add_argument("-e", "--enPOSFileName", type=str, help="en POS cluster File name")
    parser.add_argument("-f", "--frPOSFileName", type=str, help="fr POS cluster File name")
    parser.add_argument("-p", "--power", type=float, default=1, help="exponent of the multilingual similarity factor")
    
    args = parser.parse_args()
    
    inputFileName = args.inputfile
    alignFileName = args.alignfile
    
    global fileLength
    global power
    fileLength = args.filelength
    enPOSFileName = args.enPOSFileName
    frPOSFileName = args.frPOSFileName
    power = args.power
    
    main(inputFileName, alignFileName, enPOSFileName, frPOSFileName)