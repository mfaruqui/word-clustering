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

def printNewClusters(outputFileName, enWordsInClusDict, frWordsInClusDict, enWordDict, frWordDict):
    
    outFileEn = open(outputFileName+'.en', 'w')
    outFileFr = open(outputFileName+'.fr', 'w')
    
    clusSimDict = {}
    for ((clus1, wordListEn), (clus2, wordListFr)) in zip(enWordsInClusDict.iteritems(), frWordsInClusDict.iteritems()):
        if alignedWordsInClusPairDict.has_key((clus1, clus2)):
            clusSimDict[clus1] = 1.0*len(alignedWordsInClusPairDict[(clus1, clus2)])/(len(wordListEn)*len(wordListFr))
        else:
            clusSimDict[clus1] = 0.0
        
    for clus, val in sorted(clusSimDict.items(), key=itemgetter(1), reverse=True):
        
        wordListEn = enWordsInClusDict[clus]
        wordListFr = frWordsInClusDict[clus]
        
        sortedEnDict = {}
        for word in wordListEn:
            sortedEnDict[word] = enWordDict[word]
        
        sortedEnList = []    
        for (word, val) in sorted(sortedEnDict.items(), key = itemgetter(1), reverse = True):
            sortedEnList.append(word)
            
        sortedFrDict = {}
        for word in wordListFr:
            sortedFrDict[word] = frWordDict[word]
        
        sortedFrList = []    
        for (word, val) in sorted(sortedFrDict.items(), key = itemgetter(1), reverse = True):
            sortedFrList.append(word)
        
        outFileEn.write(str(clus)+' ||| ')       
        for word in sortedEnList:
            outFileEn.write(word+' ')
        outFileEn.write('\n')
        
        outFileFr.write(str(clus)+' ||| ')       
        for word in sortedFrList:
            outFileFr.write(word+' ')
        outFileFr.write('\n')
        
    outFileEn.close()
    outFileFr.close()
        
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

def readBilingualData(bilingualFileName, alignFileName, mono1FileName, mono2FileName):
    
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
            enWordDict[word] += 1.0
            if prevWord != '':
                enBigramDict[(prevWord, word)] += 1.0
            prevWord = word
        
        frWords = fr.split()   
        prevWord = ''
        for word in frWords:
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
    
def getAlignedClasses(fromClass, wordsInClass, fromToAlignDict, toWordToClus):
    
     alignedClasses = []
     for word in wordsInClass[fromClass]:
         if word in fromToAlignDict:
             for alignedWord in fromToAlignDict[word]:
                 c = toWordToClus[alignedWord]
                 if c not in alignedClasses:
                     alignedClasses.append(c)
            
     return alignedClasses
     
def getWordAlignedClasses(wordToBeShifted, aToBAlignedDict, bWordToClusDict):
    
    wordAlignedClasses = []
    if wordToBeShifted in aToBAlignedDict:
        for alignedWord in aToBAlignedDict[wordToBeShifted]:
            c = bWordToClusDict[alignedWord]
            if c not in wordAlignedClasses:
                wordAlignedClasses.append(c)
                
    return wordAlignedClasses
    
def getInitialWordAlignedClasses(enWordToClusDict, frWordToClusDict):
    
    enWordAlignedClusDict = {}
    for w_en, frWordList in enToFrAlignedDict.iteritems():
        enWordAlignedClusDict[w_en] = []
        for w_fr in frWordList:
            c_fr = frWordToClusDict[w_fr]
            if c_fr not in enWordAlignedClusDict[w_en]:
                enWordAlignedClusDict[w_en].append(c_fr)
                
    frWordAlignedClusDict = {}
    for w_fr, enWordList in frToEnAlignedDict.iteritems():
        frWordAlignedClusDict[w_fr] = []
        for w_en in enWordList:
            c_en = enWordToClusDict[w_en]
            if c_en not in frWordAlignedClusDict[w_fr]:
                frWordAlignedClusDict[w_fr].append(c_en)
                
    return enWordAlignedClusDict, frWordAlignedClusDict
    
