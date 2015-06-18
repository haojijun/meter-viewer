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

#points to pick pixel



#for segmentvalue2 roi adjust
testpoints2 =((0.05, 0.50), #-
              (0.12,0.30), #1b
              (0.11,0.70), #1c
              (0.12,0.95), #1h
              (0.27, 0.08), #2a
              (0.31, 0.30), #2b
              (0.30, 0.70), #2c
              (0.25, 0.92), #2d
              (0.20, 0.70), #2e
              (0.21, 0.30), #2f
              (0.26, 0.50), #2g
              (0.31, 0.95), #2h
              (0.46, 0.08), #3a
              (0.51, 0.30), #3b
              (0.49, 0.70), #3c
              (0.44, 0.92), #3d
              (0.39, 0.70), #3e
              (0.41, 0.30), #3f
              (0.45, 0.50), #3g
              (0.51, 0.95), #3h
              (0.65, 0.08), #4a
              (0.695, 0.30), #4b
              (0.68, 0.70), #4c
              (0.63, 0.92), #4d
              (0.58, 0.70), #4e
              (0.59, 0.30), #4f
              (0.64, 0.50), #4g
              (0.695, 0.95), #4h
              (0.96, 0.85)) #dBm



#8-segment number
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
               (0, 0, 0, 0, 0, 0, 0), #MASK_N, same as 0
               (1, 0, 0, 1, 1, 1, 0), #C
               (1, 1, 1, 0, 1, 1, 1), #A
               (0, 0, 0, 1, 1, 1, 0)) #L

MASK_C = (1, 0, 0, 1, 1, 1, 0) #CAL
MASK_A = (1, 1, 1, 0, 1, 1, 1)
MASK_L = (0, 0, 0, 1, 1, 1, 0)

MASK_N = (0, 0, 0, 0, 0, 0, 0) #no number display

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

    #print cv2.cv.BoxPoints( box )
    #segmentvalue2( gray, box, testpoints2, threshold_2 )

    #number_points = segmentvalue( gray, box, testpoints, threshold_2 )
    

    #return getnumber( number_points )



#need update
#from points to segments
def getsegments( img, points, disp=1 ):
    values = []
    segmentcolor = (255, 0, 0)

    #print len(img)
    #print len(img[0])
    #print img[50]

    for p in points:
        p_x = int(roi_w*p[0])
        p_y = int(roi_h*p[1])
        #thresh for number segment
        if img[p_y][p_x]:
            #print p_x, p_y, img[p_y][p_x]
            values.append(1)
        else:
            values.append(0)

        if disp:
            cv2.circle( img, (p_x,p_y), 3, segmentcolor, -1 )
            #print p_x, p_y

    return values

def getSingleNumber( img, cont, disp=0 ):
    """
    single number ROI size: 60x100
    """
    pos1 = np.float32( [ [cont[0],0],
                         [cont[0]+cont[2],0],
                         [cont[0]+cont[2],99] ] )
    pos2 = np.float32( [ [0,0],
                         [59,0],
                         [59,99] ] )#

    M = cv2.getAffineTransform( pos1, pos2 )
    #roi_sn mean roi_singlenumber
    roi_sn = cv2.warpAffine( img, M, (60,100),
                             borderValue=cv2.cv.ScalarAll(255) )

    seg7 = 7*[0]
    
    if sum( roi_sn[25][0:20] ) > 0: #f,5
        seg7[5] = 1   
    if sum( roi_sn[25][40:60] ) > 0: #b,1
        seg7[1] = 1   
    if sum( roi_sn[75][0:20] ) > 0: #e,4
        seg7[4] = 1   
    if sum( roi_sn[75][40:60] ) > 0: #c,2
        seg7[2] = 1

    #for "7." or "L"
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
    #print seg7

    cv2.imshow( "roi_sn", roi_sn )

    if number_mask.count( tuple( seg7 ) ):
        #imwritefile = "E://PIL/num/singlenum/normal/" + str(cv2.getTickCount()) + ".jpg"
        #cv2.imwrite( imwritefile, roi_sn )
        return str( number_mask.index( tuple( seg7 ) ) )
    else:
        #imwritefile = "E://PIL/num/singlenum/error/" + str(cv2.getTickCount()) + ".jpg"
        #cv2.imwrite( imwritefile, roi_sn )
        return "*"

    

    return
    

