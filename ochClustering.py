# Type python ochClustering.py -h for information on how to use
import sys
from operator import itemgetter
import math
import argparse
from collections import Counter

def readInputFile(inputFileName):
    
    wordDict = {}
    bigramDict = {}
    
    # Stores the list of words next to a given word
    nextWordDict = {}
    # Stores the list of words appearing before a given word
    prevWordDict = {}
    
    for line in open(inputFileName,'r'):
        line = line.strip()
    
        try:
            w, num = line.split()
            wordDict[w] = int(num)
        except:
            w1, w2, num = line.split()
            bigramDict[(w1, w2)] = int(num)
        
            try:
                nextWordDict[w1].append(w2)
            except KeyError:
                nextWordDict[w1] = [w2]
        
            try:
                prevWordDict[w2].append(w1)
            except KeyError:
                prevWordDict[w2] = [w1]
                
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
def calcPerplexity(uniCount, biCount):
    
    sum1 = 0
    sum2 = 0
    
    for (c1, c2), nC1C2 in biCount.iteritems():
        if nC1C2 != 0 and c1 != c2:
            sum1 += nlogn( nC1C2 )
    
    for c, n in uniCount.iteritems():
        if n != 0:
            sum2 += nlogn( n )
            
    perplex = 2 * sum2 - sum1
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
            logValues[x] = x * math.log(x)
            return logValues[x]
       
def calcTentativePerplex(origPerplex, wordToBeShifted, origClass, tempNewClass, clusUniCount, \
clusBiCount, wordToClusDict, wordDict, bigramDict, nextWordDict, prevWordDict):
    
       newPerplex = origPerplex
       
       # Removing the effects of the old unigram cluster count from the perplexity
       newPerplex -= 2 * nlogn(clusUniCount[origClass])
       newPerplex -= 2 * nlogn(clusUniCount[tempNewClass])
       
       # Finding only those bigram cluster counts that will be effected by the word transfer
       newBiCount = {}
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
           
       return newPerplex
        
def updateClassDistrib(wordToBeShifted, origClass, tempNewClass, clusUniCount,\
            clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict):
            
       clusUniCount[origClass] -= wordDict[wordToBeShifted]
       clusUniCount[tempNewClass] += wordDict[wordToBeShifted]
       
       for w in nextWordDict[wordToBeShifted]:
              c = wordToClusDict[w]
            
              clusBiCount[(origClass, c)] -= bigramDict[(wordToBeShifted, w)]
              clusBiCount[(tempNewClass, c)] += bigramDict[(wordToBeShifted, w)]
               
       for w in prevWordDict[wordToBeShifted]:
               c = wordToClusDict[w]
                   
               clusBiCount[(c, origClass)] -= bigramDict[(w, wordToBeShifted)]
               clusBiCount[(c, tempNewClass)] += bigramDict[(w, wordToBeShifted)]
                                              
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
    
    while (wordsExchanged > 0.001 * wordVocabLen):
        iterNum += 1
        wordsExchanged = 0
        wordsDone = 0
    
        origPerplex = calcPerplexity(clusUniCount, clusBiCount)
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
                    clusUniCount, clusBiCount, wordToClusDict, wordDict, bigramDict,
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
    
def main(inputFileName, outputFileName, numClusInit, typeClusInit):
    
    # Read the input file and get word counts
    wordDict, bigramDict, nextWordDict, prevWordDict = readInputFile(inputFileName)
    
    # Initialise the cluster distribution
    wordToClusDict, wordsInClusDict = formInitialClusters(numClusInit, wordDict, typeClusInit)
    
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
    parser.add_argument("-n", "--numclus", type=int, help="No. of clusters to be formed")
    parser.add_argument("-o", "--outputfile", type=str, help="Output file with word clusters")
    parser.add_argument("-t", "--type", type=int, choices=[0, 1], default=1, help="type of cluster initialization")
                        
    args = parser.parse_args()
    
    inputFileName = args.inputfile
    numClusInit = args.numclus
    outputFileName = args.outputfile
    typeClusInit = args.type
    
    main(inputFileName, outputFileName, numClusInit, typeClusInit)