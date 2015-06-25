from distutils.core import setup
import py2exe
from glob import glob
import sys
import matplotlib

sys.path.append("Microsoft.VC90.CRT")


data_files = [ ( "icon", glob(r'icon\*.*') ),
               ( ".", glob(r'conf.ini') ),
               ( "records", "" ),
               ( ".", glob(r'Microsoft.VC90.CRT\*.*') ),
               ( ".", glob(r'C:\Python27\opencv_ffmpeg*.*') ),
               ( "demo", glob(r'demo.avi') ),
               ]
data_files += matplotlib.get_py2exe_datafiles()

includes =[]
excludes = [ "_gtkagg", "_tkagg", 'tcl', 'Tkinter']
dll_excludes = [ "libgdk-win32-2.0-0.dll",
                 "libgdk_pixbuf-2.0-0.dll",
                 "tcl84.dll",
                 "tk84.dll",
                 "w9xpopen.exe",
                 ]

options = {'py2exe': { "compressed": 1,
                       "optimize": 2,
                       #"bundle_files": 1,
                       "includes": includes,
                       "excludes": excludes,
                       "dll_excludes": dll_excludes,
                       #"dist_dir": "meterviewer-0.1",
                       }
           }
    

setup(
    zipfile=None,
    console=[ { "script": "mainwindow.py",
                "icon_resources": [(1,'./icon/mv.ico')]
                } ],
    options=options,
    data_files=data_files,
    version="0.1",
    description="a python software",
    name="meterviewer.",
    )
