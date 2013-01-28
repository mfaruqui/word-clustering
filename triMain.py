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
              
def rearrangeClusters(origMono, origBi, lang, langPair1, langPair2, monoPower, biPower):
    
    wordsExchanged = 0
    wordsDone = 0
    
    currLeastMono = origMono
    currLeastBi = origBi
    
    for (word, val) in sorted(lang.wordDict.items(), key=itemgetter(1), reverse=True):
        
        origClass = lang.wordToClusDict[word]
        currLeastPerplex = origMono + origBi
        tempNewClass = origClass
        
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
                        deltaBi = langPair1.calcTentativePerplex(word, origClass, possibleNewClass)
                        if langPair2 != None:
                            deltaBi += langPair2.calcTentativePerplex(word, origClass, possibleNewClass)
                    else:
                        deltaBi = 0.0
                        
                    tempMono = monoPower*deltaMono + origMono
                    tempBi = biPower*deltaBi + origBi
                    
                    possiblePerplex = tempMono + tempBi 
                    
                    if possiblePerplex < currLeastPerplex:
                        
                        currLeastPerplex = possiblePerplex
                        tempNewClass = possibleNewClass
                        currLeastMono = tempMono
                        currLeastBi = tempBi 
            
            if tempNewClass != origClass:
                
                wordsExchanged += 1
                lang.updateDistribution(word, origClass, tempNewClass)
                if biPower != 0:
                    langPair1.updateDistribution(word, origClass, tempNewClass)
                    if langPair2 != None:
                        langPair2.updateDistribution(word, origClass, tempNewClass)
        
        wordsDone += 1
        if wordsDone % 1000 == 0:    
            sys.stderr.write(str(wordsDone)+' ')

        origMono = currLeastMono
        origBi = currLeastBi
        
    return wordsExchanged, origMono, origBi
    
def runOchClustering(lang1, lang2, lang3, lang12, lang21, lang32, lang23, monoPower, biPower):
 
    wordsExchanged = 9999
    iterNum = 0
    origMono, origBi = (0.0, 0.0)
    
    while ( (wordsExchanged > 0.001 * (lang1.vocabLen + lang2.vocabLen + lang3.vocabLen) or iterNum < 5) and wordsExchanged !=0 and iterNum <= 20):
        iterNum += 1
        wordsExchanged = 0
        wordsDone = 0
    
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Mono: '+str(origMono)+' Bi: '+str(origBi)+' Total: '+str(origMono + origBi)+'\n')
        sys.stderr.write('\nRearranging English words...\n')
        # Move around words of language 1
        wordsExchangedEn, origMono, origBi = rearrangeClusters(origMono, origBi, lang1, lang12, None, monoPower, biPower)
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchangedEn)+'\n')
        
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Mono: '+str(origMono)+' Bi: '+str(origBi)+' Total: '+str(origMono + origBi)+'\n')
        sys.stderr.write('\nRearranging German words...\n')
        # Move around words of language 2            
        wordsExchangedDe, origMono, origBi = rearrangeClusters(origMono, origBi, lang2, lang21, lang23, monoPower, biPower)
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchangedDe)+'\n')
        
        sys.stderr.write('\n'+'IterNum: '+str(iterNum)+'\n'+'Mono: '+str(origMono)+' Bi: '+str(origBi)+' Total: '+str(origMono + origBi)+'\n')
        sys.stderr.write('\nRearranging French words...\n')
        # Move around words of language 3            
        wordsExchangedFr, origMono, origBi = rearrangeClusters(origMono, origBi, lang3, lang32, None, monoPower, biPower)
        sys.stderr.write('\nwordsExchanged: '+str(wordsExchangedFr)+'\n')
    
        wordsExchanged = wordsExchangedEn + wordsExchangedDe + wordsExchangedFr
        
    return
    
def initializeLanguagePairObjets(alignDictEnDe, alignDictFrDe, enWordDict, enBigramDict, deWordDict, deBigramDict,\
                                frWordDict, frBigramDict, numClusInit, typeClusInit, edgeThresh1, edgeThresh2):
    
    # lang3 (de) is the common language between the two pairs
    lang1 = Language(enWordDict, enBigramDict, numClusInit, typeClusInit)
    lang2 = Language(deWordDict, deBigramDict, numClusInit, typeClusInit)
    lang3 = Language(frWordDict, frBigramDict, numClusInit, typeClusInit)
    
    # En-De
    common12 = CommonInLangPair(alignDictEnDe, lang1, lang2, edgeThresh1)
    lang12 = LanguagePairForward(lang1, lang2, common12)
    lang21 = LanguagePairBackward(lang2, lang1, common12)
    lang12.assignReverseLanguagePair(lang21)
    lang21.assignReverseLanguagePair(lang12)
    
    # Fr-De
    common32 = CommonInLangPair(alignDictFrDe, lang3, lang2, edgeThresh2)
    lang32 = LanguagePairForward(lang3, lang2, common32)
    lang23 = LanguagePairBackward(lang2, lang3, common32)
    lang32.assignReverseLanguagePair(lang23)
    lang23.assignReverseLanguagePair(lang32)
    
    return lang1, lang2, lang3, lang12, lang21, lang32, lang23
        
