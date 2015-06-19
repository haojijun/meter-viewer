#------------------------------------------
#
# get number from an image
#
# 1. get the box
# 2. get the number
#
#-------------------------------------------

import cv2
import numpy as np
import os
import math




#image roi size
roi_w = 400
roi_h = 100


#7-segment number
#   |-a-|
#   f   b
#   |-g-|
#   e   c
#   |-d-|
number_mask = ((1, 1, 1, 1, 1, 1, 0), #0
               (0, 1, 1, 0, 0, 0, 0), #1
               (1, 1, 0, 1, 1, 0, 1), #2
               (1, 1, 1, 1, 0, 0, 1), #3
               (0, 1, 1, 0, 0, 1, 1), #4
               (1, 0, 1, 1, 0, 1, 1), #5
               (1, 0, 1, 1, 1, 1, 1), #6
               (1, 1, 1, 0, 0, 0, 0), #7
               (1, 1, 1, 1, 1, 1, 1), #8
               (1, 1, 1, 1, 0, 1, 1), #9
               (1, 0, 0, 1, 1, 1, 0), #C
               (1, 1, 1, 0, 1, 1, 1), #A
               (0, 0, 0, 1, 1, 1, 0), #L
               (0, 1, 1, 0, 0, 0, 1) )#-1


# background:176, ROI:70, number:220
threshold_1 = 120
threshold_2 = 130

#------------------------------------------------------