def getInitialClassAlignedClasses(enClusUniDict, enWordsInClusDict, frClusUniDict, frWordsInClusDict, enWordToClusDict, frWordToClusDict):
    
    enClusAlignedClusDict = {}
    for c_en in enClusUniDict.iterkeys():
        enClusAlignedClusDict[c_en] = []
        for w_en in enWordsInClusDict[c_en]:
            if w_en in enToFrAlignedDict:
                for w_fr in enToFrAlignedDict[w_en]:
                    c_fr = frWordToClusDict[w_fr]
                    if c_fr not in enClusAlignedClusDict[c_en]:
                        enClusAlignedClusDict[c_en].append(c_fr)
    
    frClusAlignedClusDict = {}
    for c_fr in frClusUniDict.iterkeys():
        frClusAlignedClusDict[c_fr] = []
        for w_fr in frWordsInClusDict[c_fr]:
            if w_fr in frToEnAlignedDict:
                for w_en in frToEnAlignedDict[w_fr]:
                    c_en = enWordToClusDict[w_en]
                    if c_en not in frClusAlignedClusDict[c_fr]:
                        frClusAlignedClusDict[c_fr].append(c_en)
                
    return enClusAlignedClusDict, frClusAlignedClusDict
    
def getInitialWordAlignedClusCount(enWordToClusDict, frWordToClusDict):
    
    enWordToFrClusCount = Counter()
    for w_en, frWordList in enToFrAlignedDict.iteritems():
        for w_fr in frWordList:
            c_fr = frWordToClusDict[w_fr]
            enWordToFrClusCount[(w_en, c_fr)] += alignDict[(w_en, w_fr)]
            
    frWordToEnClusCount = Counter()
    for w_fr, enWordList in frToEnAlignedDict.iteritems():
        for w_en in enWordList:
            c_en = enWordToClusDict[w_en]
            frWordToEnClusCount[(w_fr, c_en)] += alignDict[(w_en, w_fr)]

    return enWordToFrClusCount, frWordToEnClusCount
    
def getShiftedWordAlignedCount(lang, word, alignedClus, lookInDict, wordToClusDict):
    
    count = 0
    for alignedWord in lookInDict[word]:
        c = wordToClusDict[alignedWord]
        if c == alignedClus:
            if lang == 'en':
                count += alignDict[(word, alignedWord)]
            else:
                count += alignDict[(alignedWord, word)]
            
    return count
    
def getWordEdgeCount(enWordToFrClusCount, frWordToEnClusCount):
    
    enWordEdgeCount = Counter() 
    frWordEdgeCount = Counter()
    
    for (w_en, c_fr), val in enWordToFrClusCount.iteritems():
        enWordEdgeCount[w_en] += val
        
    for (w_fr, c_en), val in frWordToEnClusCount.iteritems():
        frWordEdgeCount[w_fr] += val
        
    return enWordEdgeCount, frWordEdgeCount
    
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
        
    #sys.stderr.write('Mono factor:'+str(perplex)+' '+'Cross-lingual factor:'+str(power*sumClusEntrop)+'\n')        
    #perplex -= power*sumClusEntrop            
    
    return perplex, -power*sumClusEntrop
            
