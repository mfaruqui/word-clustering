# Type python ochClustering.py -h for information on how to use
import sys
from operator import itemgetter
import math
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
            logValues[x] = x * math.log(x)
            return logValues[x]

def printNewClusters(outputFileName, enWordsInClusDict, frWordsInClusDict):
    
    outFile = open(outputFileName, 'w')
    
    clusSimDict = {}
    for ((clus1, wordListEn), (clus2, wordListFr)) in zip(enWordsInClusDict.iteritems(), frWordsInClusDict.iteritems()):
        if alignedWordsInClusPairDict.has_key((clus1, clus2)):
            clusSimDict[clus1] = 1.0*len(alignedWordsInClusPairDict[(clus1, clus2)])/(len(wordListEn)*len(wordListFr))
        else:
            clusSimDict[clus1] = 0.0
        
    for clus, val in sorted(clusSimDict.items(), key=itemgetter(1), reverse=True):
        #for ((clus1, wordListEn), (clus2, wordListFr)) in zip(enWordsInClusDict.iteritems(), frWordsInClusDict.iteritems()):
        
        wordListEn = enWordsInClusDict[clus]
        wordListFr = frWordsInClusDict[clus]
        
        outFile.write(str(clus)+' ||| ')       
        for word in wordListEn:
            outFile.write(word+' ')
        outFile.write('\n')
        
        outFile.write(str(clus)+' ||| ')       
        for word in wordListFr:
            outFile.write(word+' ')
        outFile.write('\n')
        
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

def readBilingualData(bilingualFileName, alignFileName):
    
    enWordDict = Counter()
    enBigramDict = Counter()
    frWordDict = Counter()
    frBigramDict = Counter()
    alignDict = Counter()
    sys.stderr.write('\nReading parallel and alignment file...\n')
    
    for wordLine, alignLine in zip(open(bilingualFileName,'r'), open(alignFileName, 'r')):
        
        en, fr = wordLine.split('|||')
        en = en.strip()
        fr = fr.strip()
        enWords = en.split()
        frWords = fr.split()
        
        prevWord = ''
        for word in enWords:
            enWordDict[word] += 1
            if prevWord != '':
                enBigramDict[(prevWord, word)] += 1
            prevWord = word
            
        prevWord = ''
        for word in frWords:
            frWordDict[word] += 1
            if prevWord != '':
                frBigramDict[(prevWord, word)] += 1
            prevWord = word
            
        for alignments in alignLine.split():
            en, fr = alignments.split('-')
            enWord = enWords[int(en)]
            frWord = frWords[int(fr)]
            alignDict[(enWord, frWord)] += 1
     
    enNextWordDict, enPrevWordDict = getNextPrevWordDict(enBigramDict)    
    frNextWordDict, frPrevWordDict = getNextPrevWordDict(frBigramDict)
    
    # Filtering out alignment pairs by their counts
    threshCount = 3
    alignDict = {key:value for (key, value) in alignDict.iteritems() if value >= threshCount}
           
    return alignDict, enWordDict, enBigramDict, enNextWordDict, enPrevWordDict, \
    frWordDict, frBigramDict, frNextWordDict, frPrevWordDict
    
def formInitialClusters(numClusInit, wordDict, typeClusInit):
    
    wordsInClusDict = {}
    wordToClusDict = {}
    
    if typeClusInit == 0:
        # Put top numClusInit-1 words into their own cluster
        # Put the rest of the words into a single cluster
        insertedClus = 0
        for key, val in sorted(wordDict.items(), key=itemgetter(1), reverse=True):
            if insertedClus == numClusInit:
                wordToClusDict[key] = insertedClus
                try:
                    wordsInClusDict[insertedClus].append(key)
                except KeyError:
                    wordsInClusDict[insertedClus] = [key]
            else:
                wordsInClusDict[insertedClus] = [key]
                wordToClusDict[key] = insertedClus
        
                insertedClus += 1
                
    if typeClusInit == 1:
        # Put words into the clusters in a round robin fashion
        # according the weight of the word
        numWord = 0
        for key, val in sorted(wordDict.items(), key=itemgetter(1), reverse=True):
            newClusNum = numWord % numClusInit
            wordToClusDict[key] = newClusNum
            try:
                wordsInClusDict[newClusNum].append(key)
            except KeyError:
                wordsInClusDict[newClusNum] = [key]
                
            numWord += 1    
            
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
    sys.stderr.write("\nMaking an word-alignment info dictionary of clusters...\n")
    
    for (w_en, w_fr) in alignDict.iterkeys():
        c_en = enWordToClusDict[w_en]
        c_fr = frWordToClusDict[w_fr]
        
        if (c_en, c_fr) in alignedWordsInClusPair:
            alignedWordsInClusPair[(c_en, c_fr)].append((w_en, w_fr))
        else:
            alignedWordsInClusPair[(c_en, c_fr)] = [(w_en, w_fr)]
                            
    return alignedWordsInClusPair
    
