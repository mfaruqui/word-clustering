import numpypy
import numpy as np
from math import log
from collections import Counter
from operator import itemgetter
import sys

charSet = {}
biCharSet = {}

# Treat all the number as one character

def makeTransitionProbMatrix(wordDict, wordsInClusDict):
    
    global transMat, priorMat
    
    index = 0
    for word in wordDict.iterkeys():
        for ch in word:
            if ch not in charSet:
                charSet[ch] = index
                index += 1
                
    numChar = len(charSet)
    numClus = len(wordsInClusDict)
    transMat = np.ones((numClus, numChar**2 + 2*numChar))
    priorMat = np.ones((numClus, numChar+2))
    
    index = 0
    for ch1 in charSet.iterkeys():
        for ch2 in charSet.iterkeys():
            if ch2 != ch1:
                biCharSet[(ch1, ch2)] = index
                index += 1
        
        biCharSet[(ch1, ch1)] = index
        index += 1
        
        biCharSet[('<w>', ch1)] = index
        index += 1
        biCharSet[(ch1, '</w>')] = index
        index += 1
        
    lenOrigCharSet = len(charSet)
    charSet['<w>'] = lenOrigCharSet
    charSet['</w>'] = lenOrigCharSet+1
            
    for clus, wordList in wordsInClusDict.iteritems():
        for word in wordList:
            
            transMat[clus][biCharSet[('<w>', word[0])]] += 1.0
            priorMat[clus][charSet['<w>']] += 1.0
            
            for i, ch in enumerate(word):
                transMat[clus][biCharSet[(word[i-1], ch)]] += 1.0
                priorMat[clus][charSet[ch]] += 1.0
                    
            transMat[clus][biCharSet[(ch, '</w>')]] += 1.0
            priorMat[clus][charSet['</w>']] += 1.0
            
    return
    
def getClusMorphFactor(clus):
    
    fact = 0.0
    for (ch1, ch2), index in biCharSet.iteritems():
        p = transMat[clus][index]/priorMat[clus][charSet[ch1]]
        #try:
        fact += p*log(p)
        #except:
        #    print transMat[clus][index], priorMat[clus][charSet[ch1]], ch1, ch2
        #    sys.exit()
        
    return fact
    
