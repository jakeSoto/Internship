var path = "";

path = getDirectory();



// Functions
function createMask(path) {
	open(path + "AI.ome.tif");
	run("Red");
	run("8-bit");
	run("Auto Local Threshold", "method=Bernsen radius=3 parameter_1=0 parameter_2=0 white stack");
	run("Bandpass Filter...", "filter_large=1000 filter_small=6 suppress=None tolerance=5 autoscale process");
	run("32-bit");
	setAutoThreshold("Default dark");
	run("NaN Background", "stack");
	run("Divide...", "value=255 stack");
	run("Enhance Contrast", "saturated=0.35");
	run("Enhance Contrast", "saturated=0.35");
	run("Enhance Contrast", "saturated=0.35");
	saveAs("Tiff", path + "mask");
}


function step2(path) {
	open(path + "CFP.tif");
	run("32-bit");
	run("Enhance Contrast", "saturated=0.35");
	imageCalculator("Multiply create stack", "mask.tif", "CFP.tif");
	saveAs("Tiff", path + "MultipliedImagewithCFP");
	close("MultipliedImagewithCFP.tif");
	close("CFP.tif");
}


function step3(path) {
	open(path + "YFP.tif");
	run("32-bit");
	run("Enhance Contrast", "saturated=0.35");
	imageCalculator("Multiply create stack", "mask.tif", "YFP.tif");
	saveAs("Tiff", path + "MultipliedImagewithYFP");
	close("MultipliedImagewithYFP.tif");
	close("YFP.tif");
}


function step4(path) {
	open(path + "FRET.tif");
	run("32-bit");
	run("Enhance Contrast", "saturated=0.35");
	imageCalculator("Multiply create stack", "mask.tif", "FRET.tif");
	saveAs("Tiff", path + "MultipliedImagewithFRET");
	close("MultipliedImagewithFRET.tif");
	close("FRET.tif");
}


function step5(path) {
	open(path + "MultipliedImagewithCFP.tif");
	run("Smooth", "stack");
	selectWindow("MultipliedImagewithCFP.tif");
	run("Enhance Contrast", "saturated=0.35");
	setAutoThreshold("Default dark");
	run("Threshold...");
	setThreshold(250, 35000);
	run("Analyze Particles...", "size=1000-10000 circularity=0.00-1.00 display clear add stack");
	selectWindow("MultipliedImagewithCFP.tif");
	close();
	
	selectWindow("Results");
	saveAs("txt", path + "Cer_results");
	close("Results");
}


function step6(path) {
	open(path + "MultipliedImagewithYFP.tif");
	selectWindow("MultipliedImagewithYFP.tif");
	roiManager("Select", 1);
	roiManager("Deselect");
	roiManager("Add");
	roiManager("Measure");
	selectWindow("Results");
	saveAs("txt", path + "YFP_Results");
	close("Results");
	selectWindow("MultipliedImagewithYFP.tif");
	close();
}


function finalStep(path) {
	open(path + "MultipliedImagewithFRET.tif");
	selectWindow("MultipliedImagewithFRET.tif");
	roiManager("Select", 1);
	roiManager("Deselect");
	roiManager("Add");
	roiManager("Measure");
	selectWindow("Results");
	saveAs("txt", path + "FRET_Results");
	close("Results");
}