def getClusSimilarity(enWordDict, frWordDict, enClusUniCount, frClusUniCount, enWordsInClusDict, frWordsInClusDict):
    
    clusSimilarityDict = Counter()
    sys.stderr.write("\nComputing initial inter-language cluster similarities...\n")
    
    totLinks = len(alignDict)
    enLen = len(enWordDict)
    frLen = len(frWordDict)
    for c_en in enClusUniCount.iterkeys():
        for c_fr in frClusUniCount.iterkeys():
            if (c_en, c_fr) in alignedWordsInClusPairDict.iterkeys():
                p_en = 1.0*len(enWordsInClusDict[c_en])/enLen
                p_fr = 1.0*len(frWordsInClusDict[c_fr])/frLen
                p_en_fr = 1.0*len(alignedWordsInClusPairDict[(c_en, c_fr)])/totLinks
                clusSimilarityDict[(c_en, c_fr)] = p_en_fr * math.log(p_en_fr/(p_en*p_fr))
            else:
                clusSimilarityDict[(c_en, c_fr)] = 0.0
                
    return clusSimilarityDict

def calcPerplexity(enWordToClusDict, frWordToClusDict, enWordsInClusDict, frWordsInClusDict,\
                   enWordDict, frWordDict, enUniCount, enBiCount, frUniCount, frBiCount):
    
    sum1 = 0
    sum2 = 0
    
    for (c1, c2), nC1C2 in enBiCount.iteritems():
        if nC1C2 != 0 and c1 != c2:
            sum1 += nlogn( nC1C2 )
    
    for c, n in enUniCount.iteritems():
        if n != 0:
            sum2 += nlogn( n )
            
    for (c1, c2), nC1C2 in frBiCount.iteritems():
        if nC1C2 != 0 and c1 != c2:
            sum1 += nlogn( nC1C2 )
    
    for c, n in frUniCount.iteritems():
        if n != 0:
            sum2 += nlogn( n )
            
    perplex = 2 * sum2 - sum1
    
    enWordCount = len(enWordDict)
    frWordCount = len(frWordDict)
    totLinks = len(alignDict)
    sumClusEntrop = 0
    
    for (c_en, c_fr) in alignedWordsInClusPairDict.iterkeys():
        links = len(alignedWordsInClusPairDict[(c_en, c_fr)])
        p_en = 1.0*len(enWordsInClusDict[c_en])/enWordCount
        p_fr = 1.0*len(frWordsInClusDict[c_fr])/frWordCount
        p_en_fr = 1.0*links/totLinks
        if links != 0:
            sumClusEntrop += p_en_fr*math.log(p_en_fr/(p_en*p_fr))
            
    perplex -= power*sumClusEntrop
        
    return perplex
            
