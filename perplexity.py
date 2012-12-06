from language import nlogn
from math import log
import sys

def calcPerplexity(en, fr, enFr, frEn, power):
    
    sum1 = 0
    sum2 = 0
    
    for (c1, c2), nC1C2 in en.clusBiCount.iteritems():
        if nC1C2 != 0 and c1 != c2:
            sum1 += nlogn( nC1C2/en.sizeLang )
            #print "enClusBi", nC1C2, "/", en.sizeLang
            #print en.wordsInClusDict[c1]
            #print en.wordsInClusDict[c2]
    
    for c, n in en.clusUniCount.iteritems():
        if n != 0:
            sum2 += nlogn( n/en.sizeLang )
            #print "enClusUni", n, "/", en.sizeLang
            
    for (c1, c2), nC1C2 in fr.clusBiCount.iteritems():
        if nC1C2 != 0 and c1 != c2:
            sum1 += nlogn( nC1C2/fr.sizeLang )
            #print "frClusBi", nC1C2, "/", fr.sizeLang
            #print fr.wordsInClusDict[c1]
            #print fr.wordsInClusDict[c2]
            
    for c, n in fr.clusUniCount.iteritems():
        if n != 0:
            sum2 += nlogn( n/fr.sizeLang )
            #print "frClusUni", n, "/", fr.sizeLang
            
    print sum1, sum2
            
    perplex = 2 * sum2 - sum1
    
    sumClusEntrop = 0.0
    for (c_en, c_fr), sumCountPair in enFr.common.sumAlignedWordsInClusPairDict.iteritems():
        pxy = sumCountPair/enFr.common.sumAllAlignLinks
        px = enFr.edgeSumInClus[c_en]/enFr.common.sumAllAlignLinks
        py = frEn.edgeSumInClus[c_fr]/frEn.common.sumAllAlignLinks
        sumClusEntrop += pxy*log(pxy/px) + pxy*log(pxy/py)
        #print c_en, c_fr, enFr.edgeSumInClus[c_en], frEn.edgeSumInClus[c_fr], frEn.common.sumAllAlignLinks
        
    #sys.exit()
        
    return perplex, -power*sumClusEntrop