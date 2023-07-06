import time
import helper
from openpyxl import Workbook


def main():
    start_time = time.time()
    fileDict, dest = helper.searchDirectory()
    img = str(dest + "/Cell_img_")
    dest += "/Cell_data.xlsx"
    channels = {}
    wb = Workbook()

    for i, folder in enumerate(fileDict):
        if (fileDict[folder] == []):
            continue

        # Get container object for channels in folder
        else:
            channels = helper.createChannelDict(fileDict[folder])
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
        helper.saveCellImg(MCHERRY.mask, (img + str(folder + ".png")))

    wb.save(dest)
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print("Done, results save to: " + str(dest))
    print("Execution time: " + str(round(total_time)) + " minutes")


if __name__ == "__main__":
    main()

