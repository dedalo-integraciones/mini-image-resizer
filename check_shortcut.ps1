$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("C:\Users\Nelson\Desktop\Mini Image Resizer.lnk")
Write-Host "Target:" $shortcut.TargetPath
Write-Host "Icon:" $shortcut.IconLocation
Write-Host "WorkingDir:" $shortcut.WorkingDirectory
