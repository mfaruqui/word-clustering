# Type python ochClustering.py -h for information on how to use
import sys
import os
import argparse

from operator import itemgetter
from math import log
from collections import Counter

from language import Language
from language import nlogn
from languagePairForward import LanguagePairForward
from languagePairBackward import LanguagePairBackward
from readAndWrite import readBilingualData
from readAndWrite import printClusters
from perplexity import calcPerplexity
from commonInLangPair import CommonInLangPair
              
def rearrangeClusters(origMono, origBi, lang, langPair, monoPower, biPower):
    
    wordsExchanged = 0
    wordsDone = 0
    
    currLeastMono = origMono
    currLeastBi = origBi
    
    for (word, val) in sorted(lang.wordDict.items(), key=itemgetter(1), reverse=False):
    #for word in sorted(lang.wordDict.keys()):
        
        origClass = lang.wordToClusDict[word]
        currLeastPerplex = origMono + origBi
        tempNewClass = origClass
        
        #print "WORD:", word
        
        # Try shifting every word to a new cluster and caluculate perplexity
        # Ensures that every cluster has at least 1 element
        if len(lang.wordsInClusDict[origClass]) > 1:
            for possibleNewClass in lang.clusUniCount.iterkeys():
                if possibleNewClass != origClass:
                    
                    if monoPower != 0:
                        deltaMono = lang.calcTentativePerplex(word, origClass, possibleNewClass)
                    else:
                        deltaMono = 0.0
                    
                    if biPower != 0:
                        deltaBi = langPair.calcTentativePerplex(word, origClass, possibleNewClass)
                    else:
                        deltaBi = 0.0
                        
                    tempMono = monoPower*deltaMono + origMono
                    tempBi = biPower*deltaBi + origBi
                    
                    possiblePerplex = tempMono + tempBi 
                    
                    #if deltaBi <= 0 and deltaMono <=0:
                    if possiblePerplex < currLeastPerplex: #and tempBi <= origBi:
                        
                        currLeastPerplex = possiblePerplex
                        tempNewClass = possibleNewClass
                        currLeastMono = tempMono
                        currLeastBi = tempBi 
            
            if tempNewClass != origClass:
                #print ''
                # Compare these values with the other version of your program
                #print word, origClass, tempNewClass
                #print langPair.wordEdgeCount[word], langPair.edgeSumInClus[origClass], langPair.edgeSumInClus[tempNewClass]
                #print lang.clusUniCount[origClass], lang.clusUniCount[tempNewClass]
                
                #print word, origClass, "->", tempNewClass
                
                wordsExchanged += 1
                
                lang.updateDistribution(word, origClass, tempNewClass)
                if biPower != 0:
                    langPair.updateDistribution(word, origClass, tempNewClass)
                
                #print langPair.wordEdgeCount[word], langPair.edgeSumInClus[origClass], langPair.edgeSumInClus[tempNewClass]
                #print lang.clusUniCount[origClass], lang.clusUniCount[tempNewClass]
                #print lang.wordToClusDict[word]
            
            #print ''        
        wordsDone += 1
        if wordsDone % 1000 == 0:    
            sys.stderr.write(str(wordsDone)+' ')

        origMono = currLeastMono
        origBi = currLeastBi
        
    return wordsExchanged, origMono, origBi
    
def runOchClustering(lang1, lang2, lang12, lang21, monoPower, biPower):
 
    wordsExchanged = 9999
    iterNum = 0
    origMono, origBi = calcPerplexity(lang1, lang2, lang12, lang21, monoPower, biPower)
    
    while ( (wordsExchanged > 0.001 * (lang1.vocabLen + lang2.vocabLen) or iterNum < 5) and wordsExchanged !=0 and iterNum <= 20):
        iterNum += 1
        wordsExchanged = 0
        wordsDone = 0
    
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Mono: '+str(origMono)+' Bi: '+str(origBi)+' Total: '+str(origMono + origBi)+'\n')
        sys.stderr.write('\nRearranging English words...\n')
        
        # Move around words of language 1
        wordsExchangedEn, origMono, origBi = rearrangeClusters(origMono, origBi, lang1, lang12, monoPower, biPower)
        
        wordsExchanged = wordsExchangedEn
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchangedEn)+'\n')
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Mono: '+str(origMono)+' Bi: '+str(origBi)+' Total: '+str(origMono + origBi)+'\n')
        sys.stderr.write('\nRearranging French words...\n')
        
        # Move around words of language 2            
        wordsExchangedFr, origMono, origBi = rearrangeClusters(origMono, origBi, lang2, lang21, monoPower, biPower)
        
        wordsExchanged += wordsExchangedFr 
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchangedFr)+'\n')
        
    return
    
