# Type python ochClustering.py -h for information on how to use
import sys
from operator import itemgetter
from math import log
import argparse
from collections import Counter

from language import Language
from perplexity import calcPerplexity
#from collections import defaultdict

def nlogn(x):
    if x == 0:
        return x
    else:
        return x * log(x)

def readInputFile(inputFileName):
    
    wordDict = {}#Counter()
    bigramDict = {}#Counter()
    
    sys.stderr.write('\nReading input file...')
    
    for en in open(inputFileName,'r'):
        
        en = en.strip()
        enWords = en.split()
        
        prevWord = ''
        for word in enWords:
            
            if word in wordDict:
                wordDict[word] += 1.0
            else:
                wordDict[word] = 1.0

            if prevWord != '':
                if (prevWord, word) in bigramDict:
                    bigramDict[(prevWord, word)] += 1.0
                else:
                    bigramDict[(prevWord, word)] = 1.0
            prevWord = word
     
    sys.stderr.write('  Complete!\n')
    return wordDict, bigramDict
       
# Implementation of Och 1999 clustering using the     
# algorithm of Martin, Liermann, Ney 1998    
def runOchClustering(lang):
 
    wordsExchanged = 9999
    iterNum = 0
    wordVocabLen = len(lang.wordDict)
    
    origPerplex, wastePerplex = calcPerplexity(lang, None, None, None, 0)
    
    while ((wordsExchanged > 0.001 * wordVocabLen or iterNum < 10) and iterNum <= 20):
        iterNum += 1
        wordsExchanged = 0
        wordsDone = 0
    
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Perplexity: '+str(origPerplex)+'\n')
        
        # Looping over all the words in the vocabulory
        for word in sorted(lang.wordDict.keys()):
            origClass = lang.wordToClusDict[word]
            currLeastPerplex = origPerplex
            tempNewClass = origClass
        
            # Try shifting every word to a new cluster and caluculate perplexity
            for possibleNewClass in lang.clusUniCount.keys():
                if possibleNewClass != origClass:
                    
                    deltaMono = lang.calcTentativePerplex(word, origClass, possibleNewClass)
                    possiblePerplex = deltaMono + origPerplex
                    
                    if possiblePerplex < currLeastPerplex:
                        currLeastPerplex = possiblePerplex
                        tempNewClass = possibleNewClass
                    
            wordsDone += 1
            if wordsDone % 1000 == 0:    
                sys.stderr.write(str(wordsDone)+' ')
            
            if tempNewClass != origClass:
                
                wordsExchanged += 1
                lang.updateDistribution(word, origClass, tempNewClass)
            
            origPerplex = currLeastPerplex
            
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchanged)+'\n')
            
    return 
    
def printNewClusters(outputFileName, lang):
    
    outFile = open(outputFileName, 'w')
     
    for clus, wordList in lang.wordsInClusDict.iteritems():
        outFile.write(str(clus)+' ||| ')       
        for word in wordList:
            outFile.write(word+' ')
        outFile.write('\n')
    
def main(inputFileName, outputFileName, numClusInit, typeClusInit):
    
    # Read the input file and get word counts
    wordDict, bigramDict = readInputFile(inputFileName)
    
    lang = Language(wordDict, bigramDict, numClusInit, typeClusInit)
    # Initialise the cluster distribution
    
    runOchClustering(lang)
    
    # Print the clusters
    printNewClusters(outputFileName, lang)
    
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