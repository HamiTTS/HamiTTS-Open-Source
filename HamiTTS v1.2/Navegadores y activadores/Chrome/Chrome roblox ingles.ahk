~/:: {
    ih := InputHook("V", "{Enter}{Esc}")
    ih.Start(), KeyWait("Enter", "D"), ih.Stop()
    
    if (ih.EndReason = "EndKey" && ih.Input != "") {
        A_Clipboard := ih.Input
        Sleep(50)
        WinExist("ahk_exe chrome.exe") ? WinActivate() : Run("chrome.exe")
        if WinWaitActive("ahk_exe chrome.exe", , 2) {
            Send("^a")
            Sleep(30)
            Send("{Backspace}")
            Sleep(50)
            Send("^v")
            Sleep(50) 
            Send("^{Enter}")
            hora := FormatTime(, "HH:mm:ss")
            FileAppend(hora . A_Tab . ih.Input . "`n", A_ScriptDir "\..\..\historial_tts.txt")
            Sleep(100), WinMinimize()
            if WinExist("ahk_exe RobloxPlayerBeta.exe")
                WinActivate()
        }
    }
}