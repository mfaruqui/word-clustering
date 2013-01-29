import sys
from collections import Counter
from operator import itemgetter

class CommonInLangPair:
    
    def __init__(self, alignDict, lang1, lang2, edgeThresh):
        
        self.sumAllAlignLinks = 0.0
        self.edgeThresh = edgeThresh
        self.alignDict = {}
        self.alignedWordsInClusPairDict = {}
        self.sumAlignedWordsInClusPairDict = Counter()
        
        self.first = lang1
        self.second = lang2
        
        tempL1 = Counter()
        tempL2 = Counter()
        #enDict = {}
        #frDict = {}
        
        for (w_en, w_fr), val in alignDict.iteritems():
            
            #if w_en in self.first.considerForBi and w_fr in self.second.considerForBi:
            self.alignDict[(w_en, w_fr)] = val
            self.sumAllAlignLinks += 1.0*val
            
            tempL1[w_en] += 1.0*val
            tempL2[w_fr] += 1.0*val
            
        sys.stderr.write('\n'+str(len(self.alignDict))+'\n')
        
        for (w_en, w_fr), count in alignDict.iteritems():
            importance = 2*count/(tempL1[w_en]+tempL2[w_fr])
            if importance < self.edgeThresh:
                self.sumAllAlignLinks -= self.alignDict[(w_en, w_fr)]
                del self.alignDict[(w_en, w_fr)]
        
        sys.stderr.write(str(len(self.alignDict))+'\n')
        self.initializeAlignedWordPairsSum()
        sys.stderr.write("\nFinished making the common lang pair object")
        
        del tempL1, tempL2
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