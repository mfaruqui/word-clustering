import sys
from collections import Counter
from operator import itemgetter

class CommonInLangPair:
    
    def __init__(self, alignDict, lang1, lang2):
        
        self.sumAllAlignLinks = 0.0
        self.alignDict = {}
        self.alignedWordsInClusPairDict = {}
        self.sumAlignedWordsInClusPairDict = Counter()
        
        self.first = lang1
        self.second = lang2
    
        for (w_en, w_fr), val in alignDict.iteritems():
            
            if w_en in self.first.considerForBi and w_fr in self.second.considerForBi:
                self.alignDict[(w_en, w_fr)] = val
                self.sumAllAlignLinks += 1.0*val
        
        #print len(alignDict), len(set([w_en for (w_en, w_fr), val in alignDict.iteritems()])),\
        #len(set([w_fr for (w_en, w_fr), val in alignDict.iteritems()]))
        self.initializeAlignedWordPairsSum()
        
        return 
            
    def initializeAlignedWordPairsSum(self):
    
        for (w_en, w_fr) in self.alignDict.iterkeys():
            c_en = self.first.wordToClusDict[w_en]
            c_fr = self.second.wordToClusDict[w_fr]
            
            if (c_en, c_fr) in self.alignedWordsInClusPairDict:
                self.alignedWordsInClusPairDict[(c_en, c_fr)].append((w_en, w_fr))
            else:
                self.alignedWordsInClusPairDict[(c_en, c_fr)] = [(w_en, w_fr)]
            
            self.sumAlignedWordsInClusPairDict[(c_en, c_fr)] += self.alignDict[(w_en, w_fr)]
            
        return
        
    def printSumMatrix(self):
        
        print ''
        
        for (c_en, c_fr), val in self.sumAlignedWordsInClusPairDict.iteritems():
            if val != 0:
                print c_en, c_fr, val
            
        return