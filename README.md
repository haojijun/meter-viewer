# meter-viewer

## Overview:
A noise measure meter which we use has no digital interface or connected software to supply "record" function 
that we have to fix our eyes on the meter panel for 40 minutes during one test case.

Therefore this vision software is developed to solve this problem, which we called metervierer will 
firstly capture the meter panel image from a camera of video file and paly back in the Capture Window, 
then do some image processing by steps to get the noise value and display in the Plot Window.

![](https://raw.githubusercontent.com/haojijun/meter-viewer/master/screenshot/CaptureWindow.PNG)
![](https://raw.githubusercontent.com/haojijun/meter-viewer/master/screenshot/PlotWindow.PNG)

## Features:
1. Capture from Camera or Video File
2. Auto save plot figure as well as capture video in "record" directory default, which can be change from menu "file" -> "set record directory"
3. Auto saved files will be split into several slices auto about every 60 minutes, which to avoid auto saved files being too large
4. The name of auto saved files will have the format of "YYMMDD_hhmmss_n.png" or "YYMMDD_hhmmss_n.avi", in which "n" means slice number
5. "Save as" command will change auto saved files to "newname_n.png" and "newname_n.avi", in which the "new_name" is used entered new filename
6. The black screen "console window" is reserved present to catch any fail messages for debug, which will be remove in latter version
7. Noise Level can be set in conf.ini file


## Usages:


## Files:


## Image Processing:
