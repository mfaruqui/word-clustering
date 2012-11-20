# Type python ochClustering.py -h for information on how to use
import sys
from operator import itemgetter
from math import log
from math import exp
import argparse
from collections import Counter
from collections import defaultdict

def multi_dimensions(n, type):
  """ Creates an n-dimension dictionary where the n-th dimension is of type 'type'
  """  
  if n<=1:
    return type()
  return defaultdict(lambda:multi_dimensions(n-1, type))

def getInitialClusterMorphSum(ngramSimDict, wordsInClusDict):
    
    clusSumMorphDict = Counter()
    
    for c, wordList in wordsInClusDict.iteritems():
        numPairs = 0.0
        logProdMorph = 0.0
        sumClus = 0.0
        for i, w in enumerate(wordList):
            tempSum = 0.0
            for j in range(i+1, len(wordList)):
                val = getWordSim(w, wordList[j])
                if val != 0:
                    numPairs += 1
                    sumClus += val
                    tempSum += val
            if tempSum != 0.0:
                logProdMorph += log(tempSum)
        if numPairs != 0.0:        
            logProdMorph -= numPairs*log(sumClus)
            clusSumMorphDict[c] = (numPairs, sumClus, logProdMorph)
        else:
            clusSumMorphDict[c] = (0.0, 0.0, 0.0)
            
    return clusSumMorphDict
                
def readMorphSimFile(morphFileName, wordDict):
    
    sys.stderr.write('\nReading Morph Sim file...')
    ngramSimDict = multi_dimensions(2, Counter)
    for line in open(morphFileName, 'r'):
        line = line.strip()
        w1, w2, val = line.split()
        val = float(val)
        
        if w1 in wordDict and w2 in wordDict:
            ngramSimDict[w1][w2] = 2 * val / (len(w1)-2 + len(w2)-2) 
        
    sys.stderr.write("  Complete!\n")
    
    return ngramSimDict
    
def getWordSim(w1, w2):
    
    return max(ngramSimDict[w1][w2], ngramSimDict[w2][w1])

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

def readInputFile(inputFileName):
    
    wordDict = Counter()
    bigramDict = Counter()
    
    sys.stderr.write('\nReading input file...')
    
    for en in open(inputFileName,'r'):
        
        en = en.strip()
        enWords = en.split()
        
        prevWord = ''
        for word in enWords:
            wordDict[word] += 1.0
            if prevWord != '':
                bigramDict[(prevWord, word)] += 1.0
            prevWord = word
     
    nextWordDict, prevWordDict = getNextPrevWordDict(bigramDict)    
    sys.stderr.write('  Complete!\n')
    return wordDict, bigramDict, nextWordDict, prevWordDict
    
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

# Calculates perplexity given the uni and bigram distribution of clusters
# Eq4 in Och 2003
def calcPerplexity(uniCount, biCount, wordsInClusDict):
    
    sum1 = 0
    sum2 = 0
    morph = 0
    
    for (c1, c2), nC1C2 in biCount.iteritems():
        if nC1C2 != 0 and c1 != c2:
            sum1 += nlogn( nC1C2 )
    
    for c, n in uniCount.iteritems():
        if n != 0:
            sum2 += nlogn( n )
        
        (sumClus, numPairs, logProdMorph) = clusSumMorphDict[c]
        morph += logProdMorph
    
    print morph, 2 * sum2 - sum1
    perplex = 2 * sum2 - sum1 - morphPower*morph
    return perplex

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
       
