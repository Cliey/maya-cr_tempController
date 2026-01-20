# How To compile with pyc

## Get pyc files
`"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -m compileall -b . `
To compile all file of the folder & keep them in the same folde + same naem as py files

=> `C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe` is to ensure we use the right python version.
-> This can be updated later with each right python version (3.10 for Maya 2024)
-> Need to change it for each? or compile for 3.10 and we're good?

## Move pyc files
Use script `movepyc.py`to move all `pyc` file into `compiled/` folder.