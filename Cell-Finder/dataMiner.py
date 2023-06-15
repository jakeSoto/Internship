import transients
import libs


class container():
  def __init__(self,fileName,
                    index = None,# none- single channel image; int otherwise
                    raw = None, # array of data; usually leave undefined 
                    mask = None, # array of cells locations
                    binaryMask = None  # binary array of cells within the img
                    ):
    self.fileName = fileName
    self.index = index
    self.raw = raw
    self.mask = mask
    self.binaryMask = binaryMask


def main():
  path = filedialog.askdirectory()
  path += "/"
  fileNames = ["CFP.tif", "GFP.tif", "mCherry.tif"]
  channelNames = ["CFP", "GFP", "MCHERRY"]

  # create a dictionary to store channel info
  channels = {}
  for i, name in enumerate(channelNames):
      channel = container(fileNames[i], index=i)
      channels[name] = channel
      channels[name].channel_index = i

  # references
  CFP = channels['CFP']
  GFP = channels['GFP']
  MCHERRY = channels['MCHERRY']


  # get raw data from images
  for channel in channels.values():
    print("processing " + channel.fileName)

    if (channel == MCHERRY):
      ar = transients.LoadTimeData(path + channel.fileName, timeReversed = True)
    else:
      ar = transients.LoadStaticData(path + channel.fileName, timeReversed = True)
    
    channel.raw = np.asarray(ar)


  # define cellpose model and run cellpose to find channel masks
  model = models.Cellpose(gpu=False, model_type='cyto2')

  for channel in channels.values():
      if (channel == MCHERRY):
          data = channel.raw[0, :, :]
      else:
          data = channel.raw[:, :]
      
      print("Processing mask for: " + channel.fileName)
      masks, flows, styles, diams = model.eval(data, diameter=None, do_3D=False, )
      channel.mask = masks


  # convert masks to binary format
  for key, channel in channels.items():
      channel.binaryMask = np.zeros_like(channel.mask, int)
      channel.binaryMask[channel.mask > 0] = 1


  # find cells only expressed in all three channels
  combo_BinaryMask = CFP.binaryMask + GFP.binaryMask + MCHERRY.binaryMask

  final_BinaryMask = np.zeros_like(combo_BinaryMask, int)
  final_BinaryMask[combo_BinaryMask == 3] = 1

  dataSet = final_BinaryMask * MCHERRY.raw


  # get cell coordinates

  

  # get time series data for selected cells in all three channels
  traces, region_cells = transients.GetTraces(
                dataSet,        # time-series data after masking
                final_BinaryMask,  # mask
                )


  # Normalize data
  normalized = [None] * len(traces)

  for i in range(len(traces)):
      trace = traces[i]
      minVal = np.min(trace)
      maxVal = np.max(trace)
      norm = (trace - minVal) / (maxVal - minVal)

      normalized[i] = norm


  # Save Results
  transposed_traces = list(map(list, zip(*traces)))
  transposed_norm = list(map(list, zip(*normalized)))
  wb = Workbook()
  sheet = wb.active

  # Traces
  for i, sublist in enumerate(transposed_traces):
      for j, item in enumerate(sublist):
          header = sheet.cell(row = 1, column = (j*4)+1)
          header.value = ("Cell " + str(j+1))

          cell = sheet.cell(row = i+2, column = (j*4)+1)
          cell.value = item

  # Normalization
  for i, sublist in enumerate(transposed_norm):
      for j, item in enumerate(sublist):
          header = sheet.cell(row = 1, column = (j*4)+2)
          header.value = ("Norm " + str(j+1))

          cell = sheet.cell(row = i+2, column = (j*4)+2)
          cell.value = item


  destFile = (path + "test(1).xlsx")
  wb.save(destFile)
  print("Done, results save to: " + str(destFile))


main()