def calcTentativePerplex(lang, origMono, origBi, wordToBeShifted, origClass, tempNewClass, clusUniCount, \
                         clusBiCount, wordToClusDict, wordDict, bigramDict, nextWordDict, prevWordDict,\
                         enWordsInClusDict, frWordsInClusDict, \
                         enWordToClusDict, frWordToClusDict, enWordDict, frWordDict, enClusUniCount, frClusUniCount):
    
    newPerplex = origMono
       
    # Removing the effects of the old unigram cluster count from the perplexity
    newPerplex -= 2 * nlogn(clusUniCount[origClass]/sizeLang[lang])
    newPerplex -= 2 * nlogn(clusUniCount[tempNewClass]/sizeLang[lang])
       
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
       
    newPerplex += 2 * nlogn(newOrigClassUniCount/sizeLang[lang])
    newPerplex += 2 * nlogn(newTempClassUniCount/sizeLang[lang])
       
    for (c1, c2), val in newBiCount.iteritems():
         if c1 != c2:
             # removing the effect of old cluster bigram counts
             newPerplex += nlogn(clusBiCount[(c1, c2)]/sizeLang[lang])
             # adding the effect of new cluster bigram counts
             newPerplex -= nlogn(val/sizeLang[lang])
             
    monoLingPerplex = newPerplex
    
    # Set to zero to know the change in perplex due to bilingual part
    # will add this change to the monoling perplex at the end of the function
    deltaBi = 0.0
        
    if lang == 'en' and wordToBeShifted in enWordAlignedClusDict:
        
        alignedClasses = enClusAlignedClusDict[origClass]
        wordAlignedClasses = enWordAlignedClusDict[wordToBeShifted]
        
        # Changing perplexity effects for classes which had wordToBeshifted aligned
        for alignedClass in wordAlignedClasses:
            
            sumCountShiftedWordAligned = enWordToFrClusCount[(wordToBeShifted, alignedClass)]
            sumCountPair = sumAlignedWordsInClusPairDict[(origClass, alignedClass)]
            
            old_px = enEdgeSumInClus[origClass]/sumAllAlignLinks
            old_py = frEdgeSumInClus[alignedClass]/sumAllAlignLinks
            old_pxy = sumCountPair/sumAllAlignLinks
            
            new_px = (enEdgeSumInClus[origClass] - enWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
            new_py = old_py
            new_pxy = (sumCountPair - sumCountShiftedWordAligned)/sumAllAlignLinks
                    
            deltaBi += old_pxy*log(old_pxy/old_px) + old_pxy*log(old_pxy/old_py)
                    
            if new_pxy != 0:
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                
        for alignedClass in alignedClasses:
            
            if alignedClass not in wordAlignedClasses:
                
                sumCountPair = sumAlignedWordsInClusPairDict[(origClass, alignedClass)]
                
                old_px = enEdgeSumInClus[origClass]/sumAllAlignLinks
                old_py = frEdgeSumInClus[alignedClass]/sumAllAlignLinks
                old_pxy = sumCountPair/sumAllAlignLinks
            
                new_px = (enEdgeSumInClus[origClass] - enWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
                new_py = old_py
                new_pxy = old_pxy
                
                deltaBi += old_pxy*log(old_pxy/old_px) #+ old_pxy*log(old_pxy/old_py)
                deltaBi -= new_pxy*log(new_pxy/new_px) #+ new_pxy*log(new_pxy/new_py)
                    
        # Adding effects due to moving to a new class
        alignedClasses = enClusAlignedClusDict[tempNewClass]
        
        for alignedClass in alignedClasses:
            
            sumCountPair = sumAlignedWordsInClusPairDict[(tempNewClass, alignedClass)]
            sumCountShiftedWordAligned = enWordToFrClusCount[(wordToBeShifted, alignedClass)]
            
            old_px = enEdgeSumInClus[tempNewClass]/sumAllAlignLinks
            old_py = frEdgeSumInClus[alignedClass]/sumAllAlignLinks
            old_pxy = sumCountPair/sumAllAlignLinks
            
            newPerplex += old_pxy*log(old_pxy/old_px) + old_pxy*log(old_pxy/old_py)
            
            if alignedClass not in wordAlignedClasses:
               
               new_px = (enEdgeSumInClus[tempNewClass] + enWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
               new_py = old_py
               new_pxy = old_pxy
                      
               deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                   
            if alignedClass in wordAlignedClasses:
                
                new_px = (enEdgeSumInClus[tempNewClass] + enWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
                new_py = old_py
                new_pxy = (sumCountPair + sumCountShiftedWordAligned)/sumAllAlignLinks
                
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                
        for alignedClass in wordAlignedClasses:
           
            sumCountShiftedWordAligned = enWordToFrClusCount[(wordToBeShifted, alignedClass)]
            
            if alignedClass not in alignedClasses:
                    
                new_px = (enEdgeSumInClus[tempNewClass] + enWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
                new_py = frEdgeSumInClus[alignedClass]/sumAllAlignLinks
                new_pxy = sumCountShiftedWordAligned/sumAllAlignLinks
                    
                # You have alwready removed the old effect earlier now, just add the new effect 
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
            elif alignedClass in alignedClasses:
                
                sumCountPair = sumAlignedWordsInClusPairDict[(tempNewClass, alignedClass)]
                
                new_px = (enEdgeSumInClus[tempNewClass] + enWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
                new_py = frEdgeSumInClus[alignedClass]/sumAllAlignLinks
                new_pxy = (sumCountPair + sumCountShiftedWordAligned)/sumAllAlignLinks
                
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                            
    if lang == 'fr' and frToEnAlignedDict.has_key(wordToBeShifted):
        
        alignedClasses = frClusAlignedClusDict[origClass]
        wordAlignedClasses = frWordAlignedClusDict[wordToBeShifted]
        
        # Changing perplexity effects for classes which had wordToBeshifted aligned
        for alignedClass in wordAlignedClasses:
            
            sumCountShiftedWordAligned = frWordToEnClusCount[(wordToBeShifted, alignedClass)]
            sumCountPair = sumAlignedWordsInClusPairDict[(alignedClass, origClass)]
            
            old_px = frEdgeSumInClus[origClass]/sumAllAlignLinks
            old_py = enEdgeSumInClus[alignedClass]/sumAllAlignLinks
            old_pxy = sumCountPair/sumAllAlignLinks
            
            new_px = (frEdgeSumInClus[origClass] - frWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
            new_py = old_py
            new_pxy = (sumCountPair - sumCountShiftedWordAligned)/sumAllAlignLinks
                    
            deltaBi += old_pxy*log(old_pxy/old_px) + old_pxy*log(old_pxy/old_py)
                    
            if new_pxy != 0:
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                
        for alignedClass in alignedClasses:
            
            if alignedClass not in wordAlignedClasses:
                
                sumCountPair = sumAlignedWordsInClusPairDict[(alignedClass, origClass)]
                
                old_px = frEdgeSumInClus[origClass]/sumAllAlignLinks
                old_py = enEdgeSumInClus[alignedClass]/sumAllAlignLinks
                old_pxy = sumCountPair/sumAllAlignLinks
            
                new_px = (frEdgeSumInClus[origClass] - frWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
                new_py = old_py
                new_pxy = old_pxy
                
                deltaBi += old_pxy*log(old_pxy/old_px) #+ old_pxy*log(old_pxy/old_py)
                deltaBi -= new_pxy*log(new_pxy/new_px) #+ new_pxy*log(new_pxy/new_py)
                    
        # Adding effects due to moving to a new class
        alignedClasses = frClusAlignedClusDict[tempNewClass]
        
        for alignedClass in alignedClasses:
            
            sumCountPair = sumAlignedWordsInClusPairDict[(alignedClass, tempNewClass)]
            sumCountShiftedWordAligned = frWordToEnClusCount[(wordToBeShifted, alignedClass)]
            
            old_px = frEdgeSumInClus[tempNewClass]/sumAllAlignLinks
            old_py = enEdgeSumInClus[alignedClass]/sumAllAlignLinks
            old_pxy = sumCountPair/sumAllAlignLinks
            
            deltaBi += old_pxy*log(old_pxy/old_px) + old_pxy*log(old_pxy/old_py)
            
            if alignedClass not in wordAlignedClasses:
               
               new_px = (frEdgeSumInClus[tempNewClass] + frWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
               new_py = old_py
               new_pxy = old_pxy
                      
               deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                   
            if alignedClass in wordAlignedClasses:
                
                new_px = (frEdgeSumInClus[tempNewClass] + frWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
                new_py = old_py
                new_pxy = (sumCountPair + sumCountShiftedWordAligned)/sumAllAlignLinks
                
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                
        for alignedClass in wordAlignedClasses:
           
            sumCountShiftedWordAligned = frWordToEnClusCount[(wordToBeShifted, alignedClass)]
            
            if alignedClass not in alignedClasses:
                    
                new_px = (frEdgeSumInClus[tempNewClass] + frWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
                new_py = enEdgeSumInClus[alignedClass]/sumAllAlignLinks
                new_pxy = sumCountShiftedWordAligned/sumAllAlignLinks
                    
                # You have alwready removed the old effect earlier now, just add the new effect 
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
            elif alignedClass in alignedClasses:
                
                sumCountPair = sumAlignedWordsInClusPairDict[(alignedClass, tempNewClass)]
                
                new_px = (frEdgeSumInClus[tempNewClass] + frWordEdgeCount[wordToBeShifted])/sumAllAlignLinks
                new_py = enEdgeSumInClus[alignedClass]/sumAllAlignLinks
                new_pxy = (sumCountPair + sumCountShiftedWordAligned)/sumAllAlignLinks
                
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
    #print monoLingPerplex, newPerplex
    return monoLingPerplex, origBi+power*deltaBi
                                                
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
           
           seenClus = []
           enEdgeSumInClus[origClass] -= enWordEdgeCount[wordToBeShifted]
           enEdgeSumInClus[tempNewClass] += enWordEdgeCount[wordToBeShifted]
           
           for w_fr in enToFrAlignedDict[wordToBeShifted]:
               
               c_fr = frWordToClusDict[w_fr]
               alignedWordsInClusPairDict[(origClass, c_fr)].remove((wordToBeShifted, w_fr))
               
               if (tempNewClass, c_fr) in alignedWordsInClusPairDict:
                   alignedWordsInClusPairDict[(tempNewClass, c_fr)].append((wordToBeShifted, w_fr))
               else:
                   alignedWordsInClusPairDict[(tempNewClass, c_fr)] = [(wordToBeShifted, w_fr)]
               
               if c_fr not in seenClus:
                   
                   seenClus.append(c_fr)
                   sumCountShiftedWordAligned = \
                   getShiftedWordAlignedCount("en", wordToBeShifted, c_fr, enToFrAlignedDict, frWordToClusDict)
                   
                   sumAlignedWordsInClusPairDict[(origClass, c_fr)] -= sumCountShiftedWordAligned
                   sumAlignedWordsInClusPairDict[(tempNewClass, c_fr)] += sumCountShiftedWordAligned
                   
                   frClusAlignedClusDict[c_fr] = getAlignedClasses(c_fr, frWordsInClusDict, frToEnAlignedDict, enWordToClusDict)
                   
               # Re-compute the frWordAlignedClusDict for all words that
               # were aligned to this word
               frWordAlignedClusDict[w_fr] = getWordAlignedClasses(w_fr, frToEnAlignedDict, enWordToClusDict)
               frWordToEnClusCount[(w_fr, origClass)] -= alignDict[(wordToBeShifted, w_fr)]
               frWordToEnClusCount[(w_fr, tempNewClass)] += alignDict[(wordToBeShifted, w_fr)]
               
           enClusAlignedClusDict[origClass] = getAlignedClasses(origClass, enWordsInClusDict, enToFrAlignedDict, frWordToClusDict)
           enClusAlignedClusDict[tempNewClass] = getAlignedClasses(tempNewClass, enWordsInClusDict, enToFrAlignedDict, frWordToClusDict)
               
           del seenClus
                       
       if lang == 'fr' and frToEnAlignedDict.has_key(wordToBeShifted):
           
           seenClus = []
           frEdgeSumInClus[origClass] -= frWordEdgeCount[wordToBeShifted]
           frEdgeSumInClus[tempNewClass] += frWordEdgeCount[wordToBeShifted]
           
           for w_en in frToEnAlignedDict[wordToBeShifted]:
               
               c_en = enWordToClusDict[w_en]
               alignedWordsInClusPairDict[(c_en, origClass)].remove((w_en, wordToBeShifted))
               
               if (c_en, tempNewClass) in alignedWordsInClusPairDict:
                   alignedWordsInClusPairDict[(c_en, tempNewClass)].append((w_en, wordToBeShifted))
               else:
                   alignedWordsInClusPairDict[(c_en, tempNewClass)] = [(w_en, wordToBeShifted)]
               
               if c_en not in seenClus:
                   
                   seenClus.append(c_en)
                   sumCountShiftedWordAligned = \
                   getShiftedWordAlignedCount("fr", wordToBeShifted, c_en, frToEnAlignedDict, enWordToClusDict)
                   
                   sumAlignedWordsInClusPairDict[(c_en, origClass)] -= sumCountShiftedWordAligned
                   sumAlignedWordsInClusPairDict[(c_en, tempNewClass)] += sumCountShiftedWordAligned
                   
                   enClusAlignedClusDict[c_en] = getAlignedClasses(c_en, enWordsInClusDict, enToFrAlignedDict, frWordToClusDict)
                   
               # Re-compute the enWordAlignedClusDict for all words that
               # were aligned to this word    
               enWordAlignedClusDict[w_en] = getWordAlignedClasses(w_en, enToFrAlignedDict, frWordToClusDict)
               enWordToFrClusCount[(w_en, origClass)] -= alignDict[(w_en, wordToBeShifted)]
               enWordToFrClusCount[(w_en, tempNewClass)] += alignDict[(w_en, wordToBeShifted)]
               
           frClusAlignedClusDict[origClass] = getAlignedClasses(origClass, frWordsInClusDict, frToEnAlignedDict, enWordToClusDict)
           frClusAlignedClusDict[tempNewClass] = getAlignedClasses(tempNewClass, frWordsInClusDict, frToEnAlignedDict, enWordToClusDict)
               
           del seenClus
                    
       return
       
def rearrangeClusters(lang, origMono, origBi,
                clusUniCount, clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict, \
                enWordsInClusDict, frWordsInClusDict, enWordToClusDict, frWordToClusDict, enWordDict, frWordDict,\
                enClusUniCount, frClusUniCount):
    
    wordsExchanged = 0
    wordsDone = 0
    
    currLeastMono = origMono
    currLeastBi = origBi
    
    for word in wordDict.keys():
        origClass = wordToClusDict[word]
        currLeastPerplex = origMono + origBi
        tempNewClass = origClass
        
        # Try shifting every word to a new cluster and caluculate perplexity
        # Ensures that every cluster has at least 2 elements 
        if len(wordsInClusDict[origClass]) > 2:
            for possibleNewClass in clusUniCount.keys():
                if possibleNewClass != origClass:
                    tempMono, tempBi = calcTentativePerplex(lang, origMono, origBi, word, origClass, possibleNewClass,\
                    clusUniCount, clusBiCount, wordToClusDict, wordDict, bigramDict, nextWordDict, prevWordDict, \
                    enWordsInClusDict, frWordsInClusDict, \
                    enWordToClusDict, frWordToClusDict, enWordDict, frWordDict, enClusUniCount, frClusUniCount)
                    
                    possiblePerplex = tempMono + tempBi 
                    
                    if possiblePerplex < currLeastPerplex:
                        currLeastPerplex = possiblePerplex
                        tempNewClass = possibleNewClass
                        
                        currLeastMono = tempMono
                        currLeastBi = tempBi 
            
            if tempNewClass != origClass:
                wordsExchanged += 1
                updateClassDistrib(lang, \
                        enWordsInClusDict, frWordsInClusDict, enWordToClusDict, frWordToClusDict, word, origClass, tempNewClass, \
                        clusUniCount, clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict,\
                        enWordDict, frWordDict)
                    
        wordsDone += 1
        if wordsDone % 1000 == 0:    
            sys.stderr.write(str(wordsDone)+' ')

        #origPerplex = currLeastPerplex
        origMono = currLeastMono
        origBi = currLeastBi
        
    #return wordsExchanged, currLeastPerplex                
    return wordsExchanged, origMono, origBi

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
    
    origMono, origBi = calcPerplexity(enWordToClusDict, frWordToClusDict, enWordsInClusDict, frWordsInClusDict,\
               enWordDict, frWordDict, enClusUniCount, enClusBiCount, frClusUniCount, frClusBiCount)
    
    while ( (wordsExchanged > 0.001 * (enWordVocabLen + frWordVocabLen) or iterNum < 10) and iterNum <= 25):
        iterNum += 1
        wordsExchanged = 0
        wordsDone = 0
    
        #origPerplex = origMono + origBi
    
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Mono: '+str(origMono)+' Bi: '+str(origBi)+' Total: '+str(origMono + origBi)+'\n')
        sys.stderr.write('\nRearranging English words...\n')
        
        wordsExchangedEn, origMono, origBi = rearrangeClusters('en', origMono, origBi,
                enClusUniCount, enClusBiCount, enWordToClusDict, enWordsInClusDict, enWordDict, enBigramDict, enNextWordDict, enPrevWordDict, \
                enWordsInClusDict, frWordsInClusDict, \
                enWordToClusDict, frWordToClusDict, enWordDict, frWordDict,\
                enClusUniCount, frClusUniCount)
        
        #origPerplex = origMono + origBi
        
        wordsExchanged = wordsExchangedEn
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchangedEn)+'\n')
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Mono: '+str(origMono)+' Bi: '+str(origBi)+' Total: '+str(origMono + origBi)+'\n')
        sys.stderr.write('\nRearranging French words...\n')
                    
        wordsExchangedFr, origMono, origBi = rearrangeClusters('fr', origMono, origBi,
                frClusUniCount, frClusBiCount, frWordToClusDict, frWordsInClusDict, frWordDict, frBigramDict, frNextWordDict, frPrevWordDict, \
                enWordsInClusDict, frWordsInClusDict, \
                enWordToClusDict, frWordToClusDict, enWordDict, frWordDict,\
                enClusUniCount, frClusUniCount)
        
        wordsExchanged += wordsExchangedFr 
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchangedFr)+'\n')
        
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
    
def main(inputFileName, alignFileName, mono1FileName, mono2FileName, outputFileName, numClusInit, typeClusInit):
    
    # All the bilingual data structures are global
    global alignDict, frToEnAlignedDict, enToFrAlignedDict, alignedWordsInClusPairDict, clusSimilarityDict
    global sizeLang, sumAlignedWordsInClusPairDict
    global enWordAlignedClusDict, frWordAlignedClusDict
    global enClusAlignedClusDict, frClusAlignedClusDict
    global enWordToFrClusCount, frWordToEnClusCount
    global enEdgeSumInClus, frEdgeSumInClus
    global enWordEdgeCount, frWordEdgeCount
    global sumAllAlignLinks
    global sizeLang
    
    # Read the input file and get word counts
    alignDict, enWordDict, enBigramDict, enNextWordDict, enPrevWordDict, \
    frWordDict, frBigramDict, frNextWordDict, frPrevWordDict = readBilingualData(inputFileName, alignFileName, mono1FileName, mono2FileName)
    
    sizeLang = {}
    sizeLang['en'] = sum(val for word, val in enWordDict.iteritems())
    sizeLang['fr'] = sum(val for word, val in frWordDict.iteritems())
    
    sumAllAlignLinks = 1.0*sum(val for (w1, w2), val in alignDict.iteritems())
    
    # Initialise the cluster distribution
    enWordToClusDict, enWordsInClusDict = formInitialClusters(numClusInit, enWordDict, typeClusInit)
    frWordToClusDict, frWordsInClusDict = formInitialClusters(numClusInit, frWordDict, typeClusInit)
    
    # Get counts of the initial cluster configuration
    enClusUniCount, enClusBiCount = getClusterCounts(enWordToClusDict, enWordsInClusDict, enWordDict, enBigramDict)
    frClusUniCount, frClusBiCount = getClusterCounts(frWordToClusDict, frWordsInClusDict, frWordDict, frBigramDict)
    
    # Get a dictionary of aligned word pairs in a cluster pair
    alignedWordsInClusPairDict, sumAlignedWordsInClusPairDict = getAllAlignedWordsInClusPair(enWordToClusDict, frWordToClusDict)
    enToFrAlignedDict, frToEnAlignedDict = getBothWaysAlignment()
    
    enEdgeSumInClus, frEdgeSumInClus = getInitialEdgeInCluster(enWordsInClusDict, frWordsInClusDict)
    
    enWordAlignedClusDict, frWordAlignedClusDict = getInitialWordAlignedClasses(enWordToClusDict, frWordToClusDict)
    
    enClusAlignedClusDict, frClusAlignedClusDict = \
    getInitialClassAlignedClasses(enClusUniCount, enWordsInClusDict, frClusUniCount, frWordsInClusDict, enWordToClusDict, frWordToClusDict)
    
    enWordToFrClusCount, frWordToEnClusCount = getInitialWordAlignedClusCount(enWordToClusDict, frWordToClusDict)
    
    enWordEdgeCount, frWordEdgeCount = getWordEdgeCount(enWordToFrClusCount, frWordToEnClusCount)
    
    # Get cluster similarity of all possible pairs
    #clusSimilarityDict = getClusSimilarity(enClusUniCount, frClusUniCount, enWordsInClusDict, frWordsInClusDict)
    
    # Run the clustering algorithm and get new clusters    
    enClusUniCount, enClusBiCount, enWordToClusDict, enWordsInClusDict,\
    frClusUniCount, frClusBiCount, frWordToClusDict, frWordsInClusDict = \
        runOchClustering(
        enWordDict, enBigramDict, enClusUniCount, enClusBiCount, enWordToClusDict, enWordsInClusDict, enNextWordDict, enPrevWordDict,\
        frWordDict, frBigramDict, frClusUniCount, frClusBiCount, frWordToClusDict, frWordsInClusDict, frNextWordDict, frPrevWordDict\
        )
    
    # Print the clusters
    printNewClusters(outputFileName, enWordsInClusDict, frWordsInClusDict, enWordDict, frWordDict)
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", type=str, help="Joint parallel file of two languages; sentences separated by |||")
    parser.add_argument("-a", "--alignfile", type=str, help="alignment file of the parallel corpus")
    parser.add_argument("-m1", "--monofile1", type=str, default='', help="Monolingual file of langauge 1")
    parser.add_argument("-m2", "--monofile2", type=str, default='', help="Monolingual file of langauge 2")
    parser.add_argument("-l", "--filelength", type=int, default=1000000000, help="max number of lines to be read")
    parser.add_argument("-n", "--numclus", type=int, default=100, help="No. of clusters to be formed")
    parser.add_argument("-o", "--outputfile", type=str, help="Output file with word clusters")
    parser.add_argument("-t", "--type", type=int, choices=[0, 1], default=1, help="type of cluster initialization")
    parser.add_argument("-p", "--power", type=float, default=1, help="exponent of the multilingual similarity factor")
                        
    args = parser.parse_args()
    
    inputFileName = args.inputfile
    alignFileName = args.alignfile
    mono1FileName = args.monofile1
    mono2FileName = args.monofile2
    numClusInit = args.numclus
    outputFileName = args.outputfile
    typeClusInit = args.type
    
    global power
    global fileLength
    power = args.power
    fileLength = args.filelength
    
    main(inputFileName, alignFileName, mono1FileName, mono2FileName, outputFileName, numClusInit, typeClusInit)