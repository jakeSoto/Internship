import os, time
import helper
from openpyxl import Workbook


def main():
    start_time = time.time()
    fileDict, dest = helper.getFiles()

    sheetName = os.path.split(dest)[1]
    if (len(sheetName) > 30):
        sheetName = sheetName[0:30]
    wb = Workbook()
    sheet = wb.create_sheet(sheetName, 1)

    imgName = os.path.join(dest, "Cell_Selection.png")
    dest = os.path.join(dest, "Cell_Data.xlsx")
    channels = {}

    # Run program
    channels = helper.createChannelDict(fileDict)
    channels = helper.processChannelData(channels)

    # Export Mask Image
    helper.saveCellImg(channels[list(channels.keys())[0]].mask, imgName)

    # Export cell flourescence traces to xlsx
    for j, channel in enumerate(channels):
        if(channels[channel].static == True):
            helper.exportStaticData(sheet, channels[channel].traces, str(channel), j+1)

        else:
            dataSet = helper.transposeData(channels[channel].traces)
            helper.exportData(sheet, dataSet, str(channel)+" ", j+1)

    wb.save(dest)
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print("Done, results save to: " + str(dest))
    print("Execution time: " + str(round(total_time, 1)) + " minutes")


if __name__ == "__main__":
    main()
