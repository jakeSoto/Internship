//#include <iostream>
#include <Windows.h>


void pressEnter() {
	INPUT input;
	input.type = INPUT_KEYBOARD;
	input.ki.time = 0;
    input.ki.dwFlags = KEYEVENTF_UNICODE;
    input.ki.wScan = VK_RETURN; //VK_RETURN is the code of Return key
    input.ki.wVk = 0;

    input.ki.dwExtraInfo = 0;
    SendInput(1, &input, sizeof(INPUT));
}