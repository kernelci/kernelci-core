import re
import sys
import json
import argparse
from collections import defaultdict

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("filename", help="file to parse dt-validation output from")
	args = parser.parse_args()
	print("Parsing from ",args.filename)

	testDict = {} #Dictionary to be converted into a json object

	dtoutput = open(args.filename, "r")
	lines = dtoutput.readlines()

	"""
	#Checking lines that begin with "CHKDT" for errors
	#	it does this by recording the name of the file on the "CHKDT" line and seing if it is in any 
	#	line after it is first seen. If it is seen later, the later line gets printed

	for i,line in enumerate(lines):
		linereg = re.search("CHKDT +(\w+/.+$)",line)
		if linereg != None: 
			filename = linereg.group(1)
			for j in range(i+1, len(lines)): 
				innerReg = re.search(filename, lines[j])
				if innerReg != None: 
					print(filename)
	"""

	#separating the lines with warnings and errors
	elist = {}; wlist = {}
	for line in lines:
		linereg = re.search("^ +(DTC|CHECK|CHKDT|SCHEMA)",line)
		if linereg == None: 
			warningreg = re.search("^(.*): *(Warning.*)$", line)
			if warningreg != None:
				wlist[warningreg.group(1)] = warningreg.group(2)
			else:
				ereg = re.search("^(.*yaml): *(.*)$", line)
				print(line)
				print(ereg.group(1))
				elist[ereg.group(1)] = ereg.group(2)

	for line in lines:
		linereg = re.search("^ *(CHECK|CHKDT|SCHEMA) +(.*)$",line)
		if linereg != None: 
			currname = linereg.group(2)
			if linereg.group(1) == "CHECK":
				failed = False
				for name in elist.keys(): 
					if currname in name: #checking if currname is in the key of elist because the elist key is shows the directory path from root
						failed = True
						testName = currname.replace('.', '_').replace(',', '_').replace('/', '.')
						print("\"", testName, ".check\" : ", "\"FAIL\"",sep='')
						testDict[testName] = "FAIL"
						break
				if(not(failed) and not(currname in wlist) ):
					testName = currname.replace('.', '_').replace(',', '_').replace('/', '.')
					print("\"", testName, ".check\" : ", "\"PASS\"",sep='')
					testDict[testName] = "PASS"
			elif linereg.group(1) == "CHKDT":
				testName = currname.replace('.', '_').replace(',', '_').replace('/', '.')
				print("\"", testName, ".chkdt\" : ", "\"PASS\"",sep='')#I am making the assumption that lines beginning with "CHKDT" have passing files based on previous testing
				testDict[testName] = "PASS"
			elif linereg.group(1) == "SCHEMA":
				testName = currname.replace('.', '_').replace(',', '_').replace('/', '.')
				print("\"", testName, ".schema\" : ", "\"PASS\"",sep='')#Assuming lines beginning with "Schema" have passing files
				testDict[testName] = "PASS"

	print("\nWarnings: ")
	for name, warning in wlist.items(): 
		print("Filename: ", name, " ", warning)

	print("\nErrors: ")
	for name, error in elist.items(): 
		print("Filename: ", name, " Error: ", error)

	print("\nWarning Count: ", len(wlist))
	print("\nError Count: ", len(elist))

	print(testDict)

	testData = json.dumps(testDict)
	return testData

if __name__ == "__main__":
	main()