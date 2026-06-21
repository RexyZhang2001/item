Set WshShell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
batPath = scriptDir & "\启动赤瞳平台.bat"
WshShell.CurrentDirectory = scriptDir
WshShell.Run """" & batPath & """", 1, False
