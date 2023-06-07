"""
Routines for isolating cells and recording transients 
"""
import util
import scipy
import numpy as np
import skimage.measure
from scipy import ndimage
import matplotlib.pylab as plt


def LoadTimeData(fileName,
                 timeReversed=False, # use if time isn't the first index in tif
                 channelIndex = None, # None if not a multi-channel image; int otherwise
                 clip = None, # if none, use original image size.
                 framesMax = None # if None, load all frames; otherwise int
                 ):

  ar = util.ReadImg(fileName)

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


# collect all non-zero intensity regions as 'cells' (screening comes later) 
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
    cell0 = ar[:, cellProp.coords[:,0], cellProp.coords[:,1] ]  #first index is time
    trace = np.mean(cell0,axis=1)
    return trace


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
  
  # analyze statistics
  renormed = util.renorm(np.log(stack)) # [channel.channel_index])
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

  # passing rtresholded image 
  stacked = img         
  return stacked
