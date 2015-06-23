#--------------------------------------
# image rotate zoom and pan
# 1. cv2.transpose cv2.flip: easy understand
# 2. cv2.warpAffine: powerful complex but only compute ROI
# 3. cv2.getRectSubPix: only copy and no zoom
# 4. cv2.pyrUp cv2.pyrDown: only 2^n
# 5. cvGetQuadrangleSubPix: like warpAffine
# 6. cvSetImageROI: only copy and no zoom
# 7. cv2.resize
#-----------------------------------

import cv2
import numpy as np

#global settings
#viewer window size
cols = 640 
rows = 360

zoom_range = [1./1., 1./1.5, 1./2., 1./2.5, 1./3., 1./3.5, 1./4., 1./4.5, 1./5.]
pan_x_range = [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1,
               0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
pan_y_range = [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1,
               0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

#global variables
rotate = 0 #0,90,180,270
zoom = zoom_range[0] #[1,1/5]
pan_x = pan_x_range[10] #[-1,1]
pan_y = pan_y_range[10] #[-1,1]
M = np.float32( [ [1.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0] ] )

#-------------------------------------------------

def image_zoom( img, cmd_init=0,
                cmd_rotate=0, cmd_zoom=0,
                cmd_pan_x=0, cmd_pan_y=0 ):
    """
    usage:
    cmd_init == 0: init
    cmd_init == 0: no init
    cmd_rotate == 1: right rotate
    cmd_rotate == -1: left rotate
    cmd_zoom == 1: zoom in
    cmd_zoom == -1: zoom out
    cmd_pan_x == 1: pan right
    cmd_pan_x == -1: pan left
    cmd_pan_y == 1: pan down
    cmd_pan_y == -1: pan up
    """
    
    global rotate, zoom, pan_x, pan_y, M

    #step 1. rotate
    if cmd_rotate:
        rotate = ( 90 * cmd_rotate / abs(cmd_rotate) + rotate ) % 360
    if rotate == 90:
        img_tmp = cv2.transpose(img)
        img_r = cv2.flip(img_tmp, 1)
    elif rotate == 180:
        img_tmp = cv2.flip(img, 0)
        img_r = cv2.flip(img_tmp, 1)
    elif rotate == 270:
        img_tmp = cv2.transpose(img)
        img_r = cv2.flip(img_tmp, 0)
    else:
        img_r = img

    #first to run or fit to window or rotate
    #set zoom and pan default
    if cmd_init or cmd_rotate:
        zoom = zoom_range[0]
        pan_x = pan_x_range[10] 
        pan_y = pan_y_range[10]

    #step 2. zoom and pan
    if cmd_zoom:
        zoom_index = zoom_range.index(zoom)
        if cmd_zoom > 0 and zoom_index + 1 < len(zoom_range) :
            zoom = zoom_range[zoom_index + 1]
        elif cmd_zoom < 0 and zoom_index - 1 >= 0 :
            zoom = zoom_range[zoom_index - 1]

    if cmd_pan_x:
        pan_x_index = pan_x_range.index(pan_x)
        if pan_x_index + cmd_pan_x / abs(cmd_pan_x) in range( len(pan_x_range) ):
            pan_x = pan_x_range[ pan_x_index + cmd_pan_x / abs(cmd_pan_x) ]

    if cmd_pan_y:
        pan_y_index = pan_y_range.index(pan_y)
        if pan_y_index + cmd_pan_y / abs(cmd_pan_y) in range( len(pan_y_range) ):
            pan_y = pan_y_range[ pan_y_index + cmd_pan_y / abs(cmd_pan_y) ]

    #update M
    if cmd_init or cmd_rotate or cmd_zoom or cmd_pan_x or cmd_pan_y:
        img_w = len(img_r[1])
        img_h = len(img_r)
        
        zm_f = max( 1.0*img_w/cols, 1.0*img_h/rows ) * zoom
        
        #better limited?
        zm_c_x = (img_w-1)/2. + pan_x * img_w * 0.5
        zm_c_y = (img_h-1)/2. + pan_y * img_h * 0.5

        zm_w = 0.5 * ( cols * zm_f - 1 ) #half width
        zm_h = 0.5 * ( rows * zm_f - 1 ) #half height

        zm_v = [ [zm_c_x - zm_w, zm_c_y - zm_h],
                 [zm_c_x + zm_w, zm_c_y - zm_h],
                 [zm_c_x + zm_w, zm_c_y + zm_h] ]

        pos1 = np.float32( zm_v )
        pos2 = np.float32([[0,0], [cols-1,0], [cols-1,rows-1]])

        M = cv2.getAffineTransform( pos1, pos2 )

    #get the image and return
    img_z = cv2.warpAffine( img_r, M, (cols,rows), borderValue=cv2.cv.ScalarAll(255) )
    
    return img_z

#--------------------------------------------------------------

