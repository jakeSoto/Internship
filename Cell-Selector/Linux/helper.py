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
    root = askdirectory(title = "Select folder to process...")
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
        print(name)
        ar = transients.LoadTimeData(name, timeReversed = True)
        channelDict[title] = container(fileName=file, index=i, raw=ar)

    return channelDict


# Multi-procceses Cellpose with all channels
def multiProcess(channelDict: dict) -> dict:
    dataSet = []

    for channel in channelDict.values():
        dataSet.append(channel.raw[0, :, :])

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


def transposeData(dataSet) -> []:
    dataSet = np.array(dataSet)
    dataSet = dataSet.T
    return dataSet


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


def saveTraces(traces, path):
    nTrace = len(traces)
    nTimePts = len(traces[0])
    frameRate = 25      #sec/frame 
    ts = np.linspace(0, (frameRate*nTimePts/60), nTimePts)
    start = 0
    end = 30

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title("Trace")
        
    for i in range(nTrace):
        trace = traces[i]
        ax.plot(ts[start:end+1], trace[start:end+1])
        
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight')


# Transposes data and exports to xlsx sheet
def exportData(sheet, dataSet, title, count):
    for i, sublist in enumerate(dataSet):
        for j, item in enumerate(sublist):
            header = sheet.cell(row = 1, column = (j*4)+count)
            header.value = (str(title) + str(j+1))

            cell = sheet.cell(row = i+2, column = (j*4)+count)
            cell.value = item



# Runs program on two channels
def processTwoChannels(channels: dict) -> dict:
    # References
    CHAN1 = None
    CHAN2 = None

    # Get masks
    channels = multiProcess(channels)
    
    # Convert masks to binary
    for key, channel in channels.items():
        channel.binaryMask = np.zeros_like(channel.mask, int)
        channel.binaryMask[channel.mask > 0] = 1
        if (CHAN1 == None):
            CHAN1 = channels[key]
        else:
            CHAN2 = channels[key]


    # Select cells
    combo_BinaryMask = CHAN1.binaryMask + CHAN2.binaryMask
    CHAN1.mask = runCellpose(combo_BinaryMask)

    final_BinaryMask = np.zeros_like(CHAN1.mask, int)
    final_BinaryMask[CHAN1.mask > 0] = 1

    dataSet1 = final_BinaryMask * CHAN1.raw
    dataSet2 = final_BinaryMask * CHAN2.raw
    cellCount = np.max(final_BinaryMask * CHAN1.mask)

    CHAN1.region_cells = getRegionCells(CHAN1.mask, cellCount)

    # Time series data
    traces, region_cells = transients.GetTraces(dataSet1, final_BinaryMask, region_cells=CHAN1.region_cells)
    CHAN1.traces = traces

    traces, region_cells = transients.GetTraces(dataSet2, final_BinaryMask, region_cells=CHAN1.region_cells)
    CHAN2.traces = traces

    return channels


