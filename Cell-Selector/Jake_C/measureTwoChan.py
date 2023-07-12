import os, time
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
            channels = helper.processTwoChannels(channels, measuredName)

        # 3 Channels
        else:
            channels = helper.processThreeChannels(channels, measuredName)

        MCHERRY = channels['mCherry']
        normalized = helper.normalizeData(MCHERRY.traces)

        # Export data
        helper.exportData(sheet, normalized, "Norm ", 3)
        helper.exportData(sheet, MCHERRY.traces, "Cell ", 4)

        temp_counter = 1
        for key, channel in channels.items():
            if (key == "mCherry"):
                continue
            else:
                helper.exportStaticData(sheet, channel.traces, str(key+" "), temp_counter)
                temp_counter += 1
        temp_counter = 0


        imgName = imgRoot + str(folder) + ".png"
        helper.saveCellImg(MCHERRY.mask, imgName)

    wb.save(dest)
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print("Done, results save to: " + str(dest))
    print("Execution time: " + str(round(total_time, 1)) + " minutes")


if __name__ == "__main__":
    main()
