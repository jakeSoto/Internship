import os, time
import helper
from openpyxl import Workbook


def main():
    start_time = time.time()
    folderDict, dest = helper.searchDirectory()
    imgRoot = os.path.join(dest, "Cells_")
    traceRoot = os.path.join(dest, "Traces_")
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

        # Export data
        for i, channel in enumerate(channels):
            imgName = imgRoot + str(channel) + ".png"
            traceName = traceRoot + str(channel) + ".png"

            normalized = helper.normalizeData(channels[channel].traces)
            dataSet = helper.transposeData(channels[channel].traces)
            helper.saveCellImg(channels[channel].mask, imgName)
            name = "Channel " + str(i+1) + " "
            helper.saveTraces(normalized, name, traceName)
            helper.exportData(sheet, dataSet, name, i+1)


    wb.save(dest)
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print("Done, results save to: " + str(dest))
    print("Execution time: " + str(round(total_time, 1)) + " minutes")


if __name__ == "__main__":
    main()
