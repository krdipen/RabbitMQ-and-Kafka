import os, sys

os.system(f"find . -name {sys.argv[1]} > dirt.txt")
infile = open("dirt.txt", "r")
files = infile.read().strip().split()
infile.close()

for file in files:
    os.system(f"git rm --cached -r {file}")
os.system(f"rm -r dirt.txt")
