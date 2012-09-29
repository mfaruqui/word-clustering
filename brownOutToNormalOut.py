import sys

clusDict = {}
for line in sys.stdin:
	line = line.strip()
	x, word, clus = line.split('\t')

	try:
		clusDict[clus].append(word)
	except:
		clusDict[clus] = [word]

for clus in clusDict.keys():
	print clus, "|||", 
	for word in clusDict[clus]:
		print word,
	print ''
