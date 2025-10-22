' RadiKal Silent Startup Script
' Starts backend and frontend without showing terminal windows

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Show loading message
MsgBox "Starting RadiKal..." & vbCrLf & vbCrLf & _
       "Backend: http://localhost:8000" & vbCrLf & _
       "Frontend: http://localhost:3000" & vbCrLf & vbCrLf & _
       "Please wait 15-20 seconds for services to start." & vbCrLf & _
       "Your browser will open automatically.", _
       vbInformation, "RadiKal Startup"

' Start Backend silently (no window)
strBackendCmd = "cmd /c cd /d """ & strScriptPath & "\backend"" && python main.py"
objShell.Run strBackendCmd, 0, False

' Wait 10 seconds for backend to initialize
WScript.Sleep 10000

' Start Frontend silently (no window)
strFrontendCmd = "cmd /c cd /d """ & strScriptPath & "\frontend"" && npm run dev"
objShell.Run strFrontendCmd, 0, False

' Wait 5 more seconds for frontend to start
WScript.Sleep 5000

' Open browser
objShell.Run "http://localhost:3000"

' Success message
MsgBox "RadiKal is now running!" & vbCrLf & vbCrLf & _
       "Services:" & vbCrLf & _
       "  Frontend: http://localhost:3000" & vbCrLf & _
       "  Backend: http://localhost:8000" & vbCrLf & _
       "  API Docs: http://localhost:8000/api/docs" & vbCrLf & vbCrLf & _
       "To stop: Use Task Manager to end 'python.exe' and 'node.exe' processes", _
       vbInformation, "RadiKal Ready"
