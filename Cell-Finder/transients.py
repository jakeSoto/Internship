"""
Routines for isolating cells and recording transients 
"""
import sys
import os
import numpy as np
import tifffile as tif
#import ipywidgets
from scipy import ndimage
import skimage.measure
import scipy
# I have since moved util.py from matched myo 
#sys.path.append("/u1/huskeypm/sources/hg/mach/matchedmyo")
import util
import matplotlib.pylab as plt


def LoadTimeData(fileName,
                 timeReversed=False, # use if time isn't the first index in tif
                 channelIndex = None, # None if not a multi-channel image; int otherwise
                 clip = None, # if none, use original image size.
                 framesMax = None # if None, load all frames; otherwise int
                 ):
  #arOrig = util.ReadImg(fileName)# ,cvtColor=False) for Seth
  ar= util.ReadImg(fileName)

  # get channel (this is doing something unexpected) - do buncho unit test if i reimplement)
  #if channelIndex is not None:
  #    ar = ar[:, channelIndex, :]

  # iefficient to put here, but oh well 
  if framesMax is None:
    # assuming t is the smallest dimension
    framesMax = np.min(np.shape(ar))
    print("Keeping %d frames"%framesMax)

  # clip image 
  if clip is not None:
    clipy,clipx = clip    
    if timeReversed: 
      ar = ar[   
            clipy[0]:clipy[1], 
            clipx[0]:clipx[1],
            0:framesMax]

    else:
      ar = ar[0:framesMax,
            clipy[0]:clipy[1], 
            clipx[0]:clipx[1]]

  print("poop",np.shape(ar))
      

  #timeReversed = True  # time isn't as first index, so shuffle
  if timeReversed:
    newAr = np.zeros([ar.shape[2],ar.shape[0],ar.shape[1]])
    for i in range( ar.shape[2] ):
        newAr[i,:,:] = ar[:,:,i]
    print("Reversing time index") 
    ar = newAr

  dim = ar.shape
  if dim[1]!=dim[2]:
      print("WARNING: Array s.b. [t,x,y] - double check just in case") 
  print("Returning an array of size", ar.shape)

  return ar


def LoadStaticData(fileName,
                 timeReversed=False, # use if time isn't the first index in tif
                 channelIndex = None, # None if not a multi-channel image; int otherwise
                 clip = None, # if none, use original image size.
                 ):
  
  ar = util.ReadImg(fileName)

  # clip image 
  if clip is not None:
    clipy, clipx = clip    
    if timeReversed: 
      ar = ar[   
            clipy[0]:clipy[1], 
            clipx[0]:clipx[1]
            ]

    else:
      ar = ar[
            clipy[0]:clipy[1], 
            clipx[0]:clipx[1]
            ]

  print("poop", np.shape(ar))
  print("Returning an array of size", ar.shape)
  return ar

# select cells by thresholding 
def FindCells(
        ar, # array of images,
        smoothSize, # kernel for smoothing images,
        thresh, # threshold for cell signal
        output_dir=".",  # directory where figures/output files are saved
        debug=True, # returns with just the stacked/thresholded image 
        channelKey=None# optional channel name 
        ):
  # stack image to get mean positions
  stack = np.sum(ar,axis=0)  # for seth's tif

  # for Surya's tif
  #stack = np.sum(ar,axis=2)  # for seth's tif
  #util.myplot(stack)
  #print(stack.shape)        
  
  # analyze statistics
  renormed =util.renorm(np.log(stack)) # [channel.channel_index])
  if debug:
    plt.figure()
    v = plt.hist(renormed)
    plt.title("Histogram of pixel intensities")
    file_path = os.path.join(output_dir, channelKey+"_histo.png")
    plt.gcf().savefig(file_path) 

  # smooth and threshold image
  smoothed = ndimage.filters.uniform_filter(
          renormed, size=(smoothSize,smoothSize))
  
  # thresh
  img = np.array(smoothed > thresh, dtype=np.int)
  
  # cheating for now to simplify analyses
  # technically can adjust this to 'window out' a region of interest
  testOneCell=False
  if False and testOneCell:  # for seth
      img[0:700,:]=0
      img[900:,:]=0
      img[:,0:1400]=0
  if testOneCell:  # for seth
      #img[:,200:]=0    # x
      #img[200:,]=0    # y
      img[:,0:200]=0    # x
      img[:,300:]=0    # x
      img[0:250,]=0    # y
      1
  
  if debug:
    plt.figure()
    util.myplot(np.flipud( img) ) # flipud so image looks similar to imageJ
    file_path = os.path.join(output_dir, channelKey+"_threshed.png")
    plt.gcf().savefig(file_path)
    #util.myplot( img )

  # passing rtresholded image 
  stacked = img         
  return stacked


