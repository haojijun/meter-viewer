import os
import wx
import cv2

import matplotlib
#matplotlib.use("WXAgg")

import matplotlib.pyplot as plt
#import matplotlib.animation as animation #cause black screen
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from collections import Counter

from imagezoom import image_zoom
from getnumber import getnumber




cols = 640 
rows = 360


fps = 10





val_list = []
val_list_n = 0



# virables for valuefilter function only
val_last = None
val_time = 0
err_cnt = 0
len_cnt = 0

# error correction
def valuefilter ( value_in, frame=0, err_max=30, len_max=100 ):
    global err_cnt, val_last, val_list, val_list_n, val_time

    if value_in[0] :
        if val_last is None: #start
            val_time = frame
            #val_list = []
            val_list_n += 1
            err_cnt = 0
            val_list.append( [ val_time, [] ] )
        val_last = float(value_in[1])
        val_list[val_list_n-1][1].append(val_last)
        if err_cnt > 0:
            err_cnt -= 1
    else:
        if val_last is not None:
            if value_in[1] == "CAL" or value_in[1] == "OFF": #end
                val_last = None
                #print val_list
                
            else: #value_in[1] == "ERR"
                if err_cnt < err_max:
                    err_cnt += 1
                    val_list[val_list_n-1][1].append(val_last)
                else: #end
                    val_last = None
                    #print val_list
                    
            

    return




#global
val_list = []

#func only
val_list_tmp = []

def valuefilter2( value_in, frame=0, len_max=10 ):
    global val_list, val_list_tmp

    if frame == 0:
        val_list = []
        
    if frame % len_max == 0:
        val_list_tmp = []
        
    val_list_tmp.append( value_in )
    
    if ( frame + 1 ) % len_max == 0:
        val_most = Counter( val_list_tmp ).most_common( 1 )[0][0]
        #print val_most[1]
        if val_most[0]:
            val_list.append( float( val_most[1] ) / -10.0 ) #"-888.8dBm"
        else:
            val_list.append( None )
            
    return
        
    
        
    
    
"""    

fig, ax = plt.subplots()
line, = ax.plot( [], [], lw=2 ) # "line," means what?
ax.set_ylim( -200.0, 0.0 )
ax.set_xlim( 0, 100 )
ax.grid()
xdata, ydata = [], []

def ani_init():
    line.set_data( [], [] )
    return line,

def value_plot( i ):
    line.set_data( range( len( val_list ) ), val_list )
    return line,

#fig.show()

#plt.show()

"""

class PlotFigure( wx.Frame ):
    """Matplotlib wxFrame with animation effect"""
    def __init__( self, parent, title ):
        wx.Frame.__init__( self, parent, title=title, size=(600,400) )

        self.fig = Figure( (6,4), 100 )
        self.canvas = FigureCanvas( self, wx.ID_ANY, self.fig )
        self.ax = self.fig.add_subplot(111)
        self.ax.set_ylim( [-200, 0] )
        self.ax.set_xlim( [0, 60] ) #200
        self.ax.set_autoscale_on(False)
        #self.ax.set_xticks([])
        #self.ax.set_yticks( [20] )
        #self.ax.grid(True)
        self.line, = self.ax.plot( [], [], lw=2 )
        self.ax.plot( range(60), [-40]*60, '--', lw=1 ) # -40, 60
        self.canvas.draw()
        self.bg = self.canvas.copy_from_bbox( self.ax.bbox )

    def onUpdate( self ):
        #self.canvas.restore_region( self.bg )
        xmin, xmax = self.ax.get_xlim()
        if len(val_list) >= xmax:
            self.ax.set_xlim(xmin, 2*xmax)
            self.ax.plot( range(2*int(xmax)), [-40]*2*int(xmax), '--', lw=1 ) #
            self.canvas.draw()
        self.line.set_data( range( len( val_list ) ), val_list )
        self.ax.draw_artist( self.line )
        self.canvas.blit( self.ax.bbox )
        
        






