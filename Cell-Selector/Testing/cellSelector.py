import time
import helper
import transients
import numpy as np
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
        else:
            channels = helper.createDict(fileDict[folder])
            sheet = wb.create_sheet(folder, i)

        # 2 Channels
        if (len(channels) < 3):
            channels = helper.processTwoChannels(channels)

        # 3 Channels
        else:
            channels = helper.processThreeChannels(channels)
        
        MCHERRY = channels['mCherry']
        normalized = helper.normalizeData(MCHERRY.traces)

        # Transpose data for export
        MCHERRY.traces = np.array(MCHERRY.traces)
        normalized = np.array(normalized)
        transposed_Traces = MCHERRY.traces.T
        transposed_Norm = normalized.T

        # Export data
        helper.exportData(sheet, transposed_Traces, "Cell ", 1)
        helper.exportData(sheet, transposed_Norm, "Norm ", 2)
        helper.saveCellImg(MCHERRY.mask, (img + str(folder + ".png")))

    wb.save(dest)
    

    """
    # Save cell segmenation img
    plt.figure(figsize=(20,10))
    ax1 = plt.subplot(131)
    ax1.set_title('Selected Cells')
    ax1.imshow(MCHERRY.mask)
    labels=[]

    for i in range(MCHERRY.mask.shape[0]):
        for j in range(MCHERRY.mask.shape[1]):
            if (MCHERRY.mask[i][j] == 0):
                continue
            else:
                if MCHERRY.mask[i][j] not in labels:
                    labels.append(MCHERRY.mask[i][j])
                    ax1.text(j, i, int(MCHERRY.mask[i][j]), ha="center", va="center", fontsize=12, fontweight='black', color='orange')

    plt.savefig(path + 'Cell_Selection.png', bbox_inches='tight')
    """
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print("Done, results save to: " + str(dest))
    print("Execution time: " + str(total_time))


if __name__ == "__main__":
    main()

