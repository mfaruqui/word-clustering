from language import nlogn
from math import log
import sys

def calcPerplexity(en, fr, enFr, frEn, monoPower, biPower):
    
    sum1 = 0.0
    sum2 = 0.0
    morphFactor = 0.0
    
    if en != None:
        for (c1, c2), nC1C2 in en.clusBiCount.iteritems():
            if nC1C2 != 0 and c1 != c2:
                sum1 += nlogn( nC1C2/en.sizeLang )
                
        for c, n in en.clusUniCount.iteritems():
            if n != 0:
                sum2 += nlogn( n/en.sizeLang )
                if en.morph!= None and en.morph.weight != 0:
                    morphFactor += en.morph.getClusMorphFactor(c)
                
    if fr != None:
        for (c1, c2), nC1C2 in fr.clusBiCount.iteritems():
            if nC1C2 != 0 and c1 != c2:
                sum1 += nlogn( nC1C2/fr.sizeLang )
                
        for c, n in fr.clusUniCount.iteritems():
            if n != 0:
                sum2 += nlogn( n/fr.sizeLang )
                if fr.morph != None and fr.morph.weight != 0:
                    morphFactor += fr.morph.getClusMorphFactor(c)
                
    monoPerplex = monoPower*(2 * sum2 - sum1)
    biPerplex = 0.0
    
    if enFr != None:
        for (c_en, c_fr), sumCountPair in enFr.common.sumAlignedWordsInClusPairDict.iteritems():
            pxy = sumCountPair/enFr.common.sumAllAlignLinks
            px = enFr.edgeSumInClus[c_en]/enFr.common.sumAllAlignLinks
            py = frEn.edgeSumInClus[c_fr]/frEn.common.sumAllAlignLinks
            if pxy != 0:
                biPerplex += pxy*log(pxy/px) + pxy*log(pxy/py)
        
    sys.stderr.write("mono: "+str(monoPerplex)+"morph: "+str(morphFactor)+"bi: "+str(-biPower*biPerplex))
        
    return monoPerplex-morphFactor, -biPower*biPerplex