class MainWindow( wx.Frame ):
    def __init__( self, parent, title ):
        wx.Frame.__init__( self, parent, title=title, size=wx.DefaultSize )

        self.zoom_param = 5*[0]
        self.record = 0
        self.framenumber = 0

        tb = self.CreateToolBar()
        self.CreateStatusBar()

        # Prepare the menu bar
        menuBar = wx.MenuBar()

        # 1st menu from left
        menu1 = wx.Menu()
        menu1.Append(101, "&Open Camera", "What does this mean")
        menu1.Append(102, "&Open File", "")
        menu1.AppendSeparator()
        menu1.Append(103, "&Exit", "Close the window")
        menuBar.Append(menu1, "&File")

        # 2nd menu from left
        menu2 = wx.Menu()
        menu2.Append(201, "Demo")
        menu2.AppendSeparator()
        menu2.Append(202, "About")
        menuBar.Append(menu2, "&Help")

        #self.SetMenuBar(menuBar)

        # Menu events
        #self.Bind(wx.EVT_MENU, self.OnOpenCam, id=101)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, id=102)
        
        
        # Tool Bar
        tsize = (16,16)
        bmp_open = wx.ArtProvider.GetBitmap( wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize )
        bmp_copy = wx.ArtProvider.GetBitmap( wx.ART_COPY, wx.ART_TOOLBAR, tsize )
        bmp_save = wx.ArtProvider.GetBitmap( wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tsize )
        bmp_cam = wx.ArtProvider.GetBitmap( wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize )

        bmp_panup = wx.ArtProvider.GetBitmap( wx.ART_GO_UP, wx.ART_TOOLBAR, tsize )
        bmp_pandown = wx.ArtProvider.GetBitmap( wx.ART_GO_DOWN, wx.ART_TOOLBAR, tsize )
        bmp_panleft = wx.ArtProvider.GetBitmap( wx.ART_GO_BACK, wx.ART_TOOLBAR, tsize )
        bmp_panright = wx.ArtProvider.GetBitmap( wx.ART_GO_FORWARD, wx.ART_TOOLBAR, tsize )

        bmp_rotate = wx.ArtProvider.GetBitmap( wx.ART_REDO, wx.ART_TOOLBAR, tsize )
        bmp_rotatec = wx.ArtProvider.GetBitmap( wx.ART_UNDO, wx.ART_TOOLBAR, tsize )

        bmp_record = wx.Bitmap("icon/record.png", wx.BITMAP_TYPE_PNG)
        bmp_stop = wx.Bitmap("icon/stop.png", wx.BITMAP_TYPE_PNG)
        bmp_plot = wx.Bitmap("icon/plot.png", wx.BITMAP_TYPE_PNG)
        
        bmp_zoomhome = wx.Bitmap("icon/zoomhome.png", wx.BITMAP_TYPE_PNG)
        bmp_zoomin = wx.Bitmap("icon/zoomin.png", wx.BITMAP_TYPE_PNG)
        bmp_zoomout = wx.Bitmap("icon/zoomout.png", wx.BITMAP_TYPE_PNG)

        tb.SetToolBitmapSize( tsize )

        tb.AddSimpleTool( 10, bmp_open, "Open", "Open Video Capture" )
        self.Bind( wx.EVT_TOOL, self.OnOpenFile, id=10 )

        tb.AddSimpleTool( 11, bmp_save, "Save", "Save Plot Figure" )
        self.Bind( wx.EVT_TOOL, self.OnSaveFig, id=11 )
        
        tb.AddSimpleTool( 12, bmp_record, "Record", "Start Record" )
        self.Bind( wx.EVT_TOOL, self.OnRecord, id=12 )
        tb.EnableTool(12, False)


        tb.AddSimpleTool( 13, bmp_stop, "Stop", "Stop Record" )
        self.Bind( wx.EVT_TOOL, self.OnStop, id=13 )
        tb.EnableTool(13, False)

