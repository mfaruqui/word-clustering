import sys

for line in sys.stdin:
	line = line.strip()
	f, e = line.split('|||')

	print e
