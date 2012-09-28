# Takes in bigram counts of a monolingual file
# with all words lower cased and clusters them
# using Monolingual clustering of Och, 2003

# Usage: python netClustering.py dataFileName numClusInit > outFile
import sys
from operator import itemgetter
from math import log

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
    
def formInitialClusters(numClusInit, wordDict):
    
    wordsInClusDict = {}
    wordToClusDict = {}
    
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
            
    return wordToClusDict, wordsInClusDict
    
def getClusterCounts(wordToClusDict, wordsInClusDict, wordDict, bigramDict):
    
    # Get initial cluster unigram [n(C)] 
    clusUniCount = {}
    # Get initial bigram counts [n(C2,C1)]   
    clusBiCount = {}
    
    for word in wordDict.keys():
        clusNum = wordToClusDict[word]
        try:
            clusUniCount[clusNum] += wordDict[word]
        except KeyError:
            clusUniCount[clusNum] = wordDict[word]
    

    for (w1, w2) in bigramDict.keys():
        c1 = wordToClusDict[w1]
        c2 = wordToClusDict[w2]
        try:
            clusBiCount[(c1, c2)] += bigramDict[(w1, w2)]
        except KeyError:
            clusBiCount[(c1, c2)] = bigramDict[(w1, w2)]
            
    return clusUniCount, clusBiCount

# Calculates perplexity given the uni and bigram distribution of clusters
# Eq4 in Och 2003
def calcPerplexity(uniCount, biCount):
    
    sum1 = 0
    sum2 = 0
    
    for (c1, c2) in biCount.keys():
        nC1C2 = biCount[(c1,c2)]
        if nC1C2 != 0 and c1 != c2:
            sum1 += nC1C2 * log( nC1C2 )
    
    for c in uniCount.keys():
        n = uniCount[c]
        if n != 0:
            sum2 += n * log( n )
            
    perplex = 2 * sum2 - sum1
    return perplex
    
def calcTentativePerplex(origPerplex, wordToBeShifted, origClass, tempNewClass, clusUniCount, \
clusBiCount, wordToClusDict, wordDict, bigramDict, nextWordDict, prevWordDict):
    
       newPerplex = origPerplex
       
       # Removing the effects of the old count from the perplexity
       if clusUniCount[origClass] != 0:
           newPerplex -= 2 * clusUniCount[origClass] * log ( clusUniCount[origClass] )
       if clusUniCount[tempNewClass] != 0:
           newPerplex -= 2 * clusUniCount[tempNewClass] * log ( clusUniCount[tempNewClass] )
       
       for c1 in [origClass, tempNewClass]:
           for c2 in clusUniCount.keys():
               try:
                   val = clusBiCount[(c1, c2)]
                   if val != 0 and c1 != c2:
                       newPerplex += val * log( val )
               except KeyError:
                   pass
               
               try:
                   val = clusBiCount[(c2, c1)]
                   if val != 0 and c1 != c2:
                       newPerplex += val * log( val )
               except KeyError:
                   pass
                   
       # In the above function (origClass, tempClass) & (tempClass, origClass)
       # both have been counted twice, so remove them once each
       try:
           val = clusBiCount[(origClass, tempNewClass)]
           if val != 0:
               newPerplex -= val * log ( val )
       except:
           pass
           
       try:
           val = clusBiCount[(tempNewClass, origClass)]
           if val != 0:
               newPerplex -= val * log ( val )
       except:
           pass
       
       # Calculating only the changed bigram counts
       newBiCount = {}
       
       for c in clusUniCount.keys():
           try:
               newBiCount[(origClass, c)] = clusBiCount[(origClass, c)]
           except:
               pass
               
           try:
               newBiCount[(c, origClass)] = clusBiCount[(c, origClass)]
           except:
               pass
               
           try:
               newBiCount[(tempNewClass, c)] = clusBiCount[(tempNewClass, c)]
           except:
               newBiCount[(tempNewClass, c)] = 0
               
           try:
               newBiCount[(c, tempNewClass)] = clusBiCount[(c, tempNewClass)]
           except:
               newBiCount[(c, tempNewClass)] = 0
                   
       for w in nextWordDict[wordToBeShifted]:
           
           c = wordToClusDict[w]
           # This is wrong think about it
           #if newBiCount[(origClass, c)] - bigramDict[(wordToBeShifted, w)] >= 0:
           newBiCount[(origClass, c)] -= bigramDict[(wordToBeShifted, w)]
           newBiCount[(tempNewClass, c)] += bigramDict[(wordToBeShifted, w)]    
               
       for w in prevWordDict[wordToBeShifted]:
           
           c = wordToClusDict[w]
           # This is wrong think about it
           #if newBiCount[(c, origClass)] - bigramDict[(w, wordToBeShifted)] >= 0:
           newBiCount[(c, origClass)] -= bigramDict[(w, wordToBeShifted)]
           newBiCount[(c, tempNewClass)] += bigramDict[(w, wordToBeShifted)]
       
       # Adding the effects of new counts in the perplexity
       newOrigClassUniCount = clusUniCount[origClass] - wordDict[wordToBeShifted]
       newTempClassUniCount = clusUniCount[tempNewClass] + wordDict[wordToBeShifted]
       
       if newOrigClassUniCount != 0:
           newPerplex += 2 * newOrigClassUniCount * log ( newOrigClassUniCount )
       if newTempClassUniCount != 0:
           newPerplex += 2 * newTempClassUniCount * log ( newTempClassUniCount )
           
       for (c1, c2) in newBiCount.keys():
           val = newBiCount[(c1, c2)]
           if val > 0 and c1 != c2:
               newPerplex -= val * log(val)
           elif val < 0:
               print c1, c2, wordToBeShifted, newBiCount[(c1, c2)]
               sys.exit()
         
       return newPerplex
        
