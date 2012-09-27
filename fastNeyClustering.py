# Takes in bigram counts of a monolingual file
# with all words lower cased and clusters them
# using Monolingual clustering of Och, 2003

# Usage: python netClustering.py dataFileName numClusInit > outFile
import sys
from operator import itemgetter
from math import log
import copy

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
    
       uniCount = copy.deepcopy(clusUniCount)
       biCount = copy.deepcopy(clusBiCount)
       
       newPerplex = origPerplex
       
       # Removing the effects of the old count from the perplexity
       if clusUniCount[origClass] != 0:
           newPerplex -= 2 * clusUniCount[origClass] * log ( clusUniCount[origClass] )
       if clusUniCount[tempNewClass] != 0:
           newPerplex -= 2 * clusUniCount[tempNewClass] * log ( clusUniCount[tempNewClass] )
       
       for c1 in [origClass, tempNewClass]:
           for c2 in clusUniCount.keys():
               try:
                   val = biCount[(c1, c2)]
                   if val != 0 and c1 != c2:
                       newPerplex += val * log( val )
               except KeyError:
                   pass
               
               try:
                   val = biCount[(c2, c1)]
                   if val != 0 and c1 != c2:
                       newPerplex += val * log( val )
               except KeyError:
                   pass
       
       # Calculating new weights again
       uniCount[origClass] -= wordDict[wordToBeShifted]
       uniCount[tempNewClass] += wordDict[wordToBeShifted]
       flag = 0
       
       for w in nextWordDict[wordToBeShifted]:
               
              if w == wordToBeShifted:
                   flag = 1
                   
              c = wordToClusDict[w]
              biCount[(origClass, c)] -= bigramDict[(wordToBeShifted, w)]
              
              try:
                  biCount[(tempNewClass, c)] += bigramDict[(wordToBeShifted, w)]
              except KeyError:
                  biCount[(tempNewClass, c)] = bigramDict[(wordToBeShifted, w)]
                           
       for w in prevWordDict[wordToBeShifted]:
               
               if w == wordToBeShifted:
                   flag = 1
                   
               c = wordToClusDict[w]
               biCount[(c, origClass)] -= bigramDict[(w, wordToBeShifted)]
               
               try:    
                   biCount[(c, tempNewClass)] += bigramDict[(w, wordToBeShifted)]
               except KeyError:
                   biCount[(c, tempNewClass)] = bigramDict[(w, wordToBeShifted)]
               
       # Adding the effects of new counts in the perplexity
       if uniCount[origClass] != 0:
           newPerplex += 2 * uniCount[origClass] * log ( uniCount[origClass] )
       if uniCount[tempNewClass] != 0:
           newPerplex += 2 * uniCount[tempNewClass] * log ( uniCount[tempNewClass] )
       
       for c1 in [origClass, tempNewClass]:
           for c2 in uniCount.keys():
               try:
                   val = biCount[(c1, c2)]
                   if val != 0 and c1 != c2:
                       newPerplex -= val * log( val )
               except KeyError:
                   pass
               
               try:
                   val = biCount[(c2, c1)]
                   if val != 0 and c1 != c2:
                       newPerplex -= val * log( val )   
               except KeyError:
                   pass
        
       return newPerplex
        
