import numpypy
import numpy as np
from math import log
from collections import Counter
from operator import itemgetter
import sys

class Morphology:
    
    def __init__(self, lang, morphWeight):
    
        self.transMat = None
        self.priorMat = None
    
        self.charSet = {}
        self.biCharSet = {}
        self.uniToBi = {}
        
        self.lang = lang
        self.weight = morphWeight
        self.suffixLen = 4

        self.makeTransitionProbMatrix()
        
        return
    
    def makeTransitionProbMatrix(self):
    
        self.charSet = {'<w>':0, '</w>':1}
        index1 = 2
        index2 = 0
        for word in self.lang.wordDict.iterkeys():
            
            if len(word) <=  self.suffixLen:
                continue
            else:
                word = word[len(word)- self.suffixLen:]
                
            prevCh = '<w>'
            for ch in word:
                if ch not in self.charSet:
                    self.charSet[ch] = index1
                    index1 += 1
                    
                if prevCh not in self.uniToBi:
                    self.uniToBi[prevCh] = []
                    
                if (prevCh, ch) not in self.biCharSet:
                    self.biCharSet[(prevCh, ch)] = index2
                    index2 += 1
                    
                    self.uniToBi[prevCh].append(ch)
                    
                prevCh = ch
                
            if (ch, '</w>') not in self.biCharSet:
                self.biCharSet[(ch, '</w>')] = index2
                index2 += 1
            
            if ch not in self.uniToBi:
                self.uniToBi[ch] = ['</w>']
            elif '</w>' not in self.uniToBi[ch]:
                self.uniToBi[ch].append('</w>')
        
        assert len(self.biCharSet) == index2
        assert len(self.charSet) == index1
        assert len(self.biCharSet) == sum(len(self.uniToBi[ch]) for ch in self.uniToBi.keys())
                
        numChar = len(self.charSet)
        numBiChar = len(self.biCharSet)
        numClus = len(self.lang.wordsInClusDict)
        
        self.transMat = np.ones((numClus, numBiChar))
        self.priorMat = np.ones((numClus, numChar))
    
        for clus, wordList in self.lang.wordsInClusDict.iteritems():
            for word in wordList:
                
                if len(word) <=  self.suffixLen:
                    continue
                else:
                    word = word[len(word)- self.suffixLen:]
            
                self.transMat[clus][self.biCharSet[('<w>', word[0])]] += 1.0
                self.priorMat[clus][self.charSet['<w>']] += 1.0
            
                for i, ch in enumerate(word):
                    if i != 0:
                        self.transMat[clus][self.biCharSet[(word[i-1], ch)]] += 1.0
                    self.priorMat[clus][self.charSet[ch]] += 1.0
                    
                self.transMat[clus][self.biCharSet[(ch, '</w>')]] += 1.0
                self.priorMat[clus][self.charSet['</w>']] += 1.0
            
        return
    
    def getClusMorphFactor(self, clus):
    
        fact = 0.0
    
        for (ch1, ch2), index in self.biCharSet.iteritems():
            p = self.transMat[clus][index]/self.priorMat[clus][self.charSet[ch1]]
            fact += p*log(p)
        
        return self.weight*fact/self.lang.numClusters
    
    def getChangeInMorph(self, wordToBeShifted, origClass, tempNewClass):
        
        if self.weight == 0:
            return 0.0
        
        deltaMorph = 0.0
        uniqBiGrams = Counter()
        uniqUniGrams = Counter()
    
        if len(wordToBeShifted) <= self.suffixLen:
            return 0.0
        else:
            wordToBeShifted = wordToBeShifted[len(wordToBeShifted)- self.suffixLen:]
    
        for i, ch in enumerate(wordToBeShifted):
            if i > 0:
                if (wordToBeShifted[i-1], ch) not in uniqBiGrams:
                    uniqBiGrams[(wordToBeShifted[i-1], ch)] += 1
                if ch not in uniqUniGrams:
                    uniqUniGrams[ch] += 1
            
        uniqUniGrams['<w>'] = 1
        uniqUniGrams['</w>'] = 1        
        uniqBiGrams[('<w>', wordToBeShifted[0])] = 1
        uniqBiGrams[(wordToBeShifted[len(wordToBeShifted)-1], '</w>')] = 1
        
        for ch1 in uniqUniGrams.iterkeys():
            if ch1 in self.uniToBi:
                for ch2 in self.uniToBi[ch1]:
                    if (ch1, ch2) in uniqBiGrams:
                        #Changes to the old cluster
                        pOldOrig = self.transMat[origClass][self.biCharSet[(ch1, ch2)]]/self.priorMat[origClass][self.charSet[ch1]]
                        pNewOrig = (self.transMat[origClass][self.biCharSet[(ch1, ch2)]]-uniqBiGrams[(ch1, ch2)])/(self.priorMat[origClass][self.charSet[ch1]]-uniqUniGrams[ch1])
                        #Changes to the new cluster
                        pOldNew = self.transMat[tempNewClass][self.biCharSet[(ch1, ch2)]]/self.priorMat[tempNewClass][self.charSet[ch1]]
                        pNewNew = (self.transMat[tempNewClass][self.biCharSet[(ch1, ch2)]]+uniqBiGrams[(ch1, ch2)])/(self.priorMat[tempNewClass][self.charSet[ch1]]+uniqUniGrams[ch1])
                        #Removing old effects of both clusters
                        deltaMorph += pOldOrig*log(pOldOrig)
                        deltaMorph += pOldNew*log(pOldNew)
                        #Adding new effects of both clusters
                        deltaMorph -= pOldNew*log(pOldNew)
                        deltaMorph -= pNewNew*log(pNewNew)
                    else:
                        #Changes to the old cluster
                        pOldOrig = self.transMat[origClass][self.biCharSet[(ch1, ch2)]]/self.priorMat[origClass][self.charSet[ch1]]
                        pNewOrig = self.transMat[origClass][self.biCharSet[(ch1, ch2)]]/(self.priorMat[origClass][self.charSet[ch1]]-uniqUniGrams[ch1])
                        #Changes to the new cluster
                        pOldNew = self.transMat[tempNewClass][self.biCharSet[(ch1, ch2)]]/self.priorMat[tempNewClass][self.charSet[ch1]]
                        pNewNew = self.transMat[tempNewClass][self.biCharSet[(ch1, ch2)]]/(self.priorMat[tempNewClass][self.charSet[ch1]]+uniqUniGrams[ch1])
                        #Removing old effects of both clusters
                        deltaMorph += pOldOrig*log(pOldOrig)
                        deltaMorph += pOldNew*log(pOldNew)
                        #Adding new effects of both clusters
                        deltaMorph -= pOldNew*log(pOldNew)
                        deltaMorph -= pNewNew*log(pNewNew)
                        
        return self.weight*deltaMorph/self.lang.numClusters
    
    def updateMorphData(self, wordToBeShifted, origClass, tempNewClass):
        
        if self.weight == 0:
            return
        
        if len(wordToBeShifted) <= self.suffixLen:
            return
        else:
            wordToBeShifted = wordToBeShifted[len(wordToBeShifted)- self.suffixLen:]
    
        for i, ch in enumerate(wordToBeShifted):
            if i > 0:
                self.transMat[origClass][self.biCharSet[(wordToBeShifted[i-1], ch)]] -= 1
                self.transMat[tempNewClass][self.biCharSet[(wordToBeShifted[i-1], ch)]] += 1
            
            self.priorMat[origClass][self.charSet[ch]] -= 1
            self.priorMat[tempNewClass][self.charSet[ch]] += 1
    
        self.priorMat[origClass][self.charSet['<w>']] -= 1
        self.priorMat[origClass][self.charSet['</w>']] -= 1
        self.priorMat[tempNewClass][self.charSet['<w>']] += 1
        self.priorMat[tempNewClass][self.charSet['</w>']] += 1
            
        self.transMat[origClass][self.biCharSet[('<w>', wordToBeShifted[0])]] -= 1
        self.transMat[origClass][self.biCharSet[(wordToBeShifted[len(wordToBeShifted)-1], '</w>')]] -= 1
        self.transMat[tempNewClass][self.biCharSet[('<w>', wordToBeShifted[0])]] += 1
        self.transMat[tempNewClass][self.biCharSet[(wordToBeShifted[len(wordToBeShifted)-1], '</w>')]] += 1
    
        return