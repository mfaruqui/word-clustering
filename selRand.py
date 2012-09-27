import sys
import random

fileName = sys.argv[1]
numSent = int( sys.argv[2])

numTaken = 0
listSent = []
for line in open(fileName,'r'):
    line = line.strip()
    
    if numTaken < numSent:
        listSent.append( line )
        numTaken += 1
    else:
        randNum = random.randint( 0, numSent-1 )
        listSent[ randNum ] = line
        
for line in listSent:
    print line