def updateClassDistrib(wordToBeShifted, origClass, tempNewClass, clusUniCount,\
            clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict):
            
       clusUniCount[origClass] -= wordDict[wordToBeShifted]
       clusUniCount[tempNewClass] += wordDict[wordToBeShifted]
       
       flag = 0
       for w in nextWordDict[wordToBeShifted]:
               
              if w == wordToBeShifted:
                   flag = 1
              c = wordToClusDict[w]
                   
              clusBiCount[(origClass, c)] -= bigramDict[(wordToBeShifted, w)]
              try:
                  clusBiCount[(tempNewClass, c)] += bigramDict[(wordToBeShifted, w)]
              except KeyError:
                  clusBiCount[(tempNewClass, c)] = bigramDict[(wordToBeShifted, w)]
               
       for w in prevWordDict[wordToBeShifted]:
               
               if w == wordToBeShifted:
                   flag = 1
               c = wordToClusDict[w]
               
               clusBiCount[(c, origClass)] -= bigramDict[(w, wordToBeShifted)]
               try:
                   clusBiCount[(c, tempNewClass)] += bigramDict[(w, wordToBeShifted)]
               except KeyError:
                   clusBiCount[(c, tempNewClass)] = bigramDict[(w, wordToBeShifted)]
           
       # Revert the double counting that could have happened    
       if flag == 1:
               clusBiCount[(origClass, origClass)] += bigramDict[(wordToBeShifted, wordToBeShifted)]
               clusBiCount[(tempNewClass, tempNewClass)] -= bigramDict[(wordToBeShifted, wordToBeShifted)]
                                   
       wordToClusDict[wordToBeShifted] = tempNewClass
       wordsInClusDict[origClass].remove(wordToBeShifted)
       wordsInClusDict[tempNewClass].append(wordToBeShifted)
       
       return
       
# File name containig unigram and bigram counts
dataFileName = sys.argv[1]

# numClusInit = No. of initial word clusters
# Most frequent n-1 words have their own cluster
# Rest all other words are in one cluster
numClusInit = int(sys.argv[2])

wordDict = {}
bigramDict = {}

# Stores the list of words next to a given word
nextWordDict = {}
# Stores the list of words appearing before a given word
prevWordDict = {}
for line in open(dataFileName,'r'):
    
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
 
# Put top numClusInit-1 words into their own cluster
# Put the rest of the words into a single cluster
wordsInClusDict = {}
wordToClusDict = {}
insertedClus = 0
for key, val in sorted(wordDict.items(), key=itemgetter(1), reverse=True):
    if insertedClus == numClusInit:
        wordToClusDict[key] = insertedClus
        try:
            wordsInClusDict[insertedClus].append(key)
        except KeyError:
            wordsInClusDict[insertedClus] = [key]
    else:
        wordsInClusDict[insertedClus] = []
        wordsInClusDict[insertedClus].append(key)
        
        wordToClusDict[key] = insertedClus
        
        insertedClus += 1        
        
# Get initial cluster unigram [n(C)] 
clusUniCount = {}
for word in wordDict.keys():
    clusNum = wordToClusDict[word]
    try:
        clusUniCount[clusNum] += wordDict[word]
    except KeyError:
        clusUniCount[clusNum] = wordDict[word]
    
# Get initial bigram counts [n(C2,C1)]   
clusBiCount = {}
for (w1, w2) in bigramDict.keys():
    c1 = wordToClusDict[w1]
    c2 = wordToClusDict[w2]
    try:
        clusBiCount[(c1, c2)] += bigramDict[(w1, w2)]
    except KeyError:
        clusBiCount[(c1, c2)] = bigramDict[(w1, w2)]

# Implementing exchange algorithm of Martin, Liermann, Ney 1998
wordsExchanged = 1
iterNum = 0
while (wordsExchanged == 1):
    
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
                possiblePerplex = calcTentativePerplex(origPerplex, word, origClass, tempNewClass,\
                clusUniCount, clusBiCount, wordToClusDict, wordDict, bigramDict,
                nextWordDict, prevWordDict)
                
                if possiblePerplex < currLeastPerplex:
                    currLeastPerplex = possiblePerplex
                    tempNewClass = possibleNewClass
                    
        wordsDone += 1
        if wordsDone % 1000 == 0:    
            sys.stderr.write(str(wordsDone)+' ')
            
        if tempNewClass != origClass:
            sys.stderr.write(word+' '+str(origClass)+'->'+str(tempNewClass)+' ')
            wordsExchanged = 1
            updateClassDistrib(word, origClass, tempNewClass, clusUniCount,\
            clusBiCount, wordToClusDict, wordsInClusDict, wordDict, bigramDict, nextWordDict, prevWordDict)
        else:
            sys.stderr.write(word+': NoChange ')
            
        origPerplex = currLeastPerplex
                           
for clus in wordsInClusDict.keys():
    print clus, '###',       
    for word in wordsInClusDict[clus]:
        print word,
    print ''