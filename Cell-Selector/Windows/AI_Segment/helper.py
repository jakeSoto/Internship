import sys, os
import tifffile
import numpy as np
import tkinter as tk
import matplotlib.pylab as plt
import multiprocessing.dummy as mp
from tkinter import filedialog
from cellpose import models
import transients


class container():
    def __init__(self, fileName,
                    index = None,
                    static = False,
                    raw = None,         # array of data
                    mask = None,        # array of cells locations
                    binaryMask = None,  # binary array of cells within the img
                    data = None,        # array of raw data from selected cells
                    cellCount = None,   # number of cells
                    traces = None,      # array of cell value traces
                    region_cells = None # array of cell indices
                    ):
        self.fileName = fileName
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


# Map folder names with file paths
def getFile() -> (dict, str):
    window = tk.Tk()
    window.wm_attributes('-topmost', 1)
    window.withdraw()
    root = filedialog.askopenfile(mode='r', filetypes=[('Tiff Files', '*.tif')])
    if (not root):
        print("Operation cancelled")
        exit(1)
    else:
        fileName = os.path.realpath(root.name)

    head, tail = os.path.split(fileName)
    return (fileName, head)


# Map channel name to container object
def createChannelContainer(fileName: str) -> container:
    root, file = os.path.split(fileName)
    title, ext = os.path.splitext(file)
    print("File"+": "+file)

    try:
        ar = transients.LoadTimeData(fileName, timeReversed = True)
        static = False
    except:
        ar = transients.LoadStaticData(fileName, timeReversed = True)
        static = True

    channel = container(fileName=file, raw=ar, static=static)

    return channel


# Multi-procceses Cellpose with all channels
def multiThread(channel: container) -> dict:
    dataSet = []

    if (channel.static == False):
        for i in range(0, len(channel.raw)):
            dataSet.append(channel.raw[i, :, :])
    else:
        dataSet.append(channel.raw)

    with mp.Pool() as pool:
        results = pool.map(runCellpose, dataSet)

    channel.mask = results
    return channel


# Calls Cellpose function
def runCellpose(data) -> []:
    model = models.Cellpose(gpu=True, model_type='cyto2')
    print("Processing mask")
    masks, flows, styles, diams = model.eval(data, diameter=None, do_3D=False)
    return masks


# Runs program on two channels
def processChannelData(channel: container, dest: str) -> dict:
    # Get masks
    channel = multiThread(channel)

    # Process data
    length = len(channel.mask)
    for i in range(length):
        dataSet = channel.mask[i]

        # Binary mask
        channel.binaryMask = np.zeros_like(dataSet, int)
        channel.binaryMask[dataSet > 0] = 1

        # Raw data of selected cells
        data = channel.binaryMask * channel.raw

        # Export
        print("Exporting mask: "+str(i+1)+"/"+str(length))
        tifffile.imwrite(dest, data, metadata={'axes': 'TZYX', 'TimeIncrement': i/length})

    return channel
