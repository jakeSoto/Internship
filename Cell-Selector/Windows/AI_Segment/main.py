import os, time
import helper
from openpyxl import Workbook


def main():
    start_time = time.time()
    folderDict, dest = helper.searchDirectory()
    tifDest = os.path.join(dest, "segment.tif")
    channels = {}

    for i, folder in enumerate(folderDict):
        if (folderDict[folder] == []):
            continue

        # Get container objects for channels in each folder
        else:
            channels = helper.createChannelDict(folderDict[folder])

        channels = helper.processChannels(channels, tifDest)

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print("Done, results save to: " + str(dest))
    print("Execution time: " + str(round(total_time, 1)) + " minutes")


if __name__ == "__main__":
    main()