def calcTentativePerplex(origPerplex, wordToBeShifted, origClass, tempNewClass, clusUniCount, \
clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict):

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
       
       # Delete contribution of the old cluster
       deltaMorph = 0.0
       wordList = wordsInClusDict[origClass]
       
       (clusSumMorph, numPairs, logProdMorph) = clusSumMorphDict[origClass]
       if numPairs != 0:
   
           deltaMorph += logProdMorph    

           newClusSumMorph = clusSumMorph
           newNumPairs = numPairs
           
           for i, w in enumerate(wordList):
               if w != wordToBeShifted:
                   newClusSumMorph -= getWordSim(w, wordToBeShifted)#ngramSimDict[(w, wordToBeShifted)]
                   newNumPairs += 1
                   
           if newClusSumMorph != 0:
               
               newLogProdMorph = logProdMorph + numPairs*log(clusSumMorph) - newNumPairs*log(newClusSumMorph)
               deltaMorph -= newLogProdMorph
                          
       wordList = wordsInClusDict[tempNewClass]
                  
       (clusSumMorph, numPairs, logProdMorph) = clusSumMorphDict[tempNewClass]
       
       if numPairs != 0:
           deltaMorph += logProdMorph    
       
       newClusSumMorph = clusSumMorph
       newNumPairs = numPairs
       
       for i, w in enumerate(wordList):
           if ngramSimDict[(w, wordToBeShifted)] != 0:
               newClusSumMorph += getWordSim(w, wordToBeShifted)#ngramSimDict[(w, wordToBeShifted)]
               newNumPairs += 1
       
       if newNumPairs != 0:            
           if numPairs != 0:
               newLogProdMorph = logProdMorph + numPairs*log(clusSumMorph) - newNumPairs*log(newClusSumMorph)
           else:
               newLogProdMorph = logProdMorph - newNumPairs*log(newClusSumMorph)
           
           deltaMorph -= newLogProdMorph
       
       return newPerplex + morphPower*deltaMorph
        
def updateClassDistrib(wordToBeShifted, origClass, tempNewClass, clusUniCount,\
            clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict):
            
       #print "called"
            
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
               
               
       wordList = wordsInClusDict[origClass]
       (clusSumMorph, numPairs, logProdMorph) = clusSumMorphDict[origClass]
       
       if numPairs != 0:
           
           newClusSumMorph = clusSumMorph
           newNumPairs = numPairs
           
           for i, word in enumerate(wordList):
               if ngramSimDict[(word, wordToBeShifted)] != 0:
                   newClusSumMorph -= getWordSim(w, wordToBeShifted)#ngramSimDict[(word, wordToBeShifted)]
                   newNumPairs -= 1
       
           if newNumPairs != 0:        
               newLogProdMorph = logProdMorph + numPairs*log(clusSumMorph) - newNumPairs*log(newClusSumMorph)
               clusSumMorphDict[origClass] = (newClusSumMorph, newNumPairs, newLogProdMorph)
           else:   
               clusSumMorphDict[origClass] = (0, 0, 0)       
               
       wordList = wordsInClusDict[tempNewClass]
       (clusSumMorph, numPairs, logProdMorph) = clusSumMorphDict[tempNewClass]
       
       newClusSumMorph = clusSumMorph
       newNumPairs = numPairs
           
       for i, word in enumerate(wordList):
           if ngramSimDict[(word, wordToBeShifted)] != 0:
               newClusSumMorph += getWordSim(w, wordToBeShifted)#ngramSimDict[(word, wordToBeShifted)]
               newNumPairs += 1
       
       if newNumPairs != 0:
           if numPairs != 0:
               newLogProdMorph = logProdMorph + numPairs*log(clusSumMorph) - newNumPairs*log(newClusSumMorph)
           else:
               newLogProdMorph = logProdMorph - newNumPairs*log(newClusSumMorph)
           
           clusSumMorphDict[tempNewClass] = (newClusSumMorph, newNumPairs, newLogProdMorph)
       else:   
           clusSumMorphDict[tempNewClass] = (0, 0, 0)
                                              
       wordToClusDict[wordToBeShifted] = tempNewClass
       wordsInClusDict[origClass].remove(wordToBeShifted)
       wordsInClusDict[tempNewClass].append(wordToBeShifted)
       
       return

