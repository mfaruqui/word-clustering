from math import log
from operator import itemgetter
import string
import sys
USE_ALL_WORDS = -1

def nlogn(x):
    if x == 0:
        return x
    else:
        return x * log(x)

class Language:
    
    def __init__(self, wDict, bigramDict, numClusInit, typeClusInit):
        
        self.sizeLang = 0.0
        self.vocabLen = 0.0
        #self.freqCutoff = freqCutoff#USE_ALL_WORDS
        
        self.wordDict = {}
        self.bigramDict = {}
        self.wordToClusDict = {}
        self.wordsInClusDict = {}
        self.nextWordDict = {}
        self.prevWordDict = {}
        self.clusUniCount = {}
        self.clusBiCount = {}
        self.morph = None
        
        #self.stopWordFile = stopWordFile
        #self.stopWords = []
        #self.considerForBi = []
        
    
        self.numClusters = numClusInit
        self.typeClusInit = typeClusInit
        
        #for key, val in wDict.iteritems():
        #    self.wordDict[key] = wDict[key]
        #    self.sizeLang += wDict[key]
            
        #for (w1, w2), val in bigramDict.iteritems():
        #    self.bigramDict[(w1, w2)] = bigramDict[(w1, w2)]
        
        self.wordDict = dict(wDict)
        self.bigramDict = dict(bigramDict)
        self.sizeLang = sum(1.0*val for word, val in wDict.iteritems())
        self.vocabLen = 1.0*len(self.wordDict)
        
        #self.readStopWordList()
        #self.setWordsForBi()    
        self.formClusters()
        self.formPrevNextWordDict()
        self.initializeClusterCounts()
        
        sys.stderr.write("\nFinished making a language object")
        
    def readStopWordList(self):
        
        for line in open(self.stopWordFile,'r'):
            line = line.strip()
            self.stopWords.append(line)
            
        return
        
    def setWordsForBi(self):
        
        if self.freqCutoff != USE_ALL_WORDS:
            #This makes bilingual factor only consider words below a particular frequnecy
            #for (word, val) in sorted(self.wordDict.items(), key=itemgetter(1), reverse=True):
            #    if val <= self.freqCutoff:
            #        self.considerForBi.append(word)
            
            for word in self.wordDict.keys():
                if word not in string.punctuation and word not in self.stopWords:
                    self.considerForBi.append(word)
            
        else:
            self.considerForBi = [word for word in self.wordDict.keys()]
            
        return
        
    def setMorphologyObject(self, morphObj):
        
        self.morph = morphObj
            
        return
            
    def formClusters(self):
    
        if self.typeClusInit == 0:
            # Put top numClusInit-1 words into their own cluster
            # Put the rest of the words into a single cluster
            insertedClus = 0
            for key, val in sorted(self.wordDict.items(), key=itemgetter(1), reverse=True):
                if insertedClus == self.numClusters:
                    self.wordToClusDict[key] = insertedClus
                    if insertedClus in self.wordsInClusDict:
                        self.wordsInClusDict[insertedClus].append(key)
                    else:
                        self.wordsInClusDict[insertedClus] = [key]
                else:
                    self.wordsInClusDict[insertedClus] = [key]
                    self.wordToClusDict[key] = insertedClus
        
                    insertedClus += 1
                
        if self.typeClusInit == 1:
            # Put words into the clusters in a round robin fashion
            # according the weight of the word
            numWord = 0
            for key, val in sorted(self.wordDict.items(), key=itemgetter(1), reverse=True):
                newClusNum = numWord % self.numClusters
                self.wordToClusDict[key] = newClusNum
                if newClusNum in self.wordsInClusDict:
                    self.wordsInClusDict[newClusNum].append(key)
                else:
                    self.wordsInClusDict[newClusNum] = [key]
                numWord += 1
                
                #print numWord-1, key, newClusNum
        return
        
    def initializeClusterCounts(self):
        
        # Get initial cluster counts
        for word in self.wordDict.iterkeys():
            clusNum = self.wordToClusDict[word]
            if clusNum in self.clusUniCount:
                self.clusUniCount[clusNum] += self.wordDict[word]
            else:
                self.clusUniCount[clusNum] = self.wordDict[word]
    
        for (w1, w2) in self.bigramDict.iterkeys():
            c1 = self.wordToClusDict[w1]
            c2 = self.wordToClusDict[w2]
            if (c1, c2) in self.clusBiCount:
                self.clusBiCount[(c1, c2)] += self.bigramDict[(w1, w2)]
            else:
                self.clusBiCount[(c1, c2)] = self.bigramDict[(w1, w2)]
            
        return
        
    def formPrevNextWordDict(self):
        
        for (w1, w2) in self.bigramDict.iterkeys():
            if w1 in self.nextWordDict:
                if w2 in self.nextWordDict[w1]:
                    pass
                else:
                    self.nextWordDict[w1].append(w2)
            else:
                self.nextWordDict[w1] = [w2]
            
            if w2 in self.prevWordDict:
                if w1 in self.prevWordDict[w2]:
                    pass
                else:
                    self.prevWordDict[w2].append(w1)
            else:
                self.prevWordDict[w2] = [w1]
                
        return
         
    def updateDistribution(self, wordToBeShifted, origClass, newClass):
        
        self.clusUniCount[origClass] -= self.wordDict[wordToBeShifted]
        self.clusUniCount[newClass] += self.wordDict[wordToBeShifted]
       
        if self.nextWordDict.has_key(wordToBeShifted):
            for w in self.nextWordDict[wordToBeShifted]:
               c = self.wordToClusDict[w]
               self.clusBiCount[(origClass, c)] -= self.bigramDict[(wordToBeShifted, w)]
               if (newClass, c) in self.clusBiCount:
                   self.clusBiCount[(newClass, c)] += self.bigramDict[(wordToBeShifted, w)]
               else:
                   self.clusBiCount[(newClass, c)] = self.bigramDict[(wordToBeShifted, w)]
              
        if self.prevWordDict.has_key(wordToBeShifted):
            for w in self.prevWordDict[wordToBeShifted]:
                c = self.wordToClusDict[w]
                self.clusBiCount[(c, origClass)] -= self.bigramDict[(w, wordToBeShifted)]
                if (c, newClass) in self.clusBiCount:
                    self.clusBiCount[(c, newClass)] += self.bigramDict[(w, wordToBeShifted)]
                else:
                    self.clusBiCount[(c, newClass)] = self.bigramDict[(w, wordToBeShifted)]
                                              
        self.wordToClusDict[wordToBeShifted] = newClass
        self.wordsInClusDict[origClass].remove(wordToBeShifted)
        self.wordsInClusDict[newClass].append(wordToBeShifted)
        
        if self.morph != None:
            self.morph.updateMorphData(wordToBeShifted, origClass, newClass)
        
    def calcTentativePerplex(self, wordToBeShifted, origClass, tempNewClass):
        
        deltaPerplex = 0.0
       
        # Removing the effects of the old unigram cluster count from the perplexity
        deltaPerplex -= 2 * nlogn(self.clusUniCount[origClass]/self.sizeLang)
        deltaPerplex -= 2 * nlogn(self.clusUniCount[tempNewClass]/self.sizeLang)
       
        # Finding only those bigram cluster counts that will be effected by the word transfer
        newBiCount = {}
        if self.nextWordDict.has_key(wordToBeShifted):
            for w in self.nextWordDict[wordToBeShifted]:
                c = self.wordToClusDict[w]
                if (origClass, c) in newBiCount:
                    newBiCount[(origClass, c)] -= self.bigramDict[(wordToBeShifted, w)]
                else:
                    newBiCount[(origClass, c)] = self.clusBiCount[(origClass, c)] - self.bigramDict[(wordToBeShifted, w)]
               
                if (tempNewClass, c) in newBiCount:
                    newBiCount[(tempNewClass, c)] += self.bigramDict[(wordToBeShifted, w)]
                elif (tempNewClass, c) in self.clusBiCount:
                    newBiCount[(tempNewClass, c)] = self.clusBiCount[(tempNewClass, c)] + self.bigramDict[(wordToBeShifted, w)]
                else:
                    newBiCount[(tempNewClass, c)] = self.bigramDict[(wordToBeShifted, w)]
    
        if self.prevWordDict.has_key(wordToBeShifted):
            for w in self.prevWordDict[wordToBeShifted]:
                c = self.wordToClusDict[w]
                if (c, origClass) in newBiCount:
                    newBiCount[(c, origClass)] -= self.bigramDict[(w, wordToBeShifted)]
                else:
                    newBiCount[(c, origClass)] = self.clusBiCount[(c, origClass)] - self.bigramDict[(w, wordToBeShifted)]
               
                if (c, tempNewClass) in newBiCount:
                    newBiCount[(c, tempNewClass)] += self.bigramDict[(w, wordToBeShifted)]
                elif (c, tempNewClass) in self.clusBiCount:
                    newBiCount[(c, tempNewClass)] = self.clusBiCount[(c, tempNewClass)] + self.bigramDict[(w, wordToBeShifted)]
                else:
                    newBiCount[(c, tempNewClass)] = self.bigramDict[(w, wordToBeShifted)]
        
        # Adding the effects of new unigram cluster counts in the perplexity
        newOrigClassUniCount = self.clusUniCount[origClass] - self.wordDict[wordToBeShifted]
        newTempClassUniCount = self.clusUniCount[tempNewClass] + self.wordDict[wordToBeShifted]
       
        deltaPerplex += 2 * nlogn(newOrigClassUniCount/self.sizeLang)
        deltaPerplex += 2 * nlogn(newTempClassUniCount/self.sizeLang)
       
        for (c1, c2), val in newBiCount.iteritems():
             if c1 != c2:
                 # removing the effect of old cluster bigram counts
                 if (c1, c2) in self.clusBiCount:
                     deltaPerplex += nlogn(self.clusBiCount[(c1, c2)]/self.sizeLang)
                 # adding the effect of new cluster bigram counts
                 deltaPerplex -= nlogn(val/self.sizeLang)
        
        if self.morph != None:
            deltaMorph = self.morph.getChangeInMorph(wordToBeShifted, origClass, tempNewClass)         
        else:
            deltaMorph = 0.0
                 
        return deltaPerplex + deltaMorph