def calcTentativePerplex(lang, origPerplex, wordToBeShifted, origClass, tempNewClass, clusUniCount, \
                         clusBiCount, wordToClusDict, wordDict, bigramDict, nextWordDict, prevWordDict,\
                         enWordsInClusDict, frWordsInClusDict, \
                         enWordToClusDict, frWordToClusDict, enWordDict, frWordDict):
    
    newPerplex = origPerplex
       
    # Removing the effects of the old unigram cluster count from the perplexity
    newPerplex -= 2 * nlogn(clusUniCount[origClass])
    newPerplex -= 2 * nlogn(clusUniCount[tempNewClass])
       
    # Finding only those bigram cluster counts that will be effected by the word transfer
    newBiCount = {}
    if nextWordDict.has_key(wordToBeShifted):
        for w in nextWordDict[wordToBeShifted]:
            c = wordToClusDict[w]
            if (origClass, c) in newBiCount:
                newBiCount[(origClass, c)] -= bigramDict[(wordToBeShifted, w)]
            else:
                newBiCount[(origClass, c)] = clusBiCount[(origClass, c)] - bigramDict[(wordToBeShifted, w)]
               
            if (tempNewClass, c) in newBiCount:
                newBiCount[(tempNewClass, c)] += bigramDict[(wordToBeShifted, w)]
            else:
                newBiCount[(tempNewClass, c)] = clusBiCount[(tempNewClass, c)] + bigramDict[(wordToBeShifted, w)]      
    
    #sys.stderr.write(wordToBeShifted+' ')
    if prevWordDict.has_key(wordToBeShifted):
        for w in prevWordDict[wordToBeShifted]:
            c = wordToClusDict[w]
            if (c, origClass) in newBiCount:
                newBiCount[(c, origClass)] -= bigramDict[(w, wordToBeShifted)]
            else:
                newBiCount[(c, origClass)] = clusBiCount[(c, origClass)] - bigramDict[(w, wordToBeShifted)]
               
            if (c, tempNewClass) in newBiCount:
                newBiCount[(c, tempNewClass)] += bigramDict[(w, wordToBeShifted)]
            else:
                newBiCount[(c, tempNewClass)] = clusBiCount[(c, tempNewClass)] + bigramDict[(w, wordToBeShifted)]
       
    # Adding the effects of new unigram cluster counts in the perplexity
    newOrigClassUniCount = clusUniCount[origClass] - wordDict[wordToBeShifted]
    newTempClassUniCount = clusUniCount[tempNewClass] + wordDict[wordToBeShifted]
       
    newPerplex += 2 * nlogn(newOrigClassUniCount)
    newPerplex += 2 * nlogn(newTempClassUniCount)
       
    for (c1, c2), val in newBiCount.iteritems():
         if c1 != c2:
             # removing the effect of old cluster bigram counts
             newPerplex += nlogn(clusBiCount[(c1, c2)])
             # adding the effect of new cluster bigram counts
             newPerplex -= nlogn(val)
                          
    if lang == 'en' and enToFrAlignedDict.has_key(wordToBeShifted):
        frSeenClus = {}
        
        totLinks = len(alignDict)
        enLen = len(enWordDict)
        frLen = len(frWordDict)
        
        for w_fr in enToFrAlignedDict[wordToBeShifted]:
            c_fr = frWordToClusDict[w_fr]
            
            if c_fr not in frSeenClus:
                frSeenClus[c_fr] = 0
                oldClusFactor = clusSimilarityDict[(origClass, c_fr)]
                #Changes due to the old cluster
                newPerplex += power*oldClusFactor
                
                pairs = 0
                for (w2_en, w2_fr) in alignedWordsInClusPairDict[(origClass, c_fr)]:
                    if w2_en != wordToBeShifted:
                        pairs += 1
                        
                if pairs != 0:
                    p_en = 1.0*(len(enWordsInClusDict[origClass])-1)/enLen
                    p_fr = 1.0*len(frWordsInClusDict[c_fr])/frLen
                    p_en_fr = 1.0*pairs/totLinks
                    newPerplex -= power*p_en_fr*math.log(p_en_fr/(p_en*p_fr))
                
                #Changes due to the new cluster
                oldClusFactor = clusSimilarityDict[(tempNewClass, c_fr)]
                if oldClusFactor != 0.0:
                    newPerplex += power*oldClusFactor                    
                
                newPairs = 0
                for word_fr in enToFrAlignedDict[wordToBeShifted]:
                    if frWordToClusDict[word_fr] == c_fr:
                        newPairs += 1
                        
                if newPairs != 0:
                    p_en = 1.0*(len(enWordsInClusDict[tempNewClass])+1)/enLen
                    p_fr = 1.0*len(frWordsInClusDict[c_fr])/frLen
                    p_en_fr = 1.0*newPairs/totLinks
                    newPerplex -= power*p_en_fr*math.log(p_en_fr/(p_en*p_fr))
                    
        del frSeenClus
                            
    if lang == 'fr' and frToEnAlignedDict.has_key(wordToBeShifted):
        enSeenClus = {}
        
        totLinks = len(alignDict)
        enLen = len(enWordDict)
        frLen = len(frWordDict)
        
        for w_en in frToEnAlignedDict[wordToBeShifted]:
            c_en = enWordToClusDict[w_en]
            
            if c_en not in enSeenClus:
                enSeenClus[c_en] = 0
                oldClusFactor = clusSimilarityDict[(c_en, origClass)]
                newPerplex += power*oldClusFactor
                
                pairs = 0
                for (w2_en, w2_fr) in alignedWordsInClusPairDict[(c_en, origClass)]:
                    if w2_fr != wordToBeShifted:
                        pairs += 1
                        
                if pairs != 0:
                    p_en = 1.0*len(enWordsInClusDict[c_en])/enLen
                    p_fr = 1.0*(len(frWordsInClusDict[origClass])-1)/frLen
                    p_en_fr = 1.0*pairs/totLinks
                    newPerplex -= power*p_en_fr*math.log(p_en_fr/(p_en*p_fr))
                
                oldClusFactor = clusSimilarityDict[(c_en, tempNewClass)]
                if oldClusFactor != 0.0:
                    newPerplex += power*oldClusFactor
                
                newPairs = 0
                for word_en in frToEnAlignedDict[wordToBeShifted]:
                    if enWordToClusDict[word_en] == c_en:
                        newPairs += 1
                
                if newPairs != 0:
                    p_en = 1.0*len(enWordsInClusDict[c_en])/enLen
                    p_fr = 1.0*(len(frWordsInClusDict[tempNewClass])+1)/frLen
                    p_en_fr = 1.0*newPairs/totLinks
                    newPerplex -= power*p_en_fr*math.log(p_en_fr/(p_en*p_fr))
                
        del enSeenClus
    
    return newPerplex
                                                
