Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonw = "D:\Python311\pythonw.exe"
If Not fso.FileExists(pythonw) Then
    pythonw = "pythonw.exe"
End If

WshShell.Run Chr(34) & pythonw & Chr(34) & " " & Chr(34) & currentDir & "\main.py" & Chr(34), 0, False
