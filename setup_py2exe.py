from distutils.core import setup
import py2exe
from glob import glob
import sys
import matplotlib
import datetime
import shutil
import zlib

#this allows to run it with a simple double click.
#sys.argv.append('py2exe')
if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")

# Remove the build folder
shutil.rmtree("build", ignore_errors=True)

# do the same for dist folder
shutil.rmtree("dist", ignore_errors=True)

# http://stackoverflow.com/questions/10060765/create-python-exe-without-msvcp90-dll
sys.path.append( "Microsoft.VC90" )


manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="X86"
            publicKeyToken="1fc8b3b9a1e18e3b"
            language="*"
        />
    </dependentAssembly>
</dependency>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "0.1.0"
        self.company_name = "No Company"
        self.copyright = "no copyright"
        self.name = "meter viewer"

mv = Target(
    # used for the versioninfo resource
    description = "A python application",

    # what to build
    script = "mainwindow.py",
    other_resources = [ (24, 1,
                         manifest_template % dict(prog="meterviewer") ) ],
    icon_resources = [ (1, "mv.ico") ],
    dest_base = "meterviewer", # means meterviewer.exe
    )

data_files = [ ( "icon", glob(r'icon\*.*') ),
               ( ".", glob(r'conf.ini') ),
               ( "records", "" ),
               #( ".", glob(r'demo.avi') ),
               ( ".", glob(r'Microsoft.VC90\*.*') ),
               ( ".", glob(r'C:\Python27\opencv_ffmpeg2410.dll') ),       
               ]
data_files += matplotlib.get_py2exe_datafiles()

includes =[]
excludes = [ "_gtkagg", "_tkagg", 'tcl', 'Tkinter']
dll_excludes = [ "libgdk-win32-2.0-0.dll",
                 "libgdk_pixbuf-2.0-0.dll",
                 "libgobject-2.0-0.dll",
                 "tcl84.dll",
                 "tk84.dll",
                 "w9xpopen.exe",
                 ]
packages = []
options = {'py2exe': { "compressed": 1,
                       "optimize": 2,
                       "bundle_files": 3, #1 cannot work fine
                       "includes": includes,
                       "excludes": excludes,
                       "dll_excludes": dll_excludes,
                       "packages": packages,
                       #"dist_dir": "meterviewer-0.1",
                       }
           }

setup(
    zipfile=None,
    options=options,
    data_files=data_files,
    console = [ mv ],
    )


# Remove the build folder
shutil.rmtree("build", ignore_errors=True)
