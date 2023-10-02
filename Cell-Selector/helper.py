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
                    index = None,
                    static = False,
                    raw = None,         # array of raw flourescence data
                    mask = None,        # array of cells locations of raw data
                    binaryMask = None,  # binary array of cells within the img
                    data = None,        # array of raw data from selected cells
                    cellCount = None,   # number of cells
                    traces = None,      # array of timeseries flourescence traces
                    region_cells = None # array of cell indices
                    ):
        self.fileName = fileName
        self.index = index
        self.static = static
        self.raw = raw
        self.mask = mask
        self.binaryMask = binaryMask
        self.data = data
        self.cellCount = cellCount
        self.traces = traces
        self.region_cells = region_cells


class cellProp():
    def __init__(self, coords=None, area=None):
        self.coords = coords
        self.area = area


# Map file names with file paths
def getFiles() -> (dict, str):
    window = tk.Tk()
    window.wm_attributes('-topmost', 1)
    window.withdraw()
    root = filedialog.askopenfilenames(title="Choose files to analyze...", filetypes=[('Tiff Files', '*.tif')])
    if (not root):
        print("Operation cancelled")
        exit(1)
    else:
        fileMap = {}
        for i in range(len(root)):
            path = os.path.realpath(root[i])
            head, tail = os.path.split(root[i])
            head = os.path.realpath(head)
            fileName, ext = os.path.splitext(tail)
            fileMap[fileName] = path

    return (fileMap, head)


# Map file name to container object
def createChannelDict(fileDict: dict) -> dict:
    channelDict = {}
    
    for i, name in enumerate(fileDict):
        fileName = name + ".tif"
        print("File "+str(i+1)+": "+fileName)

        try:
            ar = transients.LoadTimeData(fileDict[name], timeReversed = True)
            static = False
        except:
            ar = transients.LoadStaticData(fileDict[name], timeReversed = True)
            static = True

        channelDict[name] = container(fileName=fileName, index=i, raw=ar, static=static)

    return channelDict


# Multi-procceses Cellpose with all channels
def multiProcess(channelDict: dict, lastFrame: bool) -> dict:
    dataSet = []

    for channel in channelDict.values():
        if (channel.static == False):
            if (lastFrame == True):
                lastFrame = len(channel.raw) - 1
                dataSet.append(channel.raw[lastFrame, :, :])
            else:
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


# Transpose data set for xlsx export
def transposeData(dataSet) -> []:
    dataSet = np.array(dataSet)
    dataSet = dataSet.T
    return dataSet


# Save one cell segmenation img
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


# Saves cell segrementation images from all channels to one .png
def saveCellImgs(channels, path):
    fig = plt.figure(figsize=(60, 30))
    fig.set_facecolor('white')
    number_of_channels = len(channels)
    
    for i, key in enumerate(channels.keys()):
        channel = channels[key]
        if (channel.static == True):
            continue
        mask = channel.mask
        ax = fig.add_subplot(1, number_of_channels, i+1)
        ax.set_title(str(key))
        ax.imshow(mask)
        labels = []

        #Label cells
        for i in range(mask.shape[0]):
            for j in range(mask.shape[1]):
                if (mask[i][j] == 0):
                    continue
                else:
                    if (mask[i][j] not in labels):
                        labels.append(mask[i][j])
                        ax.text(j, i, int(mask[i][j]), ha="center", va="center", fontsize=12, fontweight='black', color='orange')

    plt.savefig(path, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')


# Exports traces to xlsx sheet
def exportData(sheet, dataSet, title, count):
    for i, sublist in enumerate(dataSet):
        for j, item in enumerate(sublist):
            header = sheet.cell(row = 1, column = (j*5)+count)
            header.value = (str(title) + str(j+1))

            cell = sheet.cell(row = i+2, column = (j*5)+count)
            cell.value = item


# Export average cell flourescence value to xlsx sheet
def exportStaticData(sheet, dataSet, title, count):
    for i, value in enumerate(dataSet):
        header = sheet.cell(row = 1, column = (i*5)+count)
        header.value = (str(title) + str(i+1))

        cell = sheet.cell(row = 2, column = (i*5)+count)
        cell.value = value


# Runs program on two channels
def processChannelData(channels: dict) -> dict:
    # Get masks
    channels = multiProcess(channels, lastFrame=True)
    combo_BinaryMask = np.zeros_like(channels[list(channels.keys())[0]].mask, int)

    # Binary mask
    for key, channel in channels.items():
        channel.binaryMask = np.zeros_like(channel.mask, int)
        channel.binaryMask[channel.mask > 0] = 1
        combo_BinaryMask = combo_BinaryMask + channel.binaryMask
    
    # Combined mask from all channels
    combo_mask = runCellpose(combo_BinaryMask)

    final_BinaryMask = np.zeros_like(combo_mask, int)
    final_BinaryMask[combo_mask > 0] = 1

    cellCount = np.max(final_BinaryMask * combo_mask)
    region_cells = getRegionCells(combo_mask, cellCount)

    # Cell traces
    for key, channel in channels.items():
        channel.mask = combo_mask
        
        # Raw flourescence data of selected cells
        channel.data = final_BinaryMask * channel.raw
        traces, region_cells_master = transients.GetTraces(channel.data, final_BinaryMask, region_cells=region_cells)
        channel.traces = traces

    return channels