#
# collect all non-zero intensity regions as 'cells' (screening comes later) 
#
def GetTraces(ar,   # original data  [n,m,m]
              img,  # thresholded image [m,m] 
              output_dir=".",
              region_cells = None,# use region_cells from another image
              saveImg = False,
              channelName=None, # optional channel name
              segCoords=None): 
    
  # isolate all 'points' 
  if region_cells is None:
    labeled_cells = skimage.measure.label(img)
    region_cells = skimage.measure.regionprops(labeled_cells)
    # if this number is lower than expected, adjust thresholds and review img 
    nCells = np.max(labeled_cells)
    print ("Detected {} total cells.".format(nCells))
    if nCells <1:
      raise RuntimeError("Detected 0 cells; leaving with head in hands")
    
  if saveImg:
      plt.figure()
  
  traces = []
  # can apply size criterion here, by requiring cellProp area to be within
  # user-defined values   
  for i,cellProp in enumerate(region_cells):
      trace = GetTrace(ar,cellProp, channelName=channelName)
      traces.append(trace)

      if saveImg:
          plt.plot( trace, label=i   )
          plt.title(channelName)                
          print("Found %d transients before screening"%(i+1))

  if saveImg: 
    plt.legend(bbox_to_anchor=[1,1])
    print("Saved image called","traces.png") 
    plt.tight_layout()
    file_path = os.path.join(output_dir, "traces.png")
    plt.gcf().savefig(file_path) 
   

  return traces, region_cells 

def GetTrace(ar,cellProp,channelName=None):
    cell0 = ar[:, cellProp.coords[:,0], cellProp.coords[:,1] ]  # first index is time (for seth)
    #cell0 = ar[cellProp.coords[:,0], cellProp.coords[:,1],:]  # first index is time (for surya)
    #print(np.shape(cell0))
    # see all points

    trace = np.mean(cell0,axis=1)  # for seth
    #trace = np.mean(cell0,axis=0)  # for surya
    return trace
  


#
# screen traces based on size, peak height, derivatives etc 
# returns a reduced set of transients that pas the user-provided criteria
#
def ScreenTraces(inpTraces,
    region_cells,
    minCellSize = 500,
    maxCellSize = None,
    minFluctuation = 25, # base on intensity 
    minDerivative = 20.,# based on derivative (looking for rapid upswing, not slow increase)                 
    photoBleachHack=False,
    output_dir=".",
    debug = False
    ):

    traces = np.asarray( inpTraces )

    keepers = range(len( traces) )
    if photoBleachHack:
      for keeper in keepers:
        trace = traces[keeper,:]
        y0=trace[0]
        dT = len(trace)
        slope = (trace[-1] - y0)/(dT-0)
        #print(y0,slope)
        offset = slope*range(dT) + y0
        reNorm = trace-offset
        #plt.plot(reNorm)
        traces[keeper,:] = reNorm
         

    if debug: 
      plt.figure()
      fig,(ax1,ax2) = plt.subplots(2)
    
    seleTracesMap = []
    
    for i,cellProp in enumerate(region_cells) :
        # min/max sizes of cells 
        if debug:
            print("Cell area ", cellProp.area)
        if minCellSize is not None and cellProp.area < minCellSize:
            continue
        if maxCellSize is not None and cellProp.area > maxCellSize:
            continue

        # adjust offset 
        tracei = traces[i,:]
        peakHeight = np.max( tracei) - np.mean( tracei)
        derivi = np.max( np.diff(tracei) ) # (we take max, since looking for one or more rapid transients)

        # peak height
        if debug:
            print("Peak height %f (min %f)"%(peakHeight, minFluctuation))         
        if minFluctuation is not None and peakHeight < minFluctuation : 
            continue

        # derivative (as a measurement of rapid increase in Ca signal/RyR release)
        if debug:
            print("Derivative", derivi) 
        if minDerivative is not None and derivi < minDerivative: 
            continue

        # here draw instantDerivi 
        instantDerivi = np.diff(tracei)

        if debug: 
          print("Kept trace")
          ax1.plot(tracei,label=i) 
          ax1.set_title("transients") 
          ax2.plot(instantDerivi,label=i)
          ax2.set_title("derivatives") 

        # save trace
        seleTracesMap.append( i )

    if debug: 
      plt.tight_layout()
      plt.legend()
      file_path = os.path.join(output_dir, "screened.png")
      plt.gcf().savefig(file_path) 
    #dir(region_cell)    
    
    seleTracesMap = np.asarray( seleTracesMap,int )
    #print("traces map",np.shape(seleTracesMap))

    return seleTracesMap