#        tb.AddSimpleTool( 12, bmp_plot, "Plot", "Long help for 'Copy'" )
#        self.Bind( wx.EVT_TOOL, self.OnPlot, id=12 )


        
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
        
        # Window 
        self.window = wx.Window(self)

        self.window.SetSize( (cols,rows) )
        self.Fit()
        self.SetMaxSize( self.Size )
        self.SetMinSize( self.Size )

        # Timer
        self.capture = None
        self.timer = wx.Timer(self)

        self.Bind(wx.EVT_TIMER, self.NextFrame)

        self.plot = PlotFigure(self, "Plot Window")
        #self.plot.Show()

        #close window
        self.Bind( wx.EVT_CLOSE, self.OnCloseWindow )

        


        self.Show()


    def OnZoom( self, event ):
        zoom_id = event.GetId()
        if zoom_id == 20:
            self.zoom_param[0] = 1 #zoom home
        elif zoom_id == 21:
            self.zoom_param[2] = 1 #zoom in
        elif zoom_id == 22:
            self.zoom_param[2] = -1 #zoom out
        elif zoom_id == 23:
            self.zoom_param[4] = -1 #pan up
        elif zoom_id == 24:
            self.zoom_param[4] = 1 #pan down
        elif zoom_id == 25:
            self.zoom_param[3] = -1 #pan left
        elif zoom_id == 26:
            self.zoom_param[3] = 1 #pan right
        elif zoom_id == 27:
            self.zoom_param[1] = 1 #rotate right
        elif zoom_id == 28:
            self.zoom_param[1] = -1 #rotate left

    def OnToolClick( self, event ):
        tb = event.GetEventObject()
        #tb.EnableTool( 10, not tb.GetToolEnabled(10) )

    def OnOpenFile( self, event ):
        wildcard = "Video Files (*.mp4;*.avi)|*.mp4;*.avi|"     \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose a video file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )

        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()

            for path in paths: # only one file currently
                #print path
                self.OnRecord( event )       
                self.capture = cv2.VideoCapture(path)
                self.zoom_param[0] = 1 # zoom home
                fps = int( self.capture.get( cv2.cv.CV_CAP_PROP_FPS ) )
                if fps == 0:
                    fps = 10
                self.timer.Start(1000./fps)
                
                #value_ori = getnumber( img_z )
                #valuefilter( value_ori, framenumber )
                #print value_ori[1]



        dlg.Destroy()


    def OnOpenCam( self, event ):
        cam_sel = 0
        cam_all = 0
        cam_list = []

        # open all camera
        while True:
            cam_list.append( cv2.VideoCapture( cam_all ) )
            if True == cam_list[cam_all].isOpened():
                cam_all += 1
            else:
                break
            
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
                cam_sel = cam_all

            dlg.Destroy()

        #print cam_all, cam_sel

        # release camera not selected
        for i in range(cam_all):
            if i != cam_sel:
                cam_list[i].release()

        if cam_sel != cam_all:
            self.OnRecord( event )
            self.capture = cam_list[cam_sel]
            self.zoom_param[0] = 1 # zoom home
            fps = int( self.capture.get( cv2.cv.CV_CAP_PROP_FPS ) ) #get fps 0 for cam
            if fps == 0:
                fps = 10
            self.timer.Start(1000./fps)
            


    def NextFrame( self, event ):
        ret1, img_c1 = self.capture.read()
        ret2, img_c2 = self.capture.read()
        ret3, img_c3 = self.capture.read()
        if ret1 and ret2 and ret3:
            # there may be better way
            img_c = cv2.addWeighted( img_c1, 0.5, img_c2, 0.5, 0.0 )
            img_c = cv2.addWeighted( img_c, 0.67, img_c3, 0.33, 0.0 )
            
            # image zoom
            cmd_init = self.zoom_param[0]
            cmd_rotate = self.zoom_param[1]
            cmd_zoom = self.zoom_param[2]
            cmd_pan_x = self.zoom_param[3]
            cmd_pan_y = self.zoom_param[4]
            self.zoom_param = 5*[0]
            img_z = image_zoom( img_c,
                                cmd_init = cmd_init,
                                cmd_rotate = cmd_rotate,
                                cmd_zoom = cmd_zoom,
                                cmd_pan_x = cmd_pan_x,
                                cmd_pan_y = cmd_pan_y
                                )

            value_ori = getnumber( img_z ) #
            #print value_ori

            # result filter and plot
            if self.record:
                #valuefilter( value_ori, self.framenumber ) #
                valuefilter2( value_ori, self.framenumber )

                if not self.plot:
                    self.plot = PlotFigure(self, "Plot Window")
                    self.plot.Show()
                self.plot.onUpdate()

                self.framenumber += 1
                
            else:
                self.framenumber = 0


            # image disp on wxWindow 
            img_disp = cv2.cvtColor( img_z, cv2.COLOR_BGR2RGB )
            img_h = len( img_disp )
            img_w = len( img_disp[0] )
            bitmap = wx.BitmapFromBuffer( img_w, img_h, img_disp )
            dc = wx.ClientDC( self.window )
            dc.DrawBitmap( bitmap, 0, 0, False )

        # end of file
        else:
            pass
      
    def OnSaveFig( self, event ):
        wildcard = "PNG Files (*.png)|*.png|"     \
                   "JPG Files (*.jpg)|*.jpg|"     \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Save file as ...",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
            style=wx.SAVE
            )

        dlg.SetFilterIndex(2)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.plot.fig.savefig( path, dpi=100 )

        dlg.Destroy()
        


    def OnRecord( self, event ):
        " how to clear"
        self.plot.Destroy()
        self.plot = PlotFigure(self, "Plot Window")
        self.plot.Show()

        self.record = 1
        tb = event.GetEventObject()
        tb.EnableTool(12, False)
        tb.EnableTool(13, True)


    def OnStop( self, event ):
        self.record = 0
        tb = event.GetEventObject()
        tb.EnableTool(12, True)
        tb.EnableTool(13, False)
        


    def OnPlot( self, event ):
        """
        for val in val_list:
            plt.plot(tuple(range(val[0], val[0]+len(val[1]))),
                     tuple(val[1]), 'b.')
        """

        """
        plt.plot( tuple( range( len(val_list) ) ),
                  tuple( val_list ),
                  'b.' )
        """

        """
        ani = animation.FuncAnimation( fig, value_plot, init_func=ani_init,
                                       blit=True, interval=500, repeat=False )
        """

        #self.plot.Show()
        plt.show()

        
    def OnCloseWindow( self, event ):
        cv2.destroyAllWindows()
        self.Destroy()
        
        

        
#-------------------------------------------------------        

app = wx.App(False)
frame = MainWindow(None, "Capture Window")
app.MainLoop()
