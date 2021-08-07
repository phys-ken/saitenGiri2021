import os, sys

readFile = open("setting/ini.csv")
lines = readFile.readlines()
readFile.close()
w = open("setting/ini.csv",'w')
w.writelines([item for item in lines[:-1]])
w.close()