#
def getnumber( img ):
    thresh_roi = 20
    color = (255, 255, 0)
    numbers = ""

    #step 1. get box
    roi = getroi( img )
    if roi is None:
        return (0, "ERR", 1, "ROI get error")

    #segments = getsegments( roi, testpoints2, disp=0 )

    if sum( roi[50][15*4:75*4] ) < 5*255:
        return (0, "OFF", 0, "Display OFF")
    else:
        #adjust the roi
        y_up = 49                        
        for i in range(0,20,2):
            if sum(roi[i]) > thresh_roi*255:
                #print i
                y_up = i
                break

        y_down = 50
        for i in range(99,80,-2):
            if sum(roi[i]) > thresh_roi*255:
                #print i
                y_down = i
                break

        if (y_down - y_up) < 0.6 * (roi_h+10+10):
            return (0, "ERR", 2, "ROI adjust error")

        pos1 = np.float32( [ [0,y_up], [roi_w-1,y_up], [roi_w-1, y_down] ] )
        pos2 = np.float32( [ [0,0], [roi_w-1,0], [roi_w-1,roi_h-1] ] )#

        M2 = cv2.getAffineTransform( pos1, pos2 )
        roi_ad = cv2.warpAffine( roi, M2, (roi_w,roi_h),
                                   borderValue=cv2.cv.ScalarAll(255) )
        roi = roi_ad
        #print "ROI adjust"
        

    #for debug
    kernel = np.ones((5,5),np.uint8)
    #roi = cv2.morphologyEx(roi, cv2.MORPH_CLOSE, kernel, iterations = 3)
    cont, hier = cv2.findContours( roi.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )
    #cv2.drawContours( roi, cont, -1, (255,255,255) )
    
    brs = []
    for c in cont:
        r = cv2.boundingRect( c )
        
        for i in range( len(brs) ):
            if r[0] > brs[i][0]+brs[i][2]+5 or r[0]+r[2]+5 < brs[i][0]: # bu xiang jiao
                pass
            else:
                #brs[i] |= r
                brs[i] = [ min( brs[i][0], r[0] ),
                           min( brs[i][1], r[1] ),
                           max( brs[i][0]+brs[i][2], r[0]+r[2] ) - min( brs[i][0], r[0] ),
                           max( brs[i][1]+brs[i][3], r[1]+r[3] ) - min( brs[i][1], r[1] )]
                r = None
                break
        if r:
            brs.append( list( r ) )
    # height > 60
    brs_1 = []
    for br in brs:
        if br[3] > 60:
            brs_1.append( br )

    # sorted
    #print brs_1
    brs_1.sort()
    #print brs_1
    
            
    #print len( cont ), len( brs ), len( brs_1 )
    brs = brs_1
    numstr = ""
    for r in brs:
        if r[2] > 40:
            numstr += getSingleNumber( roi, r )    
        else:
            numstr += "1"
        cv2.rectangle( roi, (r[0], r[1]), (r[0]+r[2], r[1]+r[3]), (255,255,255) )


    print numstr
       


    
    #
    segments = getsegments( roi, testpoints2, disp=1 )
    #print segments

    cv2.imshow("roi", roi)

    if tuple(segments[4:11]) == MASK_C \
       and tuple(segments[12:19]) == MASK_A \
       and tuple(segments[20:27]) == MASK_L:
        return (0, "CAL", 0, "Display CAL")
    
    #three right number exist
    if number_mask.count(tuple( [0]+segments[1:3]+[0,0,0,0] ) ) \
       and number_mask.count(tuple(segments[4:11])) \
       and number_mask.count(tuple(segments[12:19])) \
       and number_mask.count(tuple(segments[20:27])):
#        if segments[3] + segments[11] + segments[19] + segments[27] > 1:
#            return (0, "ERR", 3, "More dots error")
#        if segments[0]:
#            numbers += '-'
        numbers += str( number_mask.index(tuple([0]+segments[1:3]+[0,0,0,0])) % 10 )
#        if segments[3]:
#            numbers += '.'
        numbers += str( number_mask.index(tuple(segments[4:11])) % 10 )
#        if segments[11]:
#            numbers += '.'
        numbers += str( number_mask.index(tuple(segments[12:19])) % 10 )
#        if segments[19]:
#            numbers += '.'
        numbers += str( number_mask.index(tuple(segments[20:27])) % 10 )
#        if segments[27]:
#            numbers += '.'
        #if segments[25]:
        #    number_str += " dBm"
        #else:
        #    number_str += " dB"

        return (1, numbers, 0, "Number OK")
                         
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


