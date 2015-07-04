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
* Can capture from camera or video file
* While recording the Plot window is update once per second, means just simply pick the most common one value form values during one second.
* The image processing does not deal with '-', '.' as well as the unit of noise value, 
for "-40.7" it just use "407" multiplied with "-0.1" and assume that the unit is dBm simply.
* Auto save plot figure as well as captured video in default "record" directory, which can be change from menu "file" -> "set record directory"
* Auto saved files will be split into several slices about every 60 minutes, which to avoid auto saved files being too large
* The name of auto saved files will have the format of "YYMMDD_hhmmss_n.png" and "YYMMDD_hhmmss_n.avi", 
in which "YYMMDD_hhmmss" means record start time and "n" means slice number
* "Save as" command will change auto saved files to "newname_n.png" and "newname_n.avi", in which the "new_name" is the entered new filename
* The auto saved captured video files may spend much disk space, you can delete the unused ones manually.
* The console window which is black is reserved to catch any failure messages for debug, which will be removed in latter version
* Noise Level can be set in conf.ini file and the default set is -40.0 dBm

## Usages:
The meterviewer.zip contains all the essential files that this software can be run in Windows, just extract it and double click the meterviewer.exe. 
The demo.mp4 can be used for test.

1. Open *Camera* or *Video File* from MENU command
1.1 There is an open camera command in the TOOLBAR which will just open the default camera, for camera selection please use MENU command.

2. Zoom and Pan the meter panel image form TOOLBAR command if necessary
2.1 A green rectangular will appear around the numbers, which means the numbers have been sucessfully detected.
2.2 It will also display some infomation in STATUSBAR, for noise value of "-40.7 dBm" may just display numbers of "407" simplified.

3. Start Record from TOOLBAR command
3.1 This will Record and Plot the values in Plot Window.
3.2 For capture from video file, this record command will be auto trigged when video file is opened.

4. Stop Record from TOOLBAR command
4.1 This will Stop recording the values in Plot Window.
4.2 While recording the plot figure and captured video will be auto saved in default "records" directory.
4.2 For capture form video file, this stop cammand will be auto trigged when video file is end.

5. Save as from MENU or TOOLBAR command if necessary
5.1 This will change the auto saved files(\*.avi and \*.png) with new entered name.


