import sys, os
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
                    name = None,
                    index = None,
                    raw = None,         # array of data
                    mask = None,        # array of cells locations
                    binaryMask = None,  # binary array of cells within the img
                    dataSet = None,     # holds data to get cell traces
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
            header = sheet.cell(row = 1, column = (j*5)+count)
            header.value = (str(title) + str(j+1))

            cell = sheet.cell(row = i+2, column = (j*5)+count)
            cell.value = item


# For use with static channels
def exportStaticData(sheet, dataSet, title, count):
    for i, value in enumerate(dataSet):
        header = sheet.cell(row = 1, column = (i*5)+count)
        header.value = (str(title) + str(i+1))

        cell = sheet.cell(row = 2, column = (i*5)+count)
        cell.value = value


# Save cells segmenation img
def saveCellImg(mask, path):
    plt.figure(figsize=(60,30))
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


# Runs program on two channels
def processTwoChannels(channels: dict, measuredName: str) -> dict:
    # References
    MCHERRY = channels['mCherry']
    STATIC = channels[measuredName]

    # Get masks
    channels = multiProcess(channels)
    
    # Convert masks to binary
    for key, channel in channels.items():
        channel.binaryMask = np.zeros_like(channel.mask, int)
        channel.binaryMask[channel.mask > 0] = 1

    # Select cells
    combo_BinaryMask = STATIC.binaryMask + MCHERRY.binaryMask
    MCHERRY.mask = runCellpose(combo_BinaryMask)

    final_BinaryMask = np.zeros_like(MCHERRY.mask, int)
    final_BinaryMask[MCHERRY.mask > 0] = 1

    dataSet = final_BinaryMask * MCHERRY.raw
    STATIC_values = final_BinaryMask * STATIC.raw
    cellCount = np.max(final_BinaryMask * MCHERRY.mask)

    MCHERRY.region_cells = getRegionCells(MCHERRY.mask, cellCount)

    # Time series data
    traces, region_cells = transients.GetTraces(dataSet, final_BinaryMask, region_cells=MCHERRY.region_cells)
    MCHERRY.traces = traces

    # Static channel values
    traces, region_cells = transients.GetTraces(STATIC_values, final_BinaryMask, region_cells=MCHERRY.region_cells)
    STATIC.traces = traces

    return channels


# Runs program on three channels
def processThreeChannels(channels: dict, measuredName: str) -> (dict, container):
    # References    
    for i in channels:
        if (i == 'mCherry'):
            MCHERRY = channels[i]
        elif (i == measuredName):
            MEASURED = channels[i]
        else:
            STATIC = channels[i]

        channels[i].name = i
        
    # Get masks
    channels = multiProcess(channels)

    # Convert masks to binary
    for key, channel in channels.items():
        channel.binaryMask = np.zeros_like(channel.mask, int)
        channel.binaryMask[channel.mask > 0] = 1

    # Select cells
    combo_BinaryMask = STATIC.binaryMask + MEASURED.binaryMask + MCHERRY.binaryMask
    MCHERRY.mask = runCellpose(combo_BinaryMask)

    final_BinaryMask = np.zeros_like(MCHERRY.mask, int)
    final_BinaryMask[MCHERRY.mask > 0] = 1

    for key, channel in channels.items():
        channel.dataSet = final_BinaryMask * channel.raw

    cellCount = np.max(final_BinaryMask * MCHERRY.mask)

    MCHERRY.region_cells = getRegionCells(MCHERRY.mask, cellCount)


    for key, channel in channels.items():
        traces, region_cells = transients.GetTraces(channel.dataSet, final_BinaryMask, region_cells=MCHERRY.region_cells)
        channel.traces = traces


    return channels
