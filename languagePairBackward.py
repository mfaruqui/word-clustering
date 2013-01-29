import sys
from operator import itemgetter
from math import log

class LanguagePairBackward:
    
    def __init__(self, fromObj, toObj, commonObj):
        
        self.wordToWordAlignedDict = {}
        self.edgeSumInClus = {}
        self.wordAlignedClusDict = {}
        self.clusAlignedClusDict = {} 
        self.wordToClusCount = {}
        self.wordEdgeCount = {}
        self.reverse = None
        
        self.first = fromObj
        self.second = toObj
        self.common = commonObj
        
        self.getWordAlignment()
        self.getInitialEgdeSumInCluster()
        self.getInitialWordAlignedClasses()
        self.getInitialClassAlignedClasses()
        self.getInitialWordAlignedClusCount()
        self.getWordEdgeCount()
        
        sys.stderr.write("\nFinished making the backward lang pair object")
        
        return
        
    def assignReverseLanguagePair(self, reverseLangPair):
        
        self.reverse = reverseLangPair
            
    def getWordAlignment(self):
        
        for (w_en, w_fr) in self.common.alignDict:
            if w_fr not in self.wordToWordAlignedDict:
                self.wordToWordAlignedDict[w_fr] = [w_en]
            else:
                self.wordToWordAlignedDict[w_fr].append(w_en)
                
        return
        
    def getInitialEgdeSumInCluster(self):
        
        for c_fr, frWordList in self.first.wordsInClusDict.iteritems():
            self.edgeSumInClus[c_fr] = 0.0
            for w_fr in frWordList:
                if w_fr in self.wordToWordAlignedDict:
                    for w_en in self.wordToWordAlignedDict[w_fr]:
                        self.edgeSumInClus[c_fr] += self.common.alignDict[(w_en, w_fr)]
                    
        return
                        
    def getInitialWordAlignedClasses(self):
        
        for w_fr, enWordList in self.wordToWordAlignedDict.iteritems():
            self.wordAlignedClusDict[w_fr] = []
            for w_en in enWordList:
                c_en = self.second.wordToClusDict[w_en]
                if c_en not in self.wordAlignedClusDict[w_fr]:
                    self.wordAlignedClusDict[w_fr].append(c_en)
                
        return
                    
    def getInitialClassAlignedClasses(self):
        
        for c_fr in self.first.clusUniCount.iterkeys():
            self.clusAlignedClusDict[c_fr] = []
            for w_fr in self.first.wordsInClusDict[c_fr]:
                if w_fr in self.wordToWordAlignedDict:
                    for w_en in self.wordToWordAlignedDict[w_fr]:
                        c_en = self.second.wordToClusDict[w_en]
                        if c_en not in self.clusAlignedClusDict[c_fr]:
                            self.clusAlignedClusDict[c_fr].append(c_en)
    
        return
        
    def getInitialWordAlignedClusCount(self):
    
        for w_fr, enWordList in self.wordToWordAlignedDict.iteritems():
            for w_en in enWordList:
                c_en = self.second.wordToClusDict[w_en]
                if (w_fr, c_en) in self.wordToClusCount:
                    self.wordToClusCount[(w_fr, c_en)] += self.common.alignDict[(w_en, w_fr)]
                else:
                    self.wordToClusCount[(w_fr, c_en)] = self.common.alignDict[(w_en, w_fr)]
            
        return
    
    def getWordEdgeCount(self):
    
        for (w_fr, c_en), val in self.wordToClusCount.iteritems():
            if w_fr in self.wordEdgeCount:
                self.wordEdgeCount[w_fr] += val
            else:
                self.wordEdgeCount[w_fr] = val
        
        return
            
    def getAlignedClasses(self, fromClass):
    
         alignedClasses = []
         for word in self.first.wordsInClusDict[fromClass]:
             if word in self.wordToWordAlignedDict:
                 for alignedWord in self.wordToWordAlignedDict[word]:
                     c = self.second.wordToClusDict[alignedWord]
                     if c not in alignedClasses:
                         alignedClasses.append(c)
            
         return alignedClasses
         
    def getShiftedWordAlignedCount(self, word, alignedClus):
    
        count = 0
        for alignedWord in self.wordToWordAlignedDict[word]:
            c = self.second.wordToClusDict[alignedWord]
            if c == alignedClus:
                count += self.common.alignDict[(alignedWord, word)]
            
        return count
        
    def getWordAlignedClasses(self, wordToBeShifted):
    
        wordAlignedClasses = []
        if wordToBeShifted in self.wordToWordAlignedDict:
            for alignedWord in self.wordToWordAlignedDict[wordToBeShifted]:
                c = self.second.wordToClusDict[alignedWord]
                if c not in wordAlignedClasses:
                    wordAlignedClasses.append(c)
                
        return wordAlignedClasses
         
    def updateDistribution(self, wordToBeShifted, origClass, newClass):
        
        if wordToBeShifted in self.wordToWordAlignedDict:
           
            seenClus = []
            self.edgeSumInClus[origClass] -= self.wordEdgeCount[wordToBeShifted]
            self.edgeSumInClus[newClass] += self.wordEdgeCount[wordToBeShifted]
           
            for w_en in self.wordToWordAlignedDict[wordToBeShifted]:
               
                c_en = self.second.wordToClusDict[w_en]
                self.common.alignedWordsInClusPairDict[(c_en, origClass)].remove((w_en, wordToBeShifted))
                
                if (c_en, newClass) in self.common.alignedWordsInClusPairDict:
                    self.common.alignedWordsInClusPairDict[(c_en, newClass)].append((w_en, wordToBeShifted))
                else:
                    self.common.alignedWordsInClusPairDict[(c_en, newClass)] = [(w_en, wordToBeShifted)]
               
                if c_en not in seenClus:
                    
                    seenClus.append(c_en)
                    sumCountShiftedWordAligned = self.getShiftedWordAlignedCount(wordToBeShifted, c_en)
                    self.common.sumAlignedWordsInClusPairDict[(c_en, origClass)] -= sumCountShiftedWordAligned
                    self.common.sumAlignedWordsInClusPairDict[(c_en, newClass)] += sumCountShiftedWordAligned
                    
                    self.reverse.clusAlignedClusDict[c_en] = self.reverse.getAlignedClasses(c_en)
                
                # Re-compute the frWordAlignedClusDict for all words that were aligned to this word
                self.reverse.wordAlignedClusDict[w_en] = self.reverse.getWordAlignedClasses(w_en)
                self.reverse.wordToClusCount[(w_en, origClass)] -= self.common.alignDict[(w_en, wordToBeShifted)]
                if (w_en, newClass) in self.reverse.wordToClusCount:
                    self.reverse.wordToClusCount[(w_en, newClass)] += self.common.alignDict[(w_en, wordToBeShifted)]
                else:
                    self.reverse.wordToClusCount[(w_en, newClass)] = self.common.alignDict[(w_en, wordToBeShifted)]
               
            self.clusAlignedClusDict[origClass] = self.getAlignedClasses(origClass)
            self.clusAlignedClusDict[newClass] = self.getAlignedClasses(newClass)
            
            del seenClus   
        
        return
            
    def calcTentativePerplex(self, wordToBeShifted, origClass, tempNewClass):
        
        deltaBi = 0.0
        
        if wordToBeShifted in self.wordToWordAlignedDict:
        
            alignedClasses = self.clusAlignedClusDict[origClass]
            wordAlignedClasses = self.wordAlignedClusDict[wordToBeShifted]
            
            for alignedClass in alignedClasses:
                
                # The wordToBeShifted might or might not be connected to the alignedClass
                if (wordToBeShifted, alignedClass) in self.wordToClusCount:
                    sumCountShiftedWordAligned = self.wordToClusCount[(wordToBeShifted, alignedClass)]
                else:
                    sumCountShiftedWordAligned = 0.0
                
                sumCountPair = self.common.sumAlignedWordsInClusPairDict[(alignedClass, origClass)]
            
                old_px = self.edgeSumInClus[origClass]/self.common.sumAllAlignLinks
                old_py = self.reverse.edgeSumInClus[alignedClass]/self.common.sumAllAlignLinks
                old_pxy = sumCountPair/self.common.sumAllAlignLinks
            
                new_px = (self.edgeSumInClus[origClass] - self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                new_py = old_py
                new_pxy = (sumCountPair - sumCountShiftedWordAligned)/self.common.sumAllAlignLinks
                
                deltaBi += old_pxy*log(old_pxy/old_px) + old_pxy*log(old_pxy/old_py)
                    
                if new_pxy != 0:
                    deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
            # Adding effects due to moving to a new class
            alignedClasses = self.clusAlignedClusDict[tempNewClass]
        
            for alignedClass in alignedClasses:
            
                if (wordToBeShifted, alignedClass) in self.wordToClusCount:
                    sumCountShiftedWordAligned = self.wordToClusCount[(wordToBeShifted, alignedClass)]
                else:
                    sumCountShiftedWordAligned = 0.0
                    
                sumCountPair = self.common.sumAlignedWordsInClusPairDict[(alignedClass, tempNewClass)]
            
                old_px = self.edgeSumInClus[tempNewClass]/self.common.sumAllAlignLinks
                old_py = self.reverse.edgeSumInClus[alignedClass]/self.common.sumAllAlignLinks
                old_pxy = sumCountPair/self.common.sumAllAlignLinks
            
                deltaBi += old_pxy*log(old_pxy/old_px) + old_pxy*log(old_pxy/old_py)
            
                new_px = (self.edgeSumInClus[tempNewClass] + self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                new_py = old_py
                new_pxy = (sumCountPair + sumCountShiftedWordAligned)/self.common.sumAllAlignLinks
                
                deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
            
            # New classes will be aligned to tempNewClass now because of connections of wordToBeShifted          
            for alignedClass in wordAlignedClasses:
           
                if alignedClass not in alignedClasses:
                    
                    sumCountShiftedWordAligned = self.wordToClusCount[(wordToBeShifted, alignedClass)]
                    
                    new_px = (self.edgeSumInClus[tempNewClass] + self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                    new_py = self.reverse.edgeSumInClus[alignedClass]/self.common.sumAllAlignLinks
                    new_pxy = sumCountShiftedWordAligned/self.common.sumAllAlignLinks
                    
                    deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
        return deltaBi