def initializeLanguagePairObjets(alignDict, enWordDict, enBigramDict, frWordDict, frBigramDict, numClusInit, typeClusInit, freqCutoff):
    
    lang1 = Language(enWordDict, enBigramDict, numClusInit, typeClusInit, freqCutoff, "/Users/mfaruqui/Desktop/projects/multil-word-cluster/en_stop.txt")
    lang2 = Language(frWordDict, frBigramDict, numClusInit, typeClusInit, freqCutoff, "/Users/mfaruqui/Desktop/projects/multil-word-cluster/de_stop.txt")
    common = CommonInLangPair(alignDict, lang1, lang2)
    lang12 = LanguagePairForward(lang1, lang2, common)
    lang21 = LanguagePairBackward(lang2, lang1, common)
    lang12.assignReverseLanguagePair(lang21)
    lang21.assignReverseLanguagePair(lang12)
    
    return lang1, lang2, lang12, lang21, common
        
def main(inputFileName, alignFileName, mono1FileName, mono2FileName, outputFileName, numClusInit, typeClusInit, fileLength, monoPower, biPower, freqCutoff):
    
    # Read the input file and get word counts
    alignDict, enWordDict, enBigramDict, frWordDict, frBigramDict \
    = readBilingualData(fileLength, inputFileName, alignFileName, mono1FileName, mono2FileName)
    
    lang1, lang2, lang12, lang21, common = initializeLanguagePairObjets(alignDict, enWordDict, \
                                           enBigramDict, frWordDict, frBigramDict, numClusInit, typeClusInit, freqCutoff)
                                           
    del alignDict, enWordDict, enBigramDict, frWordDict, frBigramDict
    
    #freqProfile = Counter()
    #for word, val in lang1.wordDict.iteritems():
    #    freqProfile[val] += 1
    
    #ratio = 0.0
    #for val, freq in sorted(freqProfile.items(), key=itemgetter(0)):
    #    ratio += 1.0*freq/lang1.vocabLen
    #    print val, freq, ratio
    lang12.common.printSumMatrix()
    
    #for word, val in sorted(lang1.wordDict.items(), key=itemgetter(1), reverse=True):
    #    print word, val
    
    # Run the clustering algorithm and get new clusters    
    runOchClustering(lang1, lang2, lang12, lang21, monoPower, biPower)
    
    lang12.common.printSumMatrix()
    
    origMono, origBi = calcPerplexity(lang1, lang2, lang12, lang21, monoPower, biPower)
    
    #sys.stderr.write(str(origMono)+' '+str(origBi)+'\n')
    
    # Print the clusters
    printClusters(outputFileName, lang1, lang2, lang12)
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", type=str, help="Joint parallel file of two languages; sentences separated by |||")
    parser.add_argument("-a", "--alignfile", type=str, help="alignment file of the parallel corpus")
    parser.add_argument("-m1", "--monofile1", type=str, default='', help="Monolingual file of langauge 1")
    parser.add_argument("-m2", "--monofile2", type=str, default='', help="Monolingual file of langauge 2")
    parser.add_argument("-l", "--filelength", type=int, default=1000000000, help="max number of lines to be read")
    parser.add_argument("-n", "--numclus", type=int, default=100, help="No. of clusters to be formed")
    parser.add_argument("-o", "--outputfile", type=str, help="Output file with word clusters")
    parser.add_argument("-t", "--type", type=int, choices=[0, 1], default=1, help="type of cluster initialization")
    parser.add_argument("-p", "--bipower", type=float, default=1, help="co-efficient of the multilingual perplexity factor")
    parser.add_argument("-m", "--monopower", type=float, default=1, help="co-efficient of the monolingual perplexity factor")
    parser.add_argument("-f", "--freqcutoff", type=int, default=-1, help="words of freq <= f will be considered for bi")
    
    args = parser.parse_args()
    
    inputFileName = args.inputfile
    alignFileName = args.alignfile
    mono1FileName = args.monofile1
    mono2FileName = args.monofile2
    numClusInit = args.numclus
    outputFileName = args.outputfile
    typeClusInit = args.type
    biPower = args.bipower
    monoPower = args.monopower
    fileLength = args.filelength
    freqCutoff = args.freqcutoff
    
    main(inputFileName, alignFileName, mono1FileName, mono2FileName, outputFileName, numClusInit, typeClusInit, fileLength, monoPower, biPower, freqCutoff)