def updateClassDistrib(lang, \
                        enWordsInClusDict, frWordsInClusDict, enWordToClusDict, frWordToClusDict, \
                        wordToBeShifted, origClass, tempNewClass, clusUniCount, clusBiCount, wordToClusDict, \
                        wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict, enWordDict, frWordDict):
            
       clusUniCount[origClass] -= wordDict[wordToBeShifted]
       clusUniCount[tempNewClass] += wordDict[wordToBeShifted]
       
       if nextWordDict.has_key(wordToBeShifted):
           for w in nextWordDict[wordToBeShifted]:
              c = wordToClusDict[w]
              clusBiCount[(origClass, c)] -= bigramDict[(wordToBeShifted, w)]
              clusBiCount[(tempNewClass, c)] += bigramDict[(wordToBeShifted, w)]
              
       if prevWordDict.has_key(wordToBeShifted):
           for w in prevWordDict[wordToBeShifted]:
               c = wordToClusDict[w]
               clusBiCount[(c, origClass)] -= bigramDict[(w, wordToBeShifted)]
               clusBiCount[(c, tempNewClass)] += bigramDict[(w, wordToBeShifted)]
                                              
       wordToClusDict[wordToBeShifted] = tempNewClass
       wordsInClusDict[origClass].remove(wordToBeShifted)
       wordsInClusDict[tempNewClass].append(wordToBeShifted)
       
       if lang == 'en' and enToFrAlignedDict.has_key(wordToBeShifted):
           frSeenClus = {}
           
           totLinks = len(alignDict)
           enLen = len(enWordDict)
           frLen = len(frWordDict)
        
           for w_fr in enToFrAlignedDict[wordToBeShifted]:
               c_fr = frWordToClusDict[w_fr]
            
               if c_fr not in frSeenClus:
                   frSeenClus[c_fr] = 0
                   
                   pairs = 0
                   for (w2_en, w2_fr) in alignedWordsInClusPairDict[(origClass, c_fr)]:
                       if w2_en != wordToBeShifted:
                           pairs += 1        
                   
                   if pairs != 0:
                       p_en = 1.0*(len(enWordsInClusDict[origClass])-1)/enLen
                       p_fr = 1.0*len(frWordsInClusDict[c_fr])/frLen
                       p_en_fr = 1.0*pairs/totLinks
                       clusSimilarityDict[(origClass, c_fr)] = p_en_fr*math.log(p_en_fr/(p_en*p_fr))
                
                   #Changes due to the new cluster
                   newPairs = 0
                   for word_fr in enToFrAlignedDict[wordToBeShifted]:
                       if frWordToClusDict[word_fr] == c_fr:
                           newPairs += 1
                        
                   if newPairs != 0:
                       p_en = 1.0*(len(enWordsInClusDict[tempNewClass])+1)/enLen
                       p_fr = 1.0*len(frWordsInClusDict[c_fr])/frLen
                       p_en_fr = 1.0*newPairs/totLinks
                       clusSimilarityDict[(tempNewClass, c_fr)] = p_en_fr*math.log(p_en_fr/(p_en*p_fr))
                   
           for w_fr in enToFrAlignedDict[wordToBeShifted]:
               c_fr = frWordToClusDict[w_fr]
               alignedWordsInClusPairDict[(origClass, c_fr)].remove((wordToBeShifted, w_fr))
               if alignedWordsInClusPairDict[(origClass, c_fr)] == []:
                   del alignedWordsInClusPairDict[(origClass, c_fr)]
                   
               if (tempNewClass, c_fr) in alignedWordsInClusPairDict:
                   alignedWordsInClusPairDict[(tempNewClass, c_fr)].append((wordToBeShifted, w_fr))
               else:
                   alignedWordsInClusPairDict[(tempNewClass, c_fr)] = [(wordToBeShifted, w_fr)]
                       
       if lang == 'fr' and frToEnAlignedDict.has_key(wordToBeShifted):
           enSeenClus = {}
           
           totLinks = len(alignDict)
           enLen = len(enWordDict)
           frLen = len(frWordDict)
        
           for w_en in frToEnAlignedDict[wordToBeShifted]:
               c_en = enWordToClusDict[w_en]
               
               # ensures that the cluster similarity is taken into account just once
               # irrespective of the number of aligned words it has
               if c_en not in enSeenClus:
                   enSeenClus[c_en] = 0
                   
                   pairs = 0
                   for (w2_en, w2_fr) in alignedWordsInClusPairDict[(c_en, origClass)]:
                       if w2_fr != wordToBeShifted:
                           pairs += 1
                           
                   if pairs != 0:
                       p_en = 1.0*len(enWordsInClusDict[c_en])/enLen
                       p_fr = 1.0*(len(frWordsInClusDict[origClass])-1)/frLen
                       p_en_fr = 1.0*pairs/totLinks
                       clusSimilarityDict[(c_en, origClass)] = p_en_fr*math.log(p_en_fr/(p_en*p_fr))
                
                   newPairs = 0
                   for word_en in frToEnAlignedDict[wordToBeShifted]:
                       if enWordToClusDict[word_en] == c_en:
                           newPairs += 1
                        
                   if newPairs != 0:
                       p_en = 1.0*len(enWordsInClusDict[c_en])/enLen
                       p_fr = 1.0*(len(frWordsInClusDict[tempNewClass])+1)/frLen
                       p_en_fr = 1.0*newPairs/totLinks
                       clusSimilarityDict[(c_en, tempNewClass)] = p_en_fr*math.log(p_en_fr/(p_en*p_fr))
                       
           for w_en in frToEnAlignedDict[wordToBeShifted]:
               c_en = enWordToClusDict[w_en]
               alignedWordsInClusPairDict[(c_en, origClass)].remove((w_en, wordToBeShifted))
               if alignedWordsInClusPairDict[(c_en, origClass)] == []:
                   del alignedWordsInClusPairDict[(c_en, origClass)]
               
               if (c_en, tempNewClass) in alignedWordsInClusPairDict:
                   alignedWordsInClusPairDict[(c_en, tempNewClass)].append((w_en, wordToBeShifted))
               else:
                   alignedWordsInClusPairDict[(c_en, tempNewClass)] = [(w_en, wordToBeShifted)]
                    
       return
       
