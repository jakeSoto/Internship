import sys, os
import tifffile
import numpy as np
import tkinter as tk
import matplotlib.pylab as plt
from tkinter import filedialog
from tkinter.filedialog import askdirectory
from cellpose import models
from multiprocessing import Pool
import transients


class container():
  def __init__(self, fileName,
                    index = None,
                    raw = None,         # array of data
                    mask = None,        # array of cells locations
                    binaryMask = None,  # binary array of cells within the img
                    traces = None       # array of cell value traces
                    ):
    self.fileName = fileName
    self.index = index
    self.raw = raw
    self.mask = mask
    self.binaryMask = binaryMask
    self.traces = traces

class cellProp():
    def __init__(self, coords=None, area=None):
        self.coords = coords
        self.area = area


# Map folder names with file paths
def searchDirectory() -> (dict, str):
    window = tk.Tk()
    window.wm_attributes('-topmost', 1)
    window.withdraw()
    root = askdirectory(title = "Select folder containing N_ folders...")
    if (not root):
        print("Operation cancelled")
        exit(1)
    else:
        root = os.path.realpath(root)
    
    folderPaths = []
    fileMap = {}

    for path, subdirs, files in os.walk(root):
        temp = []
        head, tail = os.path.split(path)

        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if (ext == ".tif"):
                filePath = os.path.realpath(os.path.join(path, file))
                temp.append(filePath)
            
        fileMap[tail] = temp

    return (fileMap, root)


# Prompts user to select a Static Channel
# Measures the values of cells from that channel
def measuredChannel(folderDict) -> str:
    print("Select the channel to measure")
    window = tk.Tk()
    window.wm_attributes('-topmost', 1)
    window.withdraw()
    targetFile = filedialog.askopenfile(title="Select the channel to measure...", filetypes=(('tif files','*.tif'), ('All files', '*,*')))
    if (not targetFile):
        print("Operation cancelled")
        exit(1)
    else:
        targetPath = os.path.realpath(targetFile.name)

    channelRef = None

    for i, files in folderDict.items():
        for file in files:
            if (file == targetPath):
                root, fileName = os.path.split(file)
                channelName, ext = os.path.splitext(fileName)
                channelRef = channelName

    return channelRef


# Map channel name to container object
def createChannelDict(fileNames: [str]) -> dict:
    channelDict = {}
    
    for i, name in enumerate(fileNames):
        root, file = os.path.split(name)
        title, ext = os.path.splitext(file)
        if (title == "mCherry"):
            ar = transients.LoadTimeData(name, timeReversed = True)
        else:
            ar = transients.LoadStaticData(name, timeReversed = True)

        channelDict[title] = container(fileName=file, index=i, raw=ar)

    return channelDict


# Multi-procceses Cellpose with all channels
def multiProcess(channelDict: dict) -> dict:
    dataSet = []

    for channel in channelDict.values():
        if (channel.fileName == "mCherry.tif"):
            dataSet.append(channel.raw[0, :, :])
        else:
            dataSet.append(channel.raw)

    with Pool() as pool:
        results = pool.map(runCellpose, dataSet)

    for channel in channelDict.values():
        channel.mask = results[channel.index]

    return channelDict


# Calls Cellpose function
def runCellpose(data) -> []:
    model = models.Cellpose(gpu=True, model_type='cyto2')
    print("Processing mask")
    masks, flows, styles, diams = model.eval(data, diameter=None, do_3D=False)
    return masks


# Get cell indices within image
def getRegionCells(mask, cellCount) -> []:
    indices = []
    areas = []

    for i in range(1, cellCount+1):
        index = np.argwhere(mask == i)
        area = len(index)
        indices.append(index)
        areas.append(area)
    
    indices = np.array(indices, dtype=object)
    areas = np.array(areas, dtype=object)

    region_cells = []
    for i in range(cellCount):
        prop = cellProp(indices[i], areas[i])
        region_cells.append(prop)

    return region_cells


# Normalization Formula = (x - min) / (max - min)
def normalizeData(dataSet) -> []: 
    normalized = [None] * len(dataSet)

    for i in range(len(dataSet)):
        trace = dataSet[i]
        minVal = np.min(trace)
        maxVal = np.max(trace)
        norm = (trace - minVal) / (maxVal - minVal)
        normalized[i] = norm

    return normalized


# Transposes data and exports to xlsx sheet
def exportData(sheet, dataSet, title, count):
    dataSet = np.array(dataSet)
    dataSet = dataSet.T

    for i, sublist in enumerate(dataSet):
        for j, item in enumerate(sublist):
            header = sheet.cell(row = 1, column = (j*4)+count)
            header.value = (str(title) + str(j+1))

            cell = sheet.cell(row = i+2, column = (j*4)+count)
            cell.value = item


# Save cells segmenation img
def saveCellImg(mask, path):
    plt.figure(figsize=(80,40))
    ax1 = plt.subplot(131)
    ax1.set_title('Selected Cells')
    ax1.imshow(mask)
    labels=[]

    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            if (mask[i][j] == 0):
                continue
            else:
                if (mask[i][j] not in labels):
                    labels.append(mask[i][j])
                    ax1.text(j, i, int(mask[i][j]), ha="center", va="center", fontsize=12, fontweight='black', color='orange')

    plt.savefig(path, bbox_inches='tight')



# Runs program on * channels
def processChannels(channels: dict, dest: str) -> dict:
    # Get masks
    channels = multiProcess(channels)

    # Process data
    for key, channel in channels.items():
        # Binary mask
        channel.binaryMask = np.zeros_like(channel.mask, int)
        channel.binaryMask[channel.mask > 0] = 1

        # Raw data of selected cells
        channel.data = channel.binaryMask * channel.raw

        # Export data to tiff file
        tifffile.imwrite(dest, channel.data)

    return channels
