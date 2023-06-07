import os
import sys
import cv2
import numpy as np
import tifffile as tif
import matplotlib.pylab as plt


### Create an empty instance of a class
class empty:
  pass

root = "myoimages/"
thisFileRoot = '/'.join(os.path.realpath(__file__).split('/')[:-1])

###################################################################################################
###
### Functions for Convenience
###
###################################################################################################
def myplot(img,fileName=None,clim=None):
  plt.axis('equal')
  plt.pcolormesh(img, cmap='gray')
  plt.colorbar()
  if fileName!=None:
    plt.gcf().savefig(fileName,dpi=300)
  if clim!=None:
    plt.clim(clim)

def ReadImg(
        fileName,cvtColor=True,renorm=False,
        bound=False, dataType = np.float32):
  ### Check to see what the file type is
  fileType = fileName[-4:]

  ### make sure the file exists, first and foremost
  assert os.path.isfile(fileName), "The file, {}, does not exist. Check for mistakes in inputs.".format(fileName)

  if fileType == '.tif':
    ## Read in image
    try:
      img = tif.imread(fileName)
    except:
      ### If it exists, then it's an issue with reading it in.
      raise RuntimeError("Loading of image {} threw an error. This is likely due to a data type issue. ".format(fileName)
                         +"Try converting the image data type to 32 bit float instead.")

    ## Check dimensionality of image. If image is 3D, we want to roll the z axis to the last position since 
    ##   tifffile reads in the z-stacks in the first dimension.
    if len(np.shape(img)) == 3:
      img = np.moveaxis(img,source=0,destination=2)

  elif fileType == '.png':
    ## Read in image
    img = cv2.imread(fileName)

    ## Check that an image was actually read in
    if img is None:
        raise RuntimeError(fileName+" likely doesn't exist")

    ## Convert to grayscale
    if cvtColor:
      img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ## Check if the image is bounded
    if bound != False:
      img=img[bound[0]:bound[1],bound[0]:bound[1]]

  else:
    raise RuntimeError("File type is not understood. Please use a .png or .tif file.")

  ### Normalize the image to have maximum value of 1.
  if renorm:
    img = np.divide(img.astype(float),np.float(np.amax(img)))

  ### Conver the data type of the image to the one that is specified
  img = img.astype(dataType)
  
  return img 

###################################################################################################
###
### Functions for Image Manipulation
###
###################################################################################################
def renorm(img,scale=255):
    img = img-np.min(img)
    img/= np.max(img)
    img*=scale 
    return img