def rearrangeClusters(lang, origPerplex,
                clusUniCount, clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict, \
                enWordsInClusDict, frWordsInClusDict, enWordToClusDict, frWordToClusDict, enWordDict, frWordDict):
    
    wordsExchanged = 0
    wordsDone = 0
    for word in wordDict.keys():
        origClass = wordToClusDict[word]
        currLeastPerplex = origPerplex
        tempNewClass = origClass
        
        # Try shifting every word to a new cluster and caluculate perplexity
        # Ensures that every cluster has at least 2 elements 
        if len(wordsInClusDict[origClass]) > 2:
            for possibleNewClass in clusUniCount.keys():
                if possibleNewClass != origClass:
                    possiblePerplex = calcTentativePerplex(lang, origPerplex, word, origClass, possibleNewClass,\
                    clusUniCount, clusBiCount, wordToClusDict, wordDict, bigramDict, nextWordDict, prevWordDict, \
                    enWordsInClusDict, frWordsInClusDict, \
                    enWordToClusDict, frWordToClusDict, enWordDict, frWordDict)
                
                    if possiblePerplex < currLeastPerplex:
                        currLeastPerplex = possiblePerplex
                        tempNewClass = possibleNewClass
            
            if tempNewClass != origClass:
                wordsExchanged += 1
                updateClassDistrib(lang, \
                        enWordsInClusDict, frWordsInClusDict, enWordToClusDict, frWordToClusDict, word, origClass, tempNewClass, \
                        clusUniCount, clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict, enWordDict, frWordDict)
                    
        wordsDone += 1
        if wordsDone % 1000 == 0:    
            sys.stderr.write(str(wordsDone)+' ')

        origPerplex = currLeastPerplex
        
    return wordsExchanged                
    