#return image roi
def getroi( img ):
    boxcolor = (255,0,0)
    gray = cv2.cvtColor( img, cv2.COLOR_BGR2GRAY )

    #blur = cv2.bilateralFilter(gray,9,150,150)
    blur = cv2.GaussianBlur(gray,(3,3),0)

    #edges = cv2.Canny(blur,50,150,apertureSize = 3) #
    #kernel = np.ones((3,3),np.uint8)
    #closing = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations = 1)

    # need update
    # Threshold the image
    ret,thresh = cv2.threshold(blur, threshold_1,255,1) # search white from black

    # determin by image size
    kernel = np.ones((3,3),np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations = 1)

    contours, hierarchy = cv2.findContours(closing.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(contours, key = cv2.contourArea, reverse = True)[:1] #?
    #for cnt in cnts:
    cnt = cnts[0]
    
    hull = cv2.convexHull(cnt)
    #epsilon = 0.002*cv2.arcLength(hull,True)
    #approx = cv2.approxPolyDP(hull,epsilon,True)

    box = cv2.minAreaRect(hull)
    #for dubug
    #draw_box( img, box )

    

    if box[1][0] >= box[1][1]:      
        w = box[1][0]
        h = box[1][1]
        r = box[2] #for the y=0 is top
    else:
        w = box[1][1]
        h = box[1][0]
        r = box[2] + 90

    #assert box w/h is correct
    if w/h <3.8 or w/h >4.2:
        return None

    #box to corner point
    #box_v = cv2.cv.BoxPoints(box)
    #be care that y=0 is top, r is negative
    a = 0.5 * math.cos(math.radians( r ))
    b = 0.5 * math.sin(math.radians( r ))

    tl_x = int( box[0][0] - a*w + b*h )
    tl_y = int( box[0][1] - b*w - a*h ) 

    tr_x = int( box[0][0] + a*w + b*h )
    tr_y = int( box[0][1] + b*w - a*h )

    bl_x = int( box[0][0] - a*w - b*h )
    bl_y = int( box[0][1] - b*w + a*h )

    br_x = int( box[0][0] + a*w - b*h )
    br_y = int( box[0][1] + b*w + a*h )
    
    pos1 = np.float32( [ [tl_x,tl_y], [tr_x,tr_y], [br_x,br_y] ] )
    pos2 = np.float32( [ [-20,-10], [roi_w-1+5,-10], [roi_w-1+20,roi_h-1+10] ] )#

    M1 = cv2.getAffineTransform( pos1, pos2 )
    roi = cv2.warpAffine( gray, M1, (roi_w,roi_h),
                              borderValue=cv2.cv.ScalarAll(255) )

    roi_blur = cv2.GaussianBlur(roi,(3,3),0)
    ret,roi_thresh = cv2.threshold(roi_blur, threshold_2,255,0)

    #draw box
    cv2.line( img, (tl_x,tl_y), (tr_x,tr_y), boxcolor )
    cv2.line( img, (tr_x,tr_y), (br_x,br_y), boxcolor )
    cv2.line( img, (br_x,br_y), (bl_x,bl_y), boxcolor )
    cv2.line( img, (bl_x,bl_y), (tl_x,tl_y), boxcolor )
	
    cv2.imshow("thresh", closing)
    cv2.imshow("gray", gray)

    return roi_thresh

"""
input:
    img: roi img
    cont: single number contours
output:
    single number string
"""
def getSingleNumber( img, cont ):
    """
    single number ROI size: 60x100
    """
    #step 1. get single number roi
    pos1 = np.float32( [ [cont[0],0],
                         [cont[0]+cont[2],0],
                         [cont[0]+cont[2],99] ] )
    pos2 = np.float32( [ [0,0],
                         [59,0],
                         [59,99] ] )
    M = cv2.getAffineTransform( pos1, pos2 )
    roi_sn = cv2.warpAffine( img, M, (60,100),
                             borderValue=cv2.cv.ScalarAll(255) )

    #step 2. get 7 segments of single number
    seg7 = 7*[0]
    if sum( roi_sn[25][0:20] ) > 0: #f,5
        seg7[5] = 1   
    if sum( roi_sn[25][40:60] ) > 0: #b,1
        seg7[1] = 1   
    if sum( roi_sn[75][0:20] ) > 0: #e,4
        seg7[4] = 1   
    if sum( roi_sn[75][40:60] ) > 0: #c,2
        seg7[2] = 1
    #adjust for "7." or "L"
    x_ad = 0
    if seg7[4]==0 and seg7[5]==0:
        x_ad -= 5
    if seg7[1]==0 and seg7[2]==0:
        x_ad += 5 
    if sum([ a[30+x_ad] for a in roi_sn[0:20] ]) > 0: #a,0
        seg7[0] = 1       
    if sum([ a[30+x_ad] for a in roi_sn[40:60] ]) > 0: #g,6
        seg7[6] = 1
    if sum([ a[30+x_ad] for a in roi_sn[80:100] ]) > 0: #d,3
        seg7[3] = 1   

    #for debug
    cv2.imshow( "roi_sn", roi_sn ) 

    try:
        i = number_mask.index( tuple(seg7) )
        if i==10:
            return "C"
        elif i==11:
            return "A"
        elif i==12:
            return "L"
        elif i==13:
            return "-1"
        else:
            return str( i )
    except:
        #imwritefile = "E://PIL/num/singlenum/error/" + str(cv2.getTickCount()) + ".jpg"
        #cv2.imwrite( imwritefile, roi_sn )
        return "*"




#
def getnumber( img ):
    thresh_roi = 5
    color = (255, 255, 0)
    numbers = ""

    #step 1. get box
    roi = getroi( img )
    if roi is None:
        return (0, "ERR", 1, "ROI get error")

    #adjust roi if display number
    if sum( roi[50][15*4:75*4] ) < 5*255:
        return (1, "OFF", 0, "Display OFF")
    else:
        #adjust the roi
        y_up = 49                        
        for i in range(0,30,2):
            if sum(roi[i]) >= thresh_roi*255:
                #print i
                y_up = i
                break

        y_down = 50
        for i in range(99,70,-2):
            if sum(roi[i]) >= thresh_roi*255:
                #print i
                y_down = i
                break

        if (y_down - y_up) < 0.6 * roi_h:
            #print "ROI adjust error", y_down-y_up, y_down, y_up
            #cv2.imshow("ROI ad", roi)
            return (0, "ERR", 2, "ROI adjust error")

        pos1 = np.float32( [ [0,y_up], [roi_w-1,y_up], [roi_w-1, y_down] ] )
        pos2 = np.float32( [ [0,0], [roi_w-1,0], [roi_w-1,roi_h-1] ] )#

        M2 = cv2.getAffineTransform( pos1, pos2 )
        roi_ad = cv2.warpAffine( roi, M2, (roi_w,roi_h),
                                   borderValue=cv2.cv.ScalarAll(255) )
        roi = roi_ad
        #print "ROI adjust"
        


    #step 2. get single number roi
    cont, hier = cv2.findContours( roi.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )

    #bounding rect
    brs = []
    for c in cont:
        r = cv2.boundingRect( c )      
        for i in range( len(brs) ):
            # two contours have no overlap in x axis
            if r[0] > brs[i][0]+brs[i][2]+5 or r[0]+r[2]+5 < brs[i][0]: 
                pass
            else:
                #two contours should be merge, something like number "1"
                #brs[i] |= r
                brs[i] = [ min( brs[i][0], r[0] ),
                           min( brs[i][1], r[1] ),
                           max( brs[i][0]+brs[i][2], r[0]+r[2] ) - min( brs[i][0], r[0] ),
                           max( brs[i][1]+brs[i][3], r[1]+r[3] ) - min( brs[i][1], r[1] )]
                r = None
                break
        if r:
            brs.append( list( r ) )

    #filter that single number roi height > 60
    brs_tmp = []
    for br in brs:
        if br[3] > 60:
            brs_tmp.append( br )
    brs = brs_tmp

    #sorted the contours in x axis
    brs.sort()

    #check single number roi right position
    roi_sn_right = [55, 135, 215, 295]
    brs_len = len( brs )
    if brs_len not in range(3,5):
        return (0, "ERR", 3, "Single Number ROI error")
    else:
        for i in range( 1, brs_len+1 ):
            if brs[-i][0] + brs[-i][2] not in \
               range( roi_sn_right[-i]-15, roi_sn_right[-i]+15 ):
                return (0, "ERR", 3, "Single Number ROI error")
                    

    #step 3. get numbers
    numstr = ""
    for r in brs:
        #if roi_sn width < 40, just set it to "1"
        if r[2] < 40:
            numstr += "1"
        else:
            numstr += getSingleNumber( roi, r )   

        #draw single number roi  
        cv2.rectangle( roi, (r[0], r[1]), (r[0]+r[2], r[1]+r[3]), (255,255,255) )

    #for debug
    #print numstr
    cv2.imshow("roi", roi)

    #check whether numstr is ok
    #it is ok if "-1" appear first, else wrong like "*"
    #return number string removing "-"
    try:
        num = int( numstr )
        num = abs( num )
        return (1, str(num), 0, "Number OK")
    except:
        if numstr[-3:] == "CAL":
            return (1, "CAL", 0, "Display CAL")
        else:
            return (0, "ERR", 4, "Number error")
       


#-------------------------------------------------------

def test( testmode = 0):
    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)

    if testmode == 0: # img
        imagefile = "E://PIL/num/web_92.7.jpg"
        imagefile = "E://PIL/num/mobile_70.5.jpg"
        imagefile = "VID_20141216_110259-0.00.14.18.jpg"

        img = cv2.imread( imagefile )
        print getnumber( img )[1]
        cv2.imshow("Image", img)
        k = cv2.waitKey(0)

    elif testmode == 1:
        videoCapture = cv2.VideoCapture('Capture - 2.mp4')

        i = 0
        for i in range(480):
            i = i + 1
            success, frame = videoCapture.read()

        img = frame
        print getnumber( img )[1]
        cv2.imshow("Image", img)
        k = cv2.waitKey(0)
        
        

    else: #video
        videoCapture = cv2.VideoCapture('Capture - 4.mp4')

        #get fps and size
        fps = videoCapture.get(cv2.cv.CV_CAP_PROP_FPS)
        size = (int(videoCapture.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), 
                int(videoCapture.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
 
        success, frame = videoCapture.read()
        i = 0
        while success:
            i = i+1
            print i
            print getnumber( frame )[1]
            cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
            cv2.imshow("Image", frame)
            k = cv2.waitKey(10/int(fps)) #delay #1000/int(fps)
            if k==27:#ESC Key
                break
            success, frame = videoCapture.read() 
        videoCapture.release()

        
    cv2.destroyAllWindows()
    return

#----------------------------------------------------------------

#test(0)


