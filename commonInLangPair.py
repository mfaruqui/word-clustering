import sys
from collections import Counter

class CommonInLangPair:
    
    def __init__(self, alignDict, lang1, lang2):
        
        self.sumAllAlignLinks = 0.0
        self.alignDict = {}#Counter()
        self.alignedWordsInClusPairDict = {}
        self.sumAlignedWordsInClusPairDict = Counter()
        
        self.first = lang1
        self.second = lang2
    
        for key, val in alignDict.iteritems():
            self.alignDict[key] = val
            self.sumAllAlignLinks += 1.0*val
            
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