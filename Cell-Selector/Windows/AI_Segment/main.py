import os, time
import helper
from openpyxl import Workbook


def main():
    start_time = time.time()
    
    filePath, dest = helper.getFile()
    tifDest = os.path.join(dest, "segment.tif")

    channel = helper.createChannelContainer(filePath)
    channel = helper.processChannelData(channel, tifDest)

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print("Done, results save to: " + str(dest))
    print("Execution time: " + str(round(total_time, 1)) + " minutes")


if __name__ == "__main__":
    main()