def getChangeInMorph(wordToBeShifted, origClass, tempNewClass):
    
    deltaMorph = 0.0
    uniqBiGrams = Counter()
    uniqUniGrams = Counter()
    
    w = wordToBeShifted
    
    for i, ch2 in enumerate(w[1:]):
    
        i = i+1
        ch1 = w[i-1]
    
        pOldOrig = transMat[origClass][biCharSet[(ch1, ch2)]]/priorMat[origClass][charSet[ch1]]
        pNewOrig = (transMat[origClass][biCharSet[(ch1, ch2)]]-1)/(priorMat[origClass][charSet[ch1]]-1)
        #Changes to the new cluster
        pOldNew = transMat[tempNewClass][biCharSet[(ch1, ch2)]]/priorMat[tempNewClass][charSet[ch1]]
        pNewNew = (transMat[tempNewClass][biCharSet[(ch1, ch2)]]+1)/(priorMat[tempNewClass][charSet[ch1]]+1)
        #Removing old effects of both clusters
        deltaMorph += pOldOrig*log(pOldOrig)
        deltaMorph += pOldNew*log(pOldNew)
        #Adding new effects of both clusters
        deltaMorph -= pOldNew*log(pOldNew)
        deltaMorph -= pNewNew*log(pNewNew)
        
    return deltaMorph
    
    for i, ch in enumerate(wordToBeShifted):
        if i > 0:
            if (wordToBeShifted[i-1], ch) not in uniqBiGrams:
                uniqBiGrams[(wordToBeShifted[i-1], ch)] += 1
        if ch not in uniqUniGrams:
            uniqUniGrams[ch] += 1
            
    uniqUniGrams['<w>'] += 1
    uniqUniGrams['</w>'] += 1        
    uniqBiGrams[('<w>', wordToBeShifted[0])] = 1
    uniqBiGrams[(wordToBeShifted[len(wordToBeShifted)-1], '</w>')] = 1
    
    #for (ch1, ch2) in uniqBiGrams.iterkeys():
    
    #    pOldOrig = transMat[origClass][biCharSet[(ch1, ch2)]]/priorMat[origClass][charSet[ch1]]
    #    pNewOrig = (transMat[origClass][biCharSet[(ch1, ch2)]]-uniqBiGrams[(ch1, ch2)])/(priorMat[origClass][charSet[ch1]]-uniqUniGrams[ch1])
    #    #Changes to the new cluster
    #    pOldNew = transMat[tempNewClass][biCharSet[(ch1, ch2)]]/priorMat[tempNewClass][charSet[ch1]]
    #    pNewNew = (transMat[tempNewClass][biCharSet[(ch1, ch2)]]+uniqBiGrams[(ch1, ch2)])/(priorMat[tempNewClass][charSet[ch1]]+uniqUniGrams[ch1])
    #    #Removing old effects of both clusters
    #    deltaMorph += pOldOrig*log(pOldOrig)
    #    deltaMorph += pOldNew*log(pOldNew)
    #    #Adding new effects of both clusters
    #    deltaMorph -= pOldNew*log(pOldNew)
    #    deltaMorph -= pNewNew*log(pNewNew)
        
    #return deltaMorph
    
    for (ch1, ch2) in biCharSet.iterkeys():
        
        if ch1 in uniqUniGrams and (ch1, ch2) in uniqBiGrams:
            #Changes to the old cluster
            pOldOrig = transMat[origClass][biCharSet[(ch1, ch2)]]/priorMat[origClass][charSet[ch1]]
            pNewOrig = (transMat[origClass][biCharSet[(ch1, ch2)]]-uniqBiGrams[(ch1, ch2)])/(priorMat[origClass][charSet[ch1]]-uniqUniGrams[ch1])
            #Changes to the new cluster
            pOldNew = transMat[tempNewClass][biCharSet[(ch1, ch2)]]/priorMat[tempNewClass][charSet[ch1]]
            pNewNew = (transMat[tempNewClass][biCharSet[(ch1, ch2)]]+uniqBiGrams[(ch1, ch2)])/(priorMat[tempNewClass][charSet[ch1]]+uniqUniGrams[ch1])
            #Removing old effects of both clusters
            deltaMorph += pOldOrig*log(pOldOrig)
            deltaMorph += pOldNew*log(pOldNew)
            #Adding new effects of both clusters
            deltaMorph -= pOldNew*log(pOldNew)
            deltaMorph -= pNewNew*log(pNewNew)
            
        elif ch1 in uniqUniGrams:
            #Changes to the old cluster
            pOldOrig = transMat[origClass][biCharSet[(ch1, ch2)]]/priorMat[origClass][charSet[ch1]]
            pNewOrig = transMat[origClass][biCharSet[(ch1, ch2)]]/(priorMat[origClass][charSet[ch1]]-uniqUniGrams[ch1])
            #Changes to the new cluster
            pOldNew = transMat[tempNewClass][biCharSet[(ch1, ch2)]]/priorMat[tempNewClass][charSet[ch1]]
            pNewNew = transMat[tempNewClass][biCharSet[(ch1, ch2)]]/(priorMat[tempNewClass][charSet[ch1]]+uniqUniGrams[ch1])
            #Removing old effects of both clusters
            deltaMorph += pOldOrig*log(pOldOrig)
            deltaMorph += pOldNew*log(pOldNew)
            #Adding new effects of both clusters
            deltaMorph -= pOldNew*log(pOldNew)
            deltaMorph -= pNewNew*log(pNewNew)
       
    return deltaMorph
    
def updateMorphData(wordToBeShifted, origClass, tempNewClass):
    
    for i, ch in enumerate(wordToBeShifted):
        if i > 0:
            transMat[origClass][biCharSet[(wordToBeShifted[i-1], ch)]] -= 1
            transMat[tempNewClass][biCharSet[(wordToBeShifted[i-1], ch)]] += 1
            
        if priorMat[origClass][charSet[ch]] > 1:
            priorMat[origClass][charSet[ch]] -= 1
        priorMat[tempNewClass][charSet[ch]] += 1
    
    priorMat[origClass][charSet['<w>']] -= 1
    priorMat[origClass][charSet['</w>']] -= 1
    priorMat[tempNewClass][charSet['<w>']] += 1
    priorMat[tempNewClass][charSet['</w>']] += 1
            
    transMat[origClass][biCharSet[('<w>', wordToBeShifted[0])]] -= 1
    transMat[origClass][biCharSet[(wordToBeShifted[len(wordToBeShifted)-1], '</w>')]] -= 1
    transMat[tempNewClass][biCharSet[('<w>', wordToBeShifted[0])]] += 1
    transMat[tempNewClass][biCharSet[(wordToBeShifted[len(wordToBeShifted)-1], '</w>')]] += 1
    
    return