def updateClassDistrib(wordToBeShifted, origClass, tempNewClass, clusUniCount,\
            clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict):
            
       clusUniCount[origClass] -= wordDict[wordToBeShifted]
       clusUniCount[tempNewClass] += wordDict[wordToBeShifted]
       
       for w in nextWordDict[wordToBeShifted]:
              
              c = wordToClusDict[w]
            
              # This is wrong think about it
              #if clusBiCount[(origClass, c)] - bigramDict[(wordToBeShifted, w)] >= 0:
              clusBiCount[(origClass, c)] -= bigramDict[(wordToBeShifted, w)]
              try:
                  clusBiCount[(tempNewClass, c)] += bigramDict[(wordToBeShifted, w)]
              except KeyError:
                  clusBiCount[(tempNewClass, c)] = bigramDict[(wordToBeShifted, w)]
               
       for w in prevWordDict[wordToBeShifted]:
               
               c = wordToClusDict[w]
                   
               # This is wrong think about it
               #if clusBiCount[(c, origClass)] - bigramDict[(w, wordToBeShifted)] >= 0:
               clusBiCount[(c, origClass)] -= bigramDict[(w, wordToBeShifted)]
               try:
                   clusBiCount[(c, tempNewClass)] += bigramDict[(w, wordToBeShifted)]
               except KeyError:
                   clusBiCount[(c, tempNewClass)] = bigramDict[(w, wordToBeShifted)]
                                              
       wordToClusDict[wordToBeShifted] = tempNewClass
       wordsInClusDict[origClass].remove(wordToBeShifted)
       wordsInClusDict[tempNewClass].append(wordToBeShifted)
       
       return

# Implementation fo Och 1999 clustering using the     
# algorithm of Martin, Liermann, Ney 1998    
def runOchClustering(wordDict, bigramDict, clusUniCount, clusBiCount,\
    wordToClusDict, wordsInClusDict, nextWordDict, prevWordDict):
 
    wordsExchanged = 1
    iterNum = 0
    while (wordsExchanged != 0):
    
        iterNum += 1
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n')
        wordsExchanged = 0
        wordsDone = 0
    
        origPerplex = calcPerplexity(clusUniCount, clusBiCount)
    
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
    
def printNewClusters(wordsInClusDict):
    
    print '' 
    for clus in wordsInClusDict.keys():
        print clus, '|||',       
        for word in wordsInClusDict[clus]:
            print word,
        print ''
    
def main():
    # File name containig unigram and bigram counts
    dataFileName = sys.argv[1]
    
    # numClusInit = No. of initial word clusters
    numClusInit = int(sys.argv[2])
    
    # Read the input file and get word counts
    wordDict, bigramDict, nextWordDict, prevWordDict = readInputFile(dataFileName)
    
    # Initialise the cluster distribution
    wordToClusDict, wordsInClusDict = formInitialClusters(numClusInit, wordDict)
    
    # Get counts of the initial cluster configuration
    clusUniCount, clusBiCount = getClusterCounts(wordToClusDict, wordsInClusDict, wordDict, bigramDict)
    
    # Run the clustering algorithm and get new clusters    
    clusUniCount, clusBiCount, wordsToClusDict, wordsInClusDict = \
    runOchClustering(wordDict, bigramDict, clusUniCount, clusBiCount,\
    wordToClusDict, wordsInClusDict, nextWordDict, prevWordDict)
    
    # Print the clusters
    printNewClusters(wordsInClusDict)
    
if __name__ == "__main__":
    main()
    
    