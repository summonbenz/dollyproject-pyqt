from Tkinter import *
import ttk
#---------- VERSION 3-------------
# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import imutils
import numpy as np
import atexit
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

root = Tk()


x=y=w=h=selectX=selectY=selectWidth=selectHeight=0

def left():
    myMotor_front.run(Adafruit_MotorHAT.FORWARD)
    myMotor_back.run(Adafruit_MotorHAT.FORWARD)
    print "\tSpeed up...to"+str(mySpeed)
    myMotor_front.setSpeed(mySpeed)
    myMotor_back.setSpeed(mySpeed)
    time.sleep(0.01)

def right():
    myMotor_front.run(Adafruit_MotorHAT.BACKWARD)
    myMotor_back.run(Adafruit_MotorHAT.BACKWARD)
    print "\tSpeed up...to"+str(mySpeed)
    myMotor_front.setSpeed(mySpeed)
    myMotor_back.setSpeed(mySpeed)
    time.sleep(0.01)

def stop():
    turnOffMotors()

def turnOffMotors():
    mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (480, 320)
#camera.ISO = 100
#camera.brightness = 65
#camera.contrast = 50
camera.exposure_mode = 'fixedfps'
#camera.framerate = 32
camera.rotation = 0
rawCapture = PiRGBArray(camera, size=(480, 320))

min_area = 500000

boundLeft = 120
boundRight = 380

fgbg = cv2.createBackgroundSubtractorMOG2()
# allow the camera to warmup
time.sleep(0.1)

firstFrame = None
mode = 1
textControl = None
checkMode2 = None

mySpeed = 255

#intital motor
print ("initial motor at "+str(mySpeed))

mh = Adafruit_MotorHAT(addr=0x60)
atexit.register(turnOffMotors)
myMotor_front = mh.getMotor(1)
myMotor_back = mh.getMotor(4)

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    if mode == 1:
        textMode = "Object Detection"
        # grab the raw NumPy array representing the image, then initialize the timestamp
        # and occupied/unoccupied text
        image = frame.array
        image = imutils.resize(image, width=480)
        text = "Not Ready"
        fgmask = fgbg.apply(image)
        # show the frame
        #cv2.imshow("Original", image)
        #cv2.imshow("Mask", fgmask)

        thresh = fgmask.copy()
        (_, cnts, _) = cv2.findContours(thresh, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

        # loop over the contours
        for c in cnts:
            if cv2.contourArea(c) > 1000:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = "Occupied"
                break

        #qcv2.putText(frame, "Room Status: {}".format(text),(10, 20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        #cv2.imshow("Security Feed", image)
        #cv2.imshow("Thresh", thresh)
        #cv2.imshow("Frame Delta", frameDelta)

        key = cv2.waitKey(1) & 0xFF

        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            crop_img = image[y: y + h, x: x + w]
            #cv2.imshow("cropped", crop_img)
            mode = 2
            #break

        cv2.imshow("Tracking Mode", image)

    elif mode == 2:
        if checkMode2 is None:
            checkMode2 = True
            textMode = "Object Tracking"
            image = frame.array
            image = imutils.resize(image, width=480)
            output = image.copy()
            c,r,w,h = x, y, w, h
            track_window = (c,r,w,h)
            # set up the ROI for tracking
            roi = image[r:r+h, c:c+w]
            hsv_roi =  cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_roi, np.array((0., 60.,32.)), np.array((180.,255.,255.)))
            roi_hist = cv2.calcHist([hsv_roi],[0],mask,[180],[0,180])
            cv2.normalize(roi_hist,roi_hist,0,255,cv2.NORM_MINMAX)

            # Setup the termination criteria, either 10 iteration or move by atleast 1 pt
            term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1 )

        image = frame.array
        image = imutils.resize(image, width=480, height=320)

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        #cv2.imshow("color", hsv)
        dst = cv2.calcBackProject([hsv],[0],roi_hist,[0,180],1)
        ret, track_window = cv2.meanShift(dst, track_window, term_crit)
        x,y,w,h = track_window
        output = cv2.rectangle(image, (x,y), (x+w,y+h), 255,2)
        cv2.putText(output, " {}".format(textControl),(10, 20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(output, "("+str(x)+","+str(y)+") : ("+str(x+w)+","+str(y+h)+")",(10, 250),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        #check motion
        if x<boundLeft:
            textControl = "RIGHT"
            right()
        elif x+w>boundRight:
            textControl = "LEFT"
            left()

        else:
            textControl = ""
            stop()



        output = image.copy()
        cv2.imshow("Tracking Mode", output)




        key = cv2.waitKey(1) & 0xFF
        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break


cv2.waitKey(0)
cv2.destroyAllWindows()
