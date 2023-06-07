import time
startTime = time.time()

import transients, util, searchDirectory
import numpy as np
from cellpose import models
import matplotlib.pyplot as plt
from skimage import exposure

class container():
  def __init__(self,fileName, index=None, raw = None):
    self.fileName = fileName
    self.index = index
    self.raw = raw
            
# Class for cell properties
class cellProp():
    def __init__(self, coords=None, area=None):
        self.coords = coords
        self.area = area

# Varibales
channels = {}
path = "E:/Loyola/PKH/Cell-Finder/Test_Data/"
fileNames = ["CFP.tif", "GFP.tif", "mCherry.tif"]
channelNames = ["CFP", "GFP", "MCHERRY"]
#fileNames = searchDirectory.searchDirectory()

# Main Method
# 1) Create a dictionary to store channel info (container obj)
for i, name in enumerate(channelNames):
    channel = container(fileNames[i], index=i)
    channels[name] = channel
    channels[name].index = i

# 2) Get raw data from file images
for channel in channels.values():
    ar = transients.LoadTimeData(channel.fileName, timeReversed = True)
    channel.raw = np.asarray(ar)


# 3) Define cellpose model and read in image for cell segmentation
model = models.Cellpose(gpu=False, model_type='cyto2')
data = channels['MCHERRY'].raw[0,:,:]

# 4) Cell Segmentation
# adjust contrast for better segmentation using percentile rescaling
percentiles = np.percentile(data, (0.5, 99.5))
dataAdjusted = exposure.rescale_intensity(data,in_range=tuple(percentiles))

# run cellpose
masks, flows, styles, diams = model.eval(dataAdjusted, diameter=None,do_3D=False,)
numOfCells = np.max(masks)

# Cell coordinates
indices = []
areas = []

for i in range(1, numOfCells + 1):
    index = np.argwhere(masks == i)
    area = len(index)
    indices.append(index)
    areas.append(area)

indices = np.array(indices, dtype=object)
areas = np.array(areas, dtype=object)


# 5) Convert masks to binary format
newMasks = np.zeros_like(masks, int)
newMasks[masks>=1] = 1

for key, channel in channels.items():
    result = channel.raw * newMasks[None,:,:]
    channel.masked = result
    channel.stacked = newMasks

# store segmentation info as region_cells using cellProp object    
region_cells = []

for i in range(numOfCells):
    prop = cellProp(indices[i], areas[i])
    region_cells.append(prop)

channels['channel1'].region_cells = region_cells
channels['channel2'].region_cells = region_cells

# 6) Isolate cells / Record Transients
# get time series data for each cell in each channel
for key in channels.keys():
    channel = channels[key]
    traces, region_cells_MASTER = transients.GetTraces(
                channel.masked,  # time-series data after masking
                channel.stacked, # mask
                region_cells = channel.region_cells,
                channelName = channel.index)
    channel.traces = traces
    channel.region_cells = region_cells



executionTime = time.time() - startTime
print("Execution time: ", executionTime)


"""
    Line to output a csv file:
np.savetxt(outputFileName,traces,delimiter=',')


Lines to do normalization:
valMin=np.min(trace)
valMax=np.max(trace)
traceNorm=(trace-valMin)/(valMax-valMin)

Note that the normalization is done for each individual trace
using the minimum and maximum of that trace
"""
