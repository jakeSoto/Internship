import sys, os
from fnmatch import fnmatch
from tkinter import filedialog

class container():
  def __init__(self, index, fileName, filePath):
    self.index = index
    self.fileName = fileName
    self.filePath = filePath

"""
Search for a file in a path, requires user input
Usage:
    FILE_NAME
"""
def searchDirectory():
    root = filedialog.askdirectory()
    counter = 0
    fileNames = ["CFP.tif", "mCherry.tif"]
    names = []
    paths = []
    dicts = {}

    # User input
    root = input("Enter the directory path to search: ")
    temp = input("GFP or YFP?: ")
    if (temp == "GFP" or temp == "gfp"):
        fileNames.append("GFP.tif")
    else:
        fileNames.append("YFP.tif")

    for path, subdirs, files in os.walk(root):
        for name in files:
            


"""
    # Searching - without repeats
    # Returns dictionary of container obj
    for path, subdirs, files in os.walk(root):
        for name in files:
            for target in fileNames:
                if fnmatch(name, target):
                    if checkMatches(path, paths):
                        result = container(counter, os.path.join(name), os.path.join(path, name))
                        dicts[counter] = result
                        paths.append(path)
                        #names.append(os.path.join(name))
                        #paths.append(os.path.join(path, name))
                        #dicts[counter] = zip(names, paths)
                        counter += 1

    return dicts


def checkMatches(targetPath, existingPaths):
    flag = True
    
    if existingPaths is None:
        return flag

    for target in existingPaths:
        if fnmatch(targetPath, target):
            flag = False

    return flag
"""