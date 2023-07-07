import os
import time
import helper
from openpyxl import Workbook


def main():
    start_time = time.time()
    folderDict, dest = helper.searchDirectory()
    imgRoot = os.path.join(dest, "Cells_")
    dest = os.path.join(dest, "Cell_Data.xlsx")
    channels = {}
    wb = Workbook()

    for i, folder in enumerate(folderDict):
        if (folderDict[folder] == []):
            continue

        # Get container objects for channels in each folder
        else:
            channels = helper.createChannelDict(folderDict[folder])
            sheet = wb.create_sheet(folder, i)

        # 2 Channels
        if (len(channels) < 3):
            channels = helper.processTwoChannels(channels)

        # 3 Channels
        else:
            channels = helper.processThreeChannels(channels)

        MCHERRY = channels['mCherry']
        normalized = helper.normalizeData(MCHERRY.traces)

        # Export data
        helper.exportData(sheet, MCHERRY.traces, "Cell ", 1)
        helper.exportData(sheet, normalized, "Norm ", 2)

        imgName = imgRoot + str(folder) + ".png"
        helper.saveCellImg(MCHERRY.mask, (imgRoot + imgName))

    wb.save(dest)
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print("Done, results save to: " + str(dest))
    print("Execution time: " + str(round(total_time, 1)) + " minutes")


if __name__ == "__main__":
    main()