# Implementation of Och 1999 clustering using the     
# algorithm of Martin, Liermann, Ney 1998    
def runOchClustering(
    enWordDict, enBigramDict, enClusUniCount, enClusBiCount, enWordToClusDict, enWordsInClusDict, enNextWordDict, enPrevWordDict,\
    frWordDict, frBigramDict, frClusUniCount, frClusBiCount, frWordToClusDict, frWordsInClusDict, frNextWordDict, frPrevWordDict
    ):
 
    wordsExchanged = 9999
    iterNum = 0
    enWordVocabLen = len(enWordDict.keys())
    frWordVocabLen = len(frWordDict.keys())
    
    while (wordsExchanged > 0.001 * (enWordVocabLen + frWordVocabLen)):
        iterNum += 1
        wordsExchanged = 0
        wordsDone = 0
    
        origPerplex = calcPerplexity(enWordToClusDict, frWordToClusDict, enWordsInClusDict, frWordsInClusDict,\
                   enWordDict, frWordDict, enClusUniCount, enClusBiCount, frClusUniCount, frClusBiCount)
        
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Perplexity: '+str(origPerplex)+'\n')
        sys.stderr.write('\nRearranging English words...\n')
        
        wordsExchanged = rearrangeClusters('en', origPerplex,
                enClusUniCount, enClusBiCount, enWordToClusDict, enWordsInClusDict, enWordDict, enBigramDict, enNextWordDict, enPrevWordDict, \
                enWordsInClusDict, frWordsInClusDict, \
                enWordToClusDict, frWordToClusDict, enWordDict, frWordDict)
        
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchanged)+'\n')
                    
        origPerplex = calcPerplexity(enWordToClusDict, frWordToClusDict, enWordsInClusDict, frWordsInClusDict,\
                   enWordDict, frWordDict, enClusUniCount, enClusBiCount, frClusUniCount, frClusBiCount)
        
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Perplexity: '+str(origPerplex)+'\n')
        sys.stderr.write('\nRearranging French words...\n')
                    
        wordsExchanged = rearrangeClusters('fr', origPerplex,
                frClusUniCount, frClusBiCount, frWordToClusDict, frWordsInClusDict, frWordDict, frBigramDict, frNextWordDict, frPrevWordDict, \
                enWordsInClusDict, frWordsInClusDict, \
                enWordToClusDict, frWordToClusDict, enWordDict, frWordDict)
        
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchanged)+'\n')
            
    return enClusUniCount, enClusBiCount, enWordToClusDict, enWordsInClusDict,\
           frClusUniCount, frClusBiCount, frWordToClusDict, frWordsInClusDict
    
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
    