# Implementation of Och 1999 clustering using the     
# algorithm of Martin, Liermann, Ney 1998    
def runOchClustering(wordDict, bigramDict, clusUniCount, clusBiCount,\
    wordToClusDict, wordsInClusDict, nextWordDict, prevWordDict):
 
    wordsExchanged = 9999
    iterNum = 0
    wordVocabLen = len(wordDict.keys())
    
    while (wordsExchanged > 0.001 * wordVocabLen and iterNum <= 50):
        iterNum += 1
        wordsExchanged = 0
        wordsDone = 0
    
        origPerplex = calcPerplexity(clusUniCount, clusBiCount, wordsInClusDict)
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Perplexity: '+str(origPerplex)+'\n')
        
        # Looping over all the words in the vocabulory
        for word in wordDict.keys():
            origClass = wordToClusDict[word]
            currLeastPerplex = origPerplex
            tempNewClass = origClass
        
            # Try shifting every word to a new cluster and caluculate perplexity
            for possibleNewClass in clusUniCount.keys():
                if possibleNewClass != origClass:
                    possiblePerplex = calcTentativePerplex(origPerplex, word, origClass, possibleNewClass,\
                    clusUniCount, clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict,
                    nextWordDict, prevWordDict)
                
                    if possiblePerplex < currLeastPerplex:
                        currLeastPerplex = possiblePerplex
                        tempNewClass = possibleNewClass
                    
            wordsDone += 1
            if wordsDone % 1000 == 0:    
                sys.stderr.write(str(wordsDone)+' ')
            
            if tempNewClass != origClass:
                #sys.stderr.write(word+' '+str(origClass)+'->'+str(tempNewClass)+' ')
                wordsExchanged += 1
                updateClassDistrib(word, origClass, tempNewClass, clusUniCount,\
                clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict)
            
            origPerplex = currLeastPerplex
            
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchanged)+'\n')
            
    return clusUniCount, clusBiCount, wordToClusDict, wordsInClusDict
    
def printNewClusters(outputFileName, wordsInClusDict):
    
    outFile = open(outputFileName, 'w')
     
    for clus, wordList in wordsInClusDict.iteritems():
        outFile.write(str(clus)+' ||| ')       
        for word in wordList:
            outFile.write(word+' ')
        outFile.write('\n')
    
def main(inputFileName, morphFileName, outputFileName, numClusInit, typeClusInit):
    
    global ngramSimDict, clusSumMorphDict
    global morphPower
    morphPower = 1
    
    # Read the input file and get word counts
    wordDict, bigramDict, nextWordDict, prevWordDict = readInputFile(inputFileName)
    
    # Initialise the cluster distribution
    wordToClusDict, wordsInClusDict = formInitialClusters(numClusInit, wordDict, typeClusInit)
    
    # Reading the morph file name
    ngramSimDict = readMorphSimFile(morphFileName, wordDict)
    
    # Get initial cluster moprh sum counts
    clusSumMorphDict = getInitialClusterMorphSum(ngramSimDict, wordsInClusDict)
    
    # Get counts of the initial cluster configuration
    clusUniCount, clusBiCount = getClusterCounts(wordToClusDict, wordsInClusDict, wordDict, bigramDict)
    
    # Run the clustering algorithm and get new clusters    
    clusUniCount, clusBiCount, wordsToClusDict, wordsInClusDict = \
    runOchClustering(wordDict, bigramDict, clusUniCount, clusBiCount,\
    wordToClusDict, wordsInClusDict, nextWordDict, prevWordDict)
    
    # Print the clusters
    printNewClusters(outputFileName, wordsInClusDict)
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", type=str, help="Input file containing word bigram and unigram counts")
    parser.add_argument("-m", "--morphfile", type=str, help="Morphological similarity file")
    parser.add_argument("-n", "--numclus", type=int, help="No. of clusters to be formed")
    parser.add_argument("-o", "--outputfile", type=str, help="Output file with word clusters")
    parser.add_argument("-t", "--type", type=int, choices=[0, 1], default=1, help="type of cluster initialization")
                        
    args = parser.parse_args()
    
    inputFileName = args.inputfile
    numClusInit = args.numclus
    outputFileName = args.outputfile
    typeClusInit = args.type
    morphFileName = args.morphfile
    
    main(inputFileName, morphFileName, outputFileName, numClusInit, typeClusInit)