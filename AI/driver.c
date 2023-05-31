#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "mac_mod.mac"
//#include "keyPress.cpp"


int main() {
    system("start " "C:\\PROGRA~1\\NIS-Elements2022\\nis_ar.exe" " -mw " "C:\\PROGRA~1\\NIS-Elements2022\\Macros\\testing.mac");
    runMacro();
    return 0;
}

/*
testing() {
    char dir[256] = "C:\\PROGRA~1\\NIS-Elements2022\\nis_ar.exe";
    char args[256] = " -mw Macros\\testing.mac";
    char executable[256] = "";

    strcat(executable, "start ");
    strcat(executable, dir);
    strcat(executable, args);

    system(executable);
}*/