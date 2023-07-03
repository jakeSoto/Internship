import sys, os
import numpy as np
from tkinter.filedialog import askdirectory
import matplotlib.pylab as plt
from cellpose import models
import transients

class container():
  def __init__(self, fileName,
                    index = None,
                    raw = None,   # array of data
                    mask = None,  # array of cells locations
                    binaryMask = None,  # binary array of cells within the img
                    traces = None
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


def searchDirectory() -> (dict, str):
    root = askdirectory(title = "Select folder containing N_ folders...")
    folderPaths = []
    fileMap = {}

    # Map folder names with file paths
    for path, subdirs, files in os.walk(root):
        temp = []
        head, tail = os.path.split(path)

        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if (ext == ".tif"):
                filePath = (head + "/" + tail + "/" + file)
                temp.append(filePath)
            
        fileMap[tail] = temp

    return (fileMap, root)


# Creates a dictionary for channel container
def createDict(fileNames: [str]) -> dict:
    channelDict = {}
    
    for i, name in enumerate(fileNames):
        root, file = os.path.split(name)
        fileName, ext = os.path.splitext(file)
        if (fileName == "mCherry"):
            ar = transients.LoadTimeData(name, timeReversed = True)
        else:
            ar = transients.LoadStaticData(name, timeReversed = True)
        channelDict[fileName] = container(fileName=file, index=i, raw=ar)

    return channelDict


# For use with multiprocessing pool
def runCellpose(data, title):
    model = models.Cellpose(gpu=True, model_type='cyto2')
    print("Processing mask for: " + str(title))
    masks, flows, styles, diams = model.eval(data, diameter=None, do_3D=False, )
    return masks


def getRegionCells(mask, cellCount) -> []:
    # Cell indicies
    indices=[]
    areas=[]
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

def normalizeData(dataSet): 
    normalized = [None] * len(dataSet)

    for i in range(len(dataSet)):
        trace = dataSet[i]
        minVal = np.min(trace)
        maxVal = np.max(trace)
        norm = (trace - minVal) / (maxVal - minVal)
        normalized[i] = norm

    return normalized

# Export data list to xlsx sheet
def exportData(sheet, dataSet, title, count):
    for i, sublist in enumerate(dataSet):
        for j, item in enumerate(sublist):
            header = sheet.cell(row = 1, column = (j*4)+count)
            header.value = (str(title) + str(j+1))

            cell = sheet.cell(row = i+2, column = (j*4)+count)
            cell.value = item


# Save cell segmenation img
def saveCellImg(mask, path):
    plt.figure(figsize=(20,10))
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



def processTwoChannels(channels: dict) -> dict:
    # Channel references
    MCHERRY = channels['mCherry']
    STATIC = None
    for i in channels:
        if (channels[i] != MCHERRY):
            STATIC = channels[i]

    # Get masks
    multiProcess(channels)
    #STATIC.mask = runCellpose(STATIC.raw, STATIC.fileName)
    #MCHERRY.mask = runCellpose(MCHERRY.raw[0], MCHERRY.fileName)
    
    # Convert masks to binary
    for key, channel in channels.items():
        channel.binaryMask = np.zeros_like(channel.mask, int)
        channel.binaryMask[channel.mask > 0] = 1

    # Select cells
    combo_BinaryMask = STATIC.binaryMask + MCHERRY.binaryMask
    MCHERRY.mask = runCellpose(combo_BinaryMask, "Data Set")

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



def multiProcess(channelDict: dict) -> dict:
    dataSet = []

    for channel in channelDict.values():
        if (channel.fileName == "mCherry.tif"):
            dataSet.append(channel.raw[0])
        else:
            dataSet.append(channel.raw)

    with Pool() as pool:
        results = pool.map(runCellpose, dataSet)

    for channel in channelDict.values():
        channel.mask = results[channel.index]

    return channelDict