def main(inputFileName1, alignFileName1, inputFileName2, alignFileName2, mono1FileName, mono2FileName, \
        outputFileName, numClusInit, typeClusInit, fileLength, monoPower, biPower, edgeThresh1, edgeThresh2):
    
    # Read the input file and get word counts
    # 3 languages say: en, fr, de; de is the common in en-de and fr-de
    # 1: en 2:de 3: fr
    enWordDict = Counter()
    enBigramDict = Counter()
    deWordDict = Counter()
    deBigramDict = Counter()
    frWordDict = Counter()
    frBigramDict = Counter()
    
    alignDictEnDe, enWordDict, enBigramDict, deWordDict, deBigramDict \
    = readBilingualData(fileLength, inputFileName1, alignFileName1, mono1FileName, mono2FileName,\
                        enWordDict, enBigramDict, deWordDict, deBigramDict)
                        
    alignDictFrDe, frWordDict, frBigramDict, deWordDict, deBigramDict \
    = readBilingualData(fileLength, inputFileName2, alignFileName2, mono1FileName, mono2FileName,\
                        frWordDict, frBigramDict, deWordDict, deBigramDict)
    
    lang1, lang2, lang3, lang12, lang21, lang32, lang23 = initializeLanguagePairObjets(\
                alignDictEnDe, alignDictFrDe, enWordDict, enBigramDict, deWordDict, deBigramDict, frWordDict, frBigramDict,\
                numClusInit, typeClusInit, edgeThresh1, edgeThresh2)
                                           
    del alignDictEnDe, alignDictFrDe
    del enWordDict, enBigramDict, deWordDict, deBigramDict, frWordDict, frBigramDict
    
    # Run the clustering algorithm and get new clusters    
    runOchClustering(lang1, lang2, lang3, lang12, lang21, lang32, lang23, monoPower, biPower)
    
    # Print the clusters
    printClusters(outputFileName, lang1, lang2, lang3)
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i1", "--inputfile1", type=str, help="Joint parallel file of two languages; sentences separated by |||")
    parser.add_argument("-i2", "--inputfile2", type=str, help="Joint parallel file of two languages; sentences separated by |||")
    parser.add_argument("-a1", "--alignfile1", type=str, help="alignment file of the parallel corpus")
    parser.add_argument("-a2", "--alignfile2", type=str, help="alignment file of the parallel corpus")
    parser.add_argument("-m1", "--monofile1", type=str, default='', help="Monolingual file of langauge 1")
    parser.add_argument("-m2", "--monofile2", type=str, default='', help="Monolingual file of langauge 2")
    parser.add_argument("-l", "--filelength", type=int, default=1000000000, help="max number of lines to be read")
    parser.add_argument("-n", "--numclus", type=int, default=100, help="No. of clusters to be formed")
    parser.add_argument("-o", "--outputfile", type=str, help="Output file with word clusters")
    parser.add_argument("-t", "--type", type=int, choices=[0, 1], default=1, help="type of cluster initialization")
    parser.add_argument("-p", "--bipower", type=float, default=1, help="co-efficient of the multilingual perplexity factor")
    parser.add_argument("-m", "--monopower", type=float, default=1, help="co-efficient of the monolingual perplexity factor")
    parser.add_argument("-e1", "--edgethresh1", type=float, default=0, help="thresh for edges to be considered for bi")
    parser.add_argument("-e2", "--edgethresh2", type=float, default=0, help="thresh for edges to be considered for bi")
    
    args = parser.parse_args()
    
    inputFileName1 = args.inputfile1
    alignFileName1 = args.alignfile1
    
    inputFileName2 = args.inputfile2
    alignFileName2 = args.alignfile2
    
    mono1FileName = args.monofile1
    mono2FileName = args.monofile2
    numClusInit = args.numclus
    outputFileName = args.outputfile
    typeClusInit = args.type
    biPower = args.bipower
    monoPower = args.monopower
    fileLength = args.filelength
    
    edgeThresh1 = args.edgethresh1
    edgeThresh2 = args.edgethresh2
    
    main(inputFileName1, alignFileName1, inputFileName2, alignFileName2, mono1FileName, mono2FileName,\
         outputFileName, numClusInit, typeClusInit, fileLength, monoPower, biPower, edgeThresh1, edgeThresh2)