def main(inputFileName, alignFileName, outputFileName, numClusInit, typeClusInit):
    
    # All the bilingual data structures are global
    global alignDict, frToEnAlignedDict, enToFrAlignedDict, alignedWordsInClusPairDict, clusSimilarityDict
    
    # Read the input file and get word counts
    alignDict, enWordDict, enBigramDict, enNextWordDict, enPrevWordDict, \
    frWordDict, frBigramDict, frNextWordDict, frPrevWordDict = readBilingualData(inputFileName, alignFileName)
    
    # Initialise the cluster distribution
    enWordToClusDict, enWordsInClusDict = formInitialClusters(numClusInit, enWordDict, typeClusInit)
    frWordToClusDict, frWordsInClusDict = formInitialClusters(numClusInit, frWordDict, typeClusInit)
    
    # Get counts of the initial cluster configuration
    enClusUniCount, enClusBiCount = getClusterCounts(enWordToClusDict, enWordsInClusDict, enWordDict, enBigramDict)
    frClusUniCount, frClusBiCount = getClusterCounts(frWordToClusDict, frWordsInClusDict, frWordDict, frBigramDict)
    
    # Get a dictionary of aligned word pairs in a cluster pair
    alignedWordsInClusPairDict = getAllAlignedWordsInClusPair(enWordToClusDict, frWordToClusDict)
    enToFrAlignedDict, frToEnAlignedDict = getBothWaysAlignment()
    
    # Get a word similarity across languages
    # wordSimilarityDict = getWordSimilarity(alignDict, enWordDict, frWordDict)
    
    # Get cluster similarity of all possible pairs
    clusSimilarityDict = getClusSimilarity(enWordDict, frWordDict, enClusUniCount, frClusUniCount, enWordsInClusDict, frWordsInClusDict)
    
    # Run the clustering algorithm and get new clusters    
    enClusUniCount, enClusBiCount, enWordToClusDict, enWordsInClusDict,\
    frClusUniCount, frClusBiCount, frWordToClusDict, frWordsInClusDict = \
        runOchClustering(
        enWordDict, enBigramDict, enClusUniCount, enClusBiCount, enWordToClusDict, enWordsInClusDict, enNextWordDict, enPrevWordDict,\
        frWordDict, frBigramDict, frClusUniCount, frClusBiCount, frWordToClusDict, frWordsInClusDict, frNextWordDict, frPrevWordDict\
        )
    
    # Print the clusters
    printNewClusters(outputFileName, enWordsInClusDict, frWordsInClusDict)
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", type=str, help="Joint parallel file of two languages; sentences separated by |||")
    parser.add_argument("-a", "--alignfile", type=str, help="alignment file of the parallel corpus")
    parser.add_argument("-n", "--numclus", type=int, default=100, help="No. of clusters to be formed")
    parser.add_argument("-o", "--outputfile", type=str, help="Output file with word clusters")
    parser.add_argument("-t", "--type", type=int, choices=[0, 1], default=1, help="type of cluster initialization")
    parser.add_argument("-p", "--power", type=int, default=1, help="exponent of the multilingual similarity factor")
                        
    args = parser.parse_args()
    
    inputFileName = args.inputfile
    alignFileName = args.alignfile
    numClusInit = args.numclus
    outputFileName = args.outputfile
    typeClusInit = args.type
    
    global power
    power = args.power
    
    main(inputFileName, alignFileName, outputFileName, numClusInit, typeClusInit)