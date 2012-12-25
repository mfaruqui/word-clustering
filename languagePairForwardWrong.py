import sys
from operator import itemgetter
from math import log

class LanguagePairForward:
    
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
        
        return
        
    def assignReverseLanguagePair(self, reverseLangPair):
        
        self.reverse = reverseLangPair
        
    def getWordAlignment(self):
        
        for (w_en, w_fr) in self.common.alignDict:
            if w_en not in self.wordToWordAlignedDict:
                self.wordToWordAlignedDict[w_en] = [w_fr]
            else:
                self.wordToWordAlignedDict[w_en].append(w_fr)
                
        return
        
    def getInitialEgdeSumInCluster(self):
        
        for c_en, enWordList in self.first.wordsInClusDict.iteritems():
            self.edgeSumInClus[c_en] = 0.0
            for w_en in enWordList:
                if w_en in self.wordToWordAlignedDict:
                    for w_fr in self.wordToWordAlignedDict[w_en]:
                        self.edgeSumInClus[c_en] += self.common.alignDict[(w_en, w_fr)]
                    
        return
                        
    def getInitialWordAlignedClasses(self):
        
        for w_en, frWordList in self.wordToWordAlignedDict.iteritems():
            self.wordAlignedClusDict[w_en] = []
            for w_fr in frWordList:
                c_fr = self.second.wordToClusDict[w_fr]
                if c_fr not in self.wordAlignedClusDict[w_en]:
                    self.wordAlignedClusDict[w_en].append(c_fr)
                
        return
                    
    def getInitialClassAlignedClasses(self):
        
        for c_en in self.first.clusUniCount.iterkeys():
            self.clusAlignedClusDict[c_en] = []
            for w_en in self.first.wordsInClusDict[c_en]:
                if w_en in self.wordToWordAlignedDict:
                    for w_fr in self.wordToWordAlignedDict[w_en]:
                        c_fr = self.second.wordToClusDict[w_fr]
                        if c_fr not in self.clusAlignedClusDict[c_en]:
                            self.clusAlignedClusDict[c_en].append(c_fr)
    
        return
        
    def getInitialWordAlignedClusCount(self):
    
        for w_en, frWordList in self.wordToWordAlignedDict.iteritems():
            for w_fr in frWordList:
                c_fr = self.second.wordToClusDict[w_fr]
                if (w_en, c_fr) in self.wordToClusCount:
                    self.wordToClusCount[(w_en, c_fr)] += self.common.alignDict[(w_en, w_fr)]
                else:
                    self.wordToClusCount[(w_en, c_fr)] = self.common.alignDict[(w_en, w_fr)]
            
        return
    
    def getWordEdgeCount(self):
    
        for (w_en, c_fr), val in self.wordToClusCount.iteritems():
            if w_en in self.wordEdgeCount:
                self.wordEdgeCount[w_en] += val
            else:
                self.wordEdgeCount[w_en] = val
        
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
                count += self.common.alignDict[(word, alignedWord)]
            
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
        
        if self.wordToWordAlignedDict.has_key(wordToBeShifted):
           
            seenClus = []
            self.edgeSumInClus[origClass] -= self.wordEdgeCount[wordToBeShifted]
            self.edgeSumInClus[newClass] += self.wordEdgeCount[wordToBeShifted]
           
            for w_fr in self.wordToWordAlignedDict[wordToBeShifted]:
               
                c_fr = self.second.wordToClusDict[w_fr]
                self.common.alignedWordsInClusPairDict[(origClass, c_fr)].remove((wordToBeShifted, w_fr))
                
                if (newClass, c_fr) in self.common.alignedWordsInClusPairDict:
                    self.common.alignedWordsInClusPairDict[(newClass, c_fr)].append((wordToBeShifted, w_fr))
                else:
                    self.common.alignedWordsInClusPairDict[(newClass, c_fr)] = [(wordToBeShifted, w_fr)]
               
                if c_fr not in seenClus:
                   
                    seenClus.append(c_fr)
                    sumCountShiftedWordAligned = self.getShiftedWordAlignedCount(wordToBeShifted, c_fr)
                    self.common.sumAlignedWordsInClusPairDict[(origClass, c_fr)] -= sumCountShiftedWordAligned
                    self.common.sumAlignedWordsInClusPairDict[(newClass, c_fr)] += sumCountShiftedWordAligned
                    
                    self.reverse.clusAlignedClusDict[c_fr] = self.reverse.getAlignedClasses(c_fr)
                       
                # Re-compute the frWordAlignedClusDict for all words that were aligned to this word
                self.reverse.wordAlignedClusDict[w_fr] = self.reverse.getWordAlignedClasses(w_fr)
                self.reverse.wordToClusCount[(w_fr, origClass)] -= self.common.alignDict[(wordToBeShifted, w_fr)]
                if (w_fr, newClass) in self.reverse.wordToClusCount:
                    self.reverse.wordToClusCount[(w_fr, newClass)] += self.common.alignDict[(wordToBeShifted, w_fr)]
                else:
                    self.reverse.wordToClusCount[(w_fr, newClass)] = self.common.alignDict[(wordToBeShifted, w_fr)]
               
            self.clusAlignedClusDict[origClass] = self.getAlignedClasses(origClass)
            self.clusAlignedClusDict[newClass] = self.getAlignedClasses(newClass)
            
            del seenClus   
            
        return
            
    def calcTentativePerplex(self, wordToBeShifted, origClass, tempNewClass):
        
        deltaBi = 0.0
        
        if wordToBeShifted in self.wordToWordAlignedDict:
            
            print ''
            print wordToBeShifted
        
            alignedClasses = self.clusAlignedClusDict[origClass]
            wordAlignedClasses = self.wordAlignedClusDict[wordToBeShifted]
        
            for alignedClass in wordAlignedClasses:
            
                sumCountShiftedWordAligned = self.wordToClusCount[(wordToBeShifted, alignedClass)]
                sumCountPair = self.common.sumAlignedWordsInClusPairDict[(origClass, alignedClass)]
            
                old_px = self.edgeSumInClus[origClass]/self.common.sumAllAlignLinks
                old_py = self.reverse.edgeSumInClus[alignedClass]/self.common.sumAllAlignLinks
                old_pxy = sumCountPair/self.common.sumAllAlignLinks
            
                new_px = (self.edgeSumInClus[origClass] - self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                new_py = old_py
                new_pxy = (sumCountPair - sumCountShiftedWordAligned)/self.common.sumAllAlignLinks
                
                deltaBi += old_pxy*log(old_pxy/old_px) + old_pxy*log(old_pxy/old_py)
                print "A", "R", origClass, alignedClass
                #print "A1:", deltaBi
                    
                if new_pxy != 0:
                    print "A","M", origClass, alignedClass
                    deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
                    #print "A:", deltaBi
                
            for alignedClass in alignedClasses:
            
                if alignedClass not in wordAlignedClasses:
                
                    sumCountPair = self.common.sumAlignedWordsInClusPairDict[(origClass, alignedClass)]
                
                    old_px = self.edgeSumInClus[origClass]/self.common.sumAllAlignLinks
                    old_py = self.reverse.edgeSumInClus[alignedClass]/self.common.sumAllAlignLinks
                    old_pxy = sumCountPair/self.common.sumAllAlignLinks
            
                    new_px = (self.edgeSumInClus[origClass] - self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                    new_py = old_py
                    new_pxy = old_pxy
                    
                    print "B","R", origClass, alignedClass
                    print "B","M", origClass, alignedClass
                    deltaBi += old_pxy*log(old_pxy/old_px) #+ old_pxy*log(old_pxy/old_py)
                    deltaBi -= new_pxy*log(new_pxy/new_px) #+ new_pxy*log(new_pxy/new_py)
                    
                    #print "B:", deltaBi
                    
            # Adding effects due to moving to a new class
            alignedClasses = self.clusAlignedClusDict[tempNewClass]
        
            for alignedClass in alignedClasses:
            
                sumCountPair = self.common.sumAlignedWordsInClusPairDict[(tempNewClass, alignedClass)]
                if (wordToBeShifted, alignedClass) in self.wordToClusCount:
                    sumCountShiftedWordAligned = self.wordToClusCount[(wordToBeShifted, alignedClass)]
                else:
                    sumCountShiftedWordAligned = 0.0
            
                old_px = self.edgeSumInClus[tempNewClass]/self.common.sumAllAlignLinks
                old_py = self.reverse.edgeSumInClus[alignedClass]/self.common.sumAllAlignLinks
                old_pxy = sumCountPair/self.common.sumAllAlignLinks
            
                print "C","R", origClass, alignedClass
                deltaBi += old_pxy*log(old_pxy/old_px) + old_pxy*log(old_pxy/old_py)
                #print "C1:", deltaBi
            
                if alignedClass not in wordAlignedClasses:
               
                   new_px = (self.edgeSumInClus[tempNewClass] + self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                   new_py = old_py
                   new_pxy = old_pxy
                   
                   print "C","M", origClass, alignedClass   
                   deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                   
                   #print "C:", deltaBi
                   
                if alignedClass in wordAlignedClasses:
                
                    new_px = (self.edgeSumInClus[tempNewClass] + self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                    new_py = old_py
                    new_pxy = (sumCountPair + sumCountShiftedWordAligned)/self.common.sumAllAlignLinks
                
                    print "D","M", origClass, alignedClass
                    deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
                    #print "D:", deltaBi
                
            for alignedClass in wordAlignedClasses:
           
                sumCountShiftedWordAligned = self.wordToClusCount[(wordToBeShifted, alignedClass)]
            
                if alignedClass not in alignedClasses:
                    
                    new_px = (self.edgeSumInClus[tempNewClass] + self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                    new_py = self.reverse.edgeSumInClus[alignedClass]/self.common.sumAllAlignLinks
                    new_pxy = sumCountShiftedWordAligned/self.common.sumAllAlignLinks
                    
                    # You have already removed the old effect earlier now, just add the new effect 
                    print "E","M", origClass, alignedClass
                    deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
                    #print "E:", deltaBi
                    
                elif alignedClass in alignedClasses:
                
                    sumCountPair = self.common.sumAlignedWordsInClusPairDict[(tempNewClass, alignedClass)]
                
                    new_px = (self.edgeSumInClus[tempNewClass] + self.wordEdgeCount[wordToBeShifted])/self.common.sumAllAlignLinks
                    new_py = self.reverse.edgeSumInClus[alignedClass]/self.common.sumAllAlignLinks
                    new_pxy = (sumCountPair + sumCountShiftedWordAligned)/self.common.sumAllAlignLinks
                    
                    print "F","M", origClass, alignedClass
                    deltaBi -= new_pxy*log(new_pxy/new_px) + new_pxy*log(new_pxy/new_py)
                    
                    #print "F:", deltaBi
                    
        return deltaBi