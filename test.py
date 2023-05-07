import os

fo = open("static/files/test.txt","r")
rows = fo.readlines()
print(rows[int(1)-1])
