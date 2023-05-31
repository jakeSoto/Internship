#include <stdlib.h>
#include <stdio.h>
#include <string.h>
//#include "mac_mod.mac"
//#include "keyPress.cpp"


int main() {
    char dir[256] = "C:\\PROGRA~1\\NIS-Elements2022\\nis_ar.exe";
    char args[256] = " -mw Macros\\testing.mac";
    char executable[256] = "";

    strcat(executable, "start ");
    strcat(executable, dir);
    strcat(executable, args);

    system(executable);

    return 0;
}
