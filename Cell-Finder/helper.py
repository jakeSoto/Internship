import sys, os
from tkinter.filedialog import askdirectory


def searchDirectory() -> dict:
    root = askdirectory(title = "Select folder containing N_ folders...")
    folderPaths = []
    fileMap = {}
    counter = 0

    # Map folder names with file paths
    for path, subdirs, files in os.walk(root):
        for file in files:
            head, tail = os.path.split(path)
            fileMap[tail] = (head + "/" + tail + "/" + file)

    return fileMap
