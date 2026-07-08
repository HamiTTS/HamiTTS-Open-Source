~/:: {
    ih := InputHook("V", "{Enter}{Esc}")
    ih.Start(), KeyWait("Enter", "D"), ih.Stop()
    
    if (ih.EndReason = "EndKey" && ih.Input != "") {
        A_Clipboard := ih.Input
        Sleep(50)
        WinExist("ahk_exe opera.exe") ? WinActivate() : Run("opera.exe")
        if WinWaitActive("ahk_exe opera.exe", , 2) {
            Send("^a")
            Sleep(30)
            Send("{Backspace}")
            Sleep(50)
            Send("^v")
            Sleep(50) 
            Send("^{Enter}")
            Sleep(100), WinMinimize()
            if WinExist("ahk_exe RobloxPlayerBeta.exe")
                WinActivate()
        }
    }
}