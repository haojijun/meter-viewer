import os
import wx
import cv2
import sys

from wx.lib.wordwrap import wordwrap
import matplotlib
matplotlib.use('wxagg') #before import pyplot

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from collections import Counter
import ConfigParser
import datetime
import string
import unicodedata

from imagezoom import image_zoom
from getnumber import getnumber

#global setting
noise_level = -40.0
record_minutes_max = 0.25 #max 60, the autosave.avi should < 2GB
#capture window size
cols = 640 
rows = 360
DEBUG_MODE = False
validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

#global variables
val_list = []
val_list_bar = []


#-----------------------------------------------------------------
# www.py2exe.org/index.cgi/WhereAmI

def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""
    return hasattr( sys, "frozen" )

def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))

    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))

#-----------------------------------------------------------------

"""
1. if there "number" or "CAL" or "OFF", select most common
2. if there only "ERR", then error
3. how to deal with only has one wrong number?
"""
#func use only
val_list_tmp = []
def valuefilter( value_in, frame=0, len_max=10 ):
    global val_list, val_list_tmp, val_list_bar

    if frame == 0:
        val_list = []
        val_list_bar = []
        
    if frame % len_max == 0:
        val_list_tmp = []
        
    val_list_tmp.append( value_in )
    
    if ( frame + 1 ) % len_max == 0:
        def f(x): return x[0]==1
        val_list_f = filter( f, val_list_tmp )
        if len(val_list_f) >= 0.5*len_max:
            val_most = Counter( val_list_f ).most_common( 1 )[0][0]
            #print val_most[1]
            if val_most[1] != "CAL" and val_most[1] != "OFF":
                val_float = float( val_most[1] ) / -10.0 #"-888.8dBm"
                val_list.append( val_float )
                if val_float > noise_level:
                    val_list_bar.append( [None, None, noise_level] )
                else:
                    val_list_bar.append( [noise_level, None, None] )
            else:
                val_list.append( None )
                val_list_bar.append( [noise_level, None, None] )
        else:
            val_list.append( None )
            val_list_bar.append( [None, noise_level, None] )
            #print "filter Error!", len(val_list_f)
            #for err in val_list_tmp:
                #print err
            
    return
        
#------------------------------------------------------- 

class PlotFigure( wx.Frame ):
    """ Matplotlib wxFrame with animation effect """
    def __init__( self, parent, title ):
        wx.Frame.__init__( self, parent, title=title, size=(720,405) )
        self.fig = Figure( (6,4), 100 )
        self.canvas = FigureCanvas( self, wx.ID_ANY, self.fig )
        #self.ax = self.fig.add_subplot(111)
        self.ax = self.fig.add_axes( [0.12, 0.15, 0.81, 0.76] )
        self.onClearDraw()

    def onClearDraw( self ):
        self.ax.clear()
        self.ax.set_ylim( [-200, 0] )
        self.ax.set_xlim( [0, 1] ) #x display minutes
        self.ax.set_autoscale_on(False)
        self.ax.set_yticks( range(0, -200, -10) )
        #self.ax.grid(True)
        self.ax.set_xlabel( r'Recording time (minutes)' )
        self.ax.set_ylabel( r'Noise value (dBm)' )
        self.ax.text( 0, noise_level+10, r'Noise Level: ' + str(noise_level) + r' dBm' )
        self.line, = self.ax.plot( [], [], color='blue', label='Values',
                                   lw=1 ) # value
        self.line_g, = self.ax.plot( [], [], color='green', \
                                     linestyle='--', label='Normal',
                                     lw=1 ) # number, CAL, OFF
        self.line_y, = self.ax.plot( [], [], color='yellow', \
                                     linestyle='--', marker='d',
                                     label='Miss', lw=1 ) # ERR
        self.line_r, = self.ax.plot( [], [], color='red', \
                                     linestyle=':', label='Over',
                                     marker=6, lw=1 ) # over alarm
        self.ax.legend()
        self.canvas.draw()
        self.bg = self.canvas.copy_from_bbox( self.ax.bbox )
        
    def onUpdate( self ):
        #self.canvas.restore_region( self.bg )
        xmin, xmax = self.ax.get_xlim()
        if len(val_list) >= 60*xmax:
            self.ax.set_xlim(xmin, int(1.5*xmax)+1 ) # int(1.5)=1
            self.canvas.draw()
        x_minutes = [ s/60.0 for s in range( len( val_list ) ) ]
        self.line.set_data( x_minutes, val_list )
        self.line_g.set_data( x_minutes, [ v[0] for v in val_list_bar ] )
        self.line_y.set_data( x_minutes, [ v[1] for v in val_list_bar ] )
        self.line_r.set_data( x_minutes, [ v[2] for v in val_list_bar ] )
        self.ax.draw_artist( self.line )
        self.ax.draw_artist( self.line_g )
        self.ax.draw_artist( self.line_y )
        self.ax.draw_artist( self.line_r )
        self.canvas.blit( self.ax.bbox )
#------------------------------------------------------- 

class MainWindow( wx.Frame ):
    def __init__( self, parent, title ):
        wx.Frame.__init__( self, parent, title=title, size=wx.DefaultSize )
        # control variables
        self.capturetype = None
        self.zoom_param = 5*[0]
        self.record = 0
        self.fps = 0
        self.framenumber = 0
        #auto save recorddir+recordname+recordslice+mp4/png
        #slice=0 start a new recordname
        self.recorddir = None
        self.recordname = None
        self.recordslice = 0
        self.videowriter = None

        # StatusBar
        self.CreateStatusBar()
        self.StatusBar.SetFieldsCount(3)
        self.StatusBar.SetStatusWidths( [-4, -1, -3] )
        self.StatusBar.SetStatusText( "IDLE", 0 )

        # MenuBar
        menuBar = wx.MenuBar()
        # 1st menu from left
        menu1 = wx.Menu()
        menu1.Append(101, "&Open Camera", "Open Camera Dialog")
        menu1.Append(102, "&Open File...", "Open Video File Dialog")
        menu1.AppendSeparator()
        menu1.Append(103, "&Save As...", "Save the auto saved file with a new name" )
        menu1.AppendSeparator()
        menu1.Append(104, "&Set Record Dir", "Set the auto save directory")
        menu1.Append(105, "&Open Record Dir", "Open the auto save directory" )
        menu1.AppendSeparator()
        menu1.Append(106, "&Exit", "Close this Application")
        menuBar.Append(menu1, "&File")
        # 2nd menu from left
        menu2 = wx.Menu()
        menu2.Append(201, "About")
        menuBar.Append(menu2, "&Help")
        # Menu events
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.OnOpenCam, id=101)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, id=102)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, id=103)
        self.Bind(wx.EVT_MENU, self.OnSetRecordDir, id=104)
        self.Bind(wx.EVT_MENU, self.OnOpenRecordDir, id=105)
        self.Bind(wx.EVT_MENU, self.OnCloseWindow, id=106)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=201)
        # menu init
        self.MenuBar.Enable( 101, True ) #same as toolbar 10
        self.MenuBar.Enable( 102, True ) #same as toolbar 10
        self.MenuBar.Enable( 103, False ) #same as toolbar 13
        
        
        # Tool Bar
        tb = self.CreateToolBar()
        tsize = (16,16)
        # icons
        bmp_cam = wx.Bitmap("icon/camera.png", wx.BITMAP_TYPE_PNG )
        bmp_record = wx.Bitmap("icon/record.png", wx.BITMAP_TYPE_PNG)
        bmp_stop = wx.Bitmap("icon/stop.png", wx.BITMAP_TYPE_PNG)
        bmp_saveas = wx.ArtProvider.GetBitmap( wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, tsize )
        bmp_plot = wx.Bitmap("icon/plot.png", wx.BITMAP_TYPE_PNG)
        bmp_zoomhome = wx.Bitmap("icon/zoomhome.png", wx.BITMAP_TYPE_PNG)
        bmp_zoomin = wx.Bitmap("icon/zoomin.png", wx.BITMAP_TYPE_PNG)
        bmp_zoomout = wx.Bitmap("icon/zoomout.png", wx.BITMAP_TYPE_PNG)
        bmp_panup = wx.ArtProvider.GetBitmap( wx.ART_GO_UP, wx.ART_TOOLBAR, tsize )
        bmp_pandown = wx.ArtProvider.GetBitmap( wx.ART_GO_DOWN, wx.ART_TOOLBAR, tsize )
        bmp_panleft = wx.ArtProvider.GetBitmap( wx.ART_GO_BACK, wx.ART_TOOLBAR, tsize )
        bmp_panright = wx.ArtProvider.GetBitmap( wx.ART_GO_FORWARD, wx.ART_TOOLBAR, tsize )
        bmp_rotate = wx.ArtProvider.GetBitmap( wx.ART_REDO, wx.ART_TOOLBAR, tsize )
        bmp_rotatec = wx.ArtProvider.GetBitmap( wx.ART_UNDO, wx.ART_TOOLBAR, tsize )   
        # add toolbar and bind event
        tb.SetToolBitmapSize( tsize )
        tb.AddSimpleTool( 10, bmp_cam, "Open", "Quick Open the Default Camera" )
        self.Bind( wx.EVT_TOOL, self.OnOpenCam, id=10 )
        tb.AddSimpleTool( 11, bmp_record, "Record", "Start Record the Noise Value" )
        self.Bind( wx.EVT_TOOL, self.OnRecord, id=11 )
        tb.AddSimpleTool( 12, bmp_stop, "Stop", "Stop Record" )
        self.Bind( wx.EVT_TOOL, self.OnStop, id=12 )
        tb.AddSimpleTool( 13, bmp_saveas, "Save As", "Change the autosave record file name" )
        self.Bind( wx.EVT_TOOL, self.OnSaveAs, id=13 )  
        tb.AddSimpleTool( 14, bmp_plot, "Plot", "Show plot window" )
        self.Bind( wx.EVT_TOOL, self.OnPlot, id=14 )
        tb.AddSeparator()
        tb.AddSimpleTool( 20, bmp_zoomhome, "Zoom home", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=20 )
        tb.AddSimpleTool( 21, bmp_zoomin, "Zoom in", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=21 )
        tb.AddSimpleTool( 22, bmp_zoomout, "Zoom out", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=22 )
        tb.AddSimpleTool( 23, bmp_panup, "Pan up", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=23 )
        tb.AddSimpleTool( 24, bmp_pandown, "Pan down", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=24 )
        tb.AddSimpleTool( 25, bmp_panleft, "Pan left", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=25 )
        tb.AddSimpleTool( 26, bmp_panright, "Pan right", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=26 )
        tb.AddSimpleTool( 27, bmp_rotate, "Rotate clockwise", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=27 )
        tb.AddSimpleTool( 28, bmp_rotatec, "Rotate counterclockwise", "" )
        self.Bind( wx.EVT_TOOL, self.OnZoom, id=28 )
        tb.Realize()
        #init set
        tb.EnableTool( 10, True )
        tb.EnableTool( 11, False )
        tb.EnableTool( 12, False )
        tb.EnableTool( 13, False )

        # capture window fixed size
        self.window = wx.Window(self)
        self.window.SetSize( (cols,rows) )
        self.Fit()
        self.SetMaxSize( self.Size )
        self.SetMinSize( self.Size )

        # Capture and Timer
        self.capture = None
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.NextFrame)

        # Plot window
        self.plot = None

        # close window event
        self.Bind( wx.EVT_CLOSE, self.OnCloseWindow )

        # show window
        self.Show()

    # normal function
    def getRecordDir( self ):
        if self.recorddir is None:
            try:
                config = ConfigParser.ConfigParser()
                config.read( os.path.join( module_path(), "conf.ini" ) ) # absolute
                self.recorddir = config.get( "Record Dir", "recorddir" )
                self.recorddir = os.path.realpath( self.recorddir )
            except:
                self.recorddir = module_path()

    def autoSavePng( self ):
        filepng = os.path.join( self.recorddir,
                                self.recordname + '_' + str(self.recordslice) \
                                + ".png" )
        self.plot.fig.savefig( filepng, dpi=100 ) #imgsize

    def checkFileName( self, filename ):
        cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
        return ''.join(c for c in cleanedFilename if c in validFilenameChars)
        

    # event handle function
    def OnOpenFile( self, event ):
        wildcard = "Video Files (*.mp4;*.avi)|*.mp4;*.avi|"     \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose a video file",
            defaultDir="",
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            for path in paths: # only one file currently
                self.capture = cv2.VideoCapture(path)
                self.capturetype = "File"
                self.OnSOF( event )
        dlg.Destroy()
            

    def OnOpenCam( self, event ):
        cam_list = []
        cam_all = 0
        cam_sel = 0
        #open default camera
        if 10 == event.GetId():
            cam_default = cv2.VideoCapture( 0 )
            if True == cam_default.isOpened():
                self.capture = cam_default
                self.capturetype = "Cam"
                # add this line to make sure camera is opened
                self.capture.open( 0 ) 
                self.OnSOF( event )
        #open camera select dialog
        else:   
            # open all camera
            while True:
                cam_list.append( cv2.VideoCapture( cam_all ) )
                if True == cam_list[cam_all].isOpened():
                    cam_all += 1
                else:
                    break
            # if there more than one camera exist            
            if cam_all > 1:
                sel_list = [ 'Camera '+str(i+1) for i in range(cam_all) ]     
                dlg = wx.SingleChoiceDialog(
                        self, 'Select one camera', 'Open Cam',
                        sel_list,
                        wx.CHOICEDLG_STYLE
                        )
                if dlg.ShowModal() == wx.ID_OK:
                    cam_sel = dlg.GetSelection()
                else:
                    cam_sel = cam_all #cam_sel==cam_all means on camera select
                dlg.Destroy()
            # release camera not selected
            for i in range(cam_all):
                if i != cam_sel:
                    cam_list[i].release()
            # set self.capture
            if cam_sel != cam_all:
                self.capture = cam_list[cam_sel]
                self.capturetype = "Cam"
                # add this line to make sure camera is opened
                self.capture.open( cam_sel ) 
                self.OnSOF( event )
                 
    # start of frame capture
    def OnSOF( self, event ):
        self.OnEOF( event )
        
        self.StatusBar.SetStatusText( "Capturing", 0 )
        self.zoom_param[0] = 1 # zoom home
        self.fps = int( self.capture.get( cv2.cv.CV_CAP_PROP_FPS ) )
        if self.fps == 0:
            self.fps = 10
        
        #set toolbar
        self.ToolBar.EnableTool( 10, True )
        self.ToolBar.EnableTool( 11, True )
        self.ToolBar.EnableTool( 12, False )
        self.ToolBar.EnableTool( 13, False )
        self.MenuBar.Enable( 101, True )
        self.MenuBar.Enable( 102, True )
        if self.capturetype == "File":
            self.OnRecord( event )
        #start timer last    
        self.timer.Start(1000./self.fps)

    # end of frame capture, call automate
    def OnEOF( self, event ):
        self.timer.Stop()
        self.StatusBar.SetStatusText( "IDLE", 0 )
        #self.capture = None
        #self.capturetype = None
        if self.record:
            # set toolbar in OnStop
            self.OnStop( event )
        else:
            self.ToolBar.EnableTool(10, True)
            self.ToolBar.EnableTool(11, False)
            self.ToolBar.EnableTool(12, False)
            #self.ToolBar.EnableTool(13, False)#
            self.MenuBar.Enable( 101, True )
            self.MenuBar.Enable( 102, True )
            #self.MenuBar.Enable( 103, False )#
            
    def OnRecord( self, event ):
        self.StatusBar.SetStatusText( "Recording", 0 )
        self.framenumber = 0
        #disable setRecordDir
        self.MenuBar.Enable(104, False)
        self.getRecordDir()
        if self.record == 0: # must before "self.record = 1"
            self.recordslice = 0
            self.recordname = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recordslice += 1
        fileavi = os.path.join( self.recorddir,
                                self.recordname + '_' + str(self.recordslice) \
                                + ".avi" )
        self.videowriter = cv2.VideoWriter()
        #sometimes the first will not success
        #the single video file should be smaller than 2G
        #640x360, 10fps, 60minutes, 1600M
        if not self.videowriter.open( fileavi,
                                      cv2.cv.CV_FOURCC('M', 'J', 'P', 'G'),
                                      self.fps, (cols, rows)
                                      ):
            self.videowriter.open( fileavi,
                                   cv2.cv.CV_FOURCC('M', 'J', 'P', 'G'),
                                   self.fps, (cols, rows) )
        if not self.videowriter.isOpened():
            self.videowriter = None

        self.record = 1 #
        #set toolbar
        self.ToolBar.EnableTool(10, False)
        self.ToolBar.EnableTool(11, False)
        self.ToolBar.EnableTool(12, True)
        self.ToolBar.EnableTool(13, False)
        self.MenuBar.Enable( 101, False )
        self.MenuBar.Enable( 102, False )
        self.MenuBar.Enable( 103, False )

    def OnStop( self, event ):
        self.StatusBar.SetStatusText( "IDLE", 0 )
        # assert self.record==1
        self.record = 0
        #auto save png here 2/2
        if not self.plot:
            self.OnPlot( event )
        self.autoSavePng()
        #self.recordslice = 0
        self.videowriter = None #release
        #enable setRecordDir
        self.MenuBar.Enable(104, True)
        #set toolbar
        self.ToolBar.EnableTool(10, True)
        if self.capture:
            self.ToolBar.EnableTool(11, True)
        else:
            self.ToolBar.EnableTool(11, False)
        self.ToolBar.EnableTool(12, False)
        self.ToolBar.EnableTool(13, True) #Enabe saveas only after stop
        self.MenuBar.Enable( 101, True )
        self.MenuBar.Enable( 102, True )
        self.MenuBar.Enable( 103, True )

    def NextFrame( self, event ):
        ret, img_c = self.capture.read()
        if ret:
            # step 1. image zoom
            cmd_init = self.zoom_param[0]
            cmd_rotate = self.zoom_param[1]
            cmd_zoom = self.zoom_param[2]
            cmd_pan_x = self.zoom_param[3]
            cmd_pan_y = self.zoom_param[4]
            #clear zoom param
            self.zoom_param = 5*[0]
            img_z = image_zoom( img_c,
                                cmd_init = cmd_init,
                                cmd_rotate = cmd_rotate,
                                cmd_zoom = cmd_zoom,
                                cmd_pan_x = cmd_pan_x,
                                cmd_pan_y = cmd_pan_y
                                )

            # step 2. result filter and plot
            #auto save every frame avi here
            if self.record and self.videowriter: #
                self.videowriter.write( img_z )
            value_ori = getnumber( img_z ) #
            #print value_ori[1]
            #display on StatusBar
            self.StatusBar.SetStatusText( value_ori[1], 1 )
            self.StatusBar.SetStatusText( value_ori[3], 2 )
            if self.record:
                valuefilter( value_ori, self.framenumber, self.fps )
                if self.framenumber==0: #clear plot
                    # how to clear the plot canvas???
                    if self.plot:
                    #    self.plot.Destroy()
                        self.plot.onClearDraw()
                        self.plot.SetTitle( "Plot Window - Slice: "
                                            +str(self.recordslice) )
                self.OnPlot( event )
                self.framenumber += 1

            # step 3. image disp on wxWindow 
            img_disp = cv2.cvtColor( img_z, cv2.COLOR_BGR2RGB )
            img_h = len( img_disp )
            img_w = len( img_disp[0] )
            img_disp_bm = wx.BitmapFromBuffer( img_w, img_h, img_disp )
            dc = wx.ClientDC( self.window )
            dc.DrawBitmap( img_disp_bm, 0, 0, False )

            # step 4. limit record lenght to 90 minutes
            if self.framenumber >= self.fps * 60 * record_minutes_max:
                #auto save png here 1/2
                self.autoSavePng()
                self.OnRecord( event ) #self.recordslice will not clear

        # end of frame capture
        else:
            self.OnEOF( event )

    def OnPlot( self, event ):
        if not self.plot:
            self.plot = PlotFigure(self, "Plot Window" )
            if self.recordslice != 0:
                self.plot.SetTitle( "Plot Window - Slice: "
                                    +str(self.recordslice) )
            self.plot.Show()
        self.plot.onUpdate()

    def OnZoom( self, event ):
        zoom_id = event.GetId()
        if zoom_id == 20:
            self.zoom_param[0] = 1 #zoom home
        elif zoom_id == 21:
            self.zoom_param[2] = 1 #zoom in
        elif zoom_id == 22:
            self.zoom_param[2] = -1 #zoom out
        elif zoom_id == 23:
            self.zoom_param[4] = 1 #pan up
        elif zoom_id == 24:
            self.zoom_param[4] = -1 #pan down
        elif zoom_id == 25:
            self.zoom_param[3] = 1 #pan left
        elif zoom_id == 26:
            self.zoom_param[3] = -1 #pan right
        elif zoom_id == 27:
            self.zoom_param[1] = 1 #rotate right
        elif zoom_id == 28:
            self.zoom_param[1] = -1 #rotate left



    def OnSetRecordDir( self, event ):
        if self.recorddir is None:
            self.getRecordDir()
        dlg = wx.DirDialog( self, "Choose a directory:",
                            defaultPath = self.recorddir,
                            style=wx.DD_DEFAULT_STYLE
                            )
        if dlg.ShowModal() == wx.ID_OK:
            self.recorddir = dlg.GetPath()
            config = ConfigParser.ConfigParser()
            config.read("conf.ini")
            config.set( "Record Dir", "recorddir", self.recorddir )
            configfile = open( os.path.join( module_path(), "conf.ini" ), "w" )
            config.write( configfile )
            configfile.close()            
        dlg.Destroy()

    def OnOpenRecordDir( self, event ):
        self.getRecordDir()
        os.system( "explorer.exe %s" %self.recorddir )
        
    def OnSaveAs( self, event ):
        dlg = wx.FileDialog( self,
                             message="Save file as...",
                             defaultDir=self.recorddir,
                             defaultFile=self.recordname,
                             wildcard="Png Files (*.png)|*.png",
                             style=wx.SAVE 
                             )
        if dlg.ShowModal() == wx.ID_OK:
            newdir = dlg.GetDirectory()
            #finename only, on ext
            newname = os.path.splitext( dlg.GetFilename() )[0]
            olddir = self.recorddir
            oldname = self.recordname
            #print olddir, oldname, newdir, newname
            #check, newname is check by FileDialog 
            if newname != oldname or newdir != olddir:
                #renames the autosave png/avi files
                oldfiles = filter( lambda s: s.find(oldname) != -1,
                                   os.listdir( olddir ) )
                newfiles = map( lambda s: s.replace(oldname, newname),
                                oldfiles )
                #print oldfiles, newfiles
                for i in range( len(oldfiles) ):
                    # change filename and dir meantime
                    newfile = os.path.join( newdir, newfiles[i] )
                    if os.path.exists( newfile ):
                        os.remove( newfile )
                    os.renames( os.path.join( olddir, oldfiles[i] ),
                                newfile )
                #update recordname and recorddir,
                #but the recorddir in conf.ini is not change
                self.recordname = newname
                self.recorddir = newdir
        dlg.Destroy()

    def OnAbout( self, event ):
        info = wx.AboutDialogInfo()
        info.Name = "Meter Viewer"
        info.Version = "0.1"
        info.Copyright = "(C) 2015"
        info.Description = wordwrap(
            "Meter Viewer is a program used to auto capture, \"read\" and "
            "record an old meter panel which has no digital output interface."

            "\n\nThis program used Python 2.7.9, OpenCV 2.4.10, "
            "wxPython 2.8, matplotlib 1.3.0.",
            350, wx.ClientDC( self ) )
        info.WebSite = ("https://github.com/haojijun/meter-viewer/")
        info.Developers = [ "HAO Jijun" ]
        #info.License = wordwrap( "GPL", 500, wx.ClientDC( self ) )
        wx.AboutBox( info )
        
            
        
    def OnCloseWindow( self, event ):
        self.timer.Stop()
        cv2.destroyAllWindows()
        if self.record:
            self.OnStop( event )
        if self.plot:
            self.plot.Destroy()
        self.Destroy()

#-------------------------------------------------------        

app = wx.App(False)
frame = MainWindow(None, "Capture Window")
app.MainLoop()
