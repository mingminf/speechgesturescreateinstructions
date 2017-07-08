import sys
import threading
import numpy as np
import cv2
import datetime
import Leap, sys, thread, time
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
from scipy.spatial import distance
import speech_recognition as sr
import pyttsx
import msvcrt
import logging


logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )


class SpeechCommand(object):
    def __init__(self, start=""):
        self.lock = threading.Lock()
        self.speech_cmd = start

    def set(self, cmd):
        #logging.debug('Waiting for lock')
        self.lock.acquire()
        try:
            #logging.debug('Acquired lock')
            self.speech_cmd = cmd
        finally:
            self.lock.release()

DEBUG = True
cmd = SpeechCommand()
frameId = 0

class SpeechRecognizer(threading.Thread):

    def __init__(self):
        super(SpeechRecognizer, self).__init__()
        self.setDaemon(True)
        self.recognized_text = "initial"
        self.r = sr.Recognizer()
        # see http://pyttsx.readthedocs.org/en/latest/engine.html#pyttsx.init
        self.speech_engine = pyttsx.init('sapi5')
        self.speech_engine.setProperty('rate', 150)
        self.label = False

    def speak(self, sentence):
        self.speech_engine.say(sentence)
        self.speech_engine.runAndWait()

    def emphasizeImage(self):
        global cmd
        cmd.set("emphasize")
        self.speak("OK. Show me where to emphazie?")

    def hightlightImage(self):
        global cmd
        cmd.set("highlight")
        self.speak("OK. Show me where to highlight?")

    def calloutImage(self):
        global cmd
        cmd.set("callout")
        self.speak("OK. Show me which area to callout?")

    def cropImage(self):
        global cmd
        cmd.set("crop")
        self.speak("OK. Show me which area to crop?")

    def annotateImage(self):
        global cmd
        cmd.set("annotate")
        self.speak("OK. What do you want to annotate?")

    def labelImage(self):
        global cmd
        cmd.set("label")
        self.speak("OK. What do you want to label?")
        self.label = True

    def recordAction(self):
        global cmd
        cmd.set("action")
        self.speak("OK. Show me the action.")

    def run(self):
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

        while True:
            time.sleep(0.1)
            with sr.Microphone(device_index=1) as source:
                self.r.adjust_for_ambient_noise(source)
                audio = self.r.listen(source)
            try:
                self.recognized_text = self.r.recognize_google(audio)
                if self.label:
                    global cmd
                    cmd.set(self.recognized_text)
                    self.speak("I hear: " + self.recognized_text)
                    self.label = False
                else:
                    if "emphasize" in self.recognized_text:
                        self.emphasizeImage()
                    elif "highlight" in self.recognized_text:
                        self.hightlightImage()
                    elif "callout" in self.recognized_text:
                        self.calloutImage()
                    elif "crop" in self.recognized_text:
                        self.cropImage()
                    elif "annotate" in self.recognized_text:
                        self.annotateImage()
                    elif "label" in self.recognized_text:
                        self.labelImage()
                    elif "action" in self.recognized_text:
                        self.recordAction()
                    else:
                        pass
            except sr.UnknownValueError:
                self.recognized_text = "I didn't hear you"
                #self.speak(self.recognized_text)
            except sr.RequestError as e:
                print("Recog Error; {0}".format(e))

        global cmd
        cmd.set("")


def to_np(v):
    return np.float32([v[0], v[1], v[2]])

def dis(v1, v2):
    return distance.euclidean(v1,v2)

def main():
    # start the speech recognition in a seprate thread
    recognizer = SpeechRecognizer()
    recognizer.start()

    # set up the leap motion controller
    controller = Leap.Controller()
    controller.set_policy_flags(Leap.Controller.POLICY_BACKGROUND_FRAMES)

    retval = 13.239646902
    rvec = np.float32([[[ 0.04057411],
           [ 1.93823599],
           [ 2.4833007 ]]])
    tvec = np.float32([[[  8.46050102],
    [-45.35019832],
    [  6.36817543]]])
    cm = np.float32([[ 1558.25767175,  0. ,962.81545469], [0. ,1715.42003938 ,  860.64197358], [0.  ,0.  ,1.]])
    dist = np.float32([[-0.14262444,  0.88573637,  0.07492765, -0.00911298, -1.1421962 ]])


    #this parameters are for the other LP
    """retval = 12.4304243285
    rvec = np.float32([[[-0.07403326],
           [ 2.15789327],
           [ 2.24751369]]])
    tvec = np.float32([[[ 11.12213436],
    [-44.35437003],
    [ 13.63024487]]])
    cm = np.float32([[ 1518.47267182,     0.,           949.56413171],
[    0.,          1491.83826716,   491.15957871],
[    0.,             0.,             1.        ]])
    dist = np.float32([[-0.18717047,  2.01084122,  0.01116464,  0.0163355,  -4.53963572]])"""

    if DEBUG:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG') #"XVID" was tested and it did not work
        localtime = time.strftime("%H-%M-%S-%d-%m-%Y")
        outputvideo = cv2.VideoWriter('./data/videoinstructions_'+ localtime +'.avi', fourcc, 20, (1920,1080))
        #outputvideo = cv2.VideoWriter('videoinstructions.avi', fourcc, 20, (640,480))
        outputfile = open('./data/videoinstructions_'+ localtime +'.txt', "w+")

    # set up webcamera and video processing part
    cv2.startWindowThread()
    cap = cv2.VideoCapture(2)
    #ret = cap.set(3,640);
    #ret = cap.set(4,480);
    #ret = cap.set(3,1280);
    #ret = cap.set(4,720);
    #ret = cap.set(3,960);
    #ret = cap.set(4,720);
    ret = cap.set(3,1920);
    ret = cap.set(4,1280);

    colors = [(255,255,0),(255,0,0),(0,255,0),(255,0,255)]

    global frameId,cmd, DEBUG
    finger_x = 0
    finger_y = 0
    while(True):
        ret, img = cap.read()
        #H, W = img.shape[:2]
        frame = controller.frame()

        tip = None
        for hand1 in frame.hands:
            tip_pos = to_np([0,0,0])
            max_dis = 0
            hand_center = hand1.stabilized_palm_position #__palm_position
            for f in hand1.fingers:
                for bn in range(4):
                    bone = f.bone(bn)
                    if bone.is_valid:
                        if dis(to_np(bone.prev_joint), to_np(hand_center)) > max_dis:
                            max_dis =  dis(to_np(bone.prev_joint), to_np(hand_center))
                            tip_pos = to_np(bone.prev_joint)
                        xy1 = cv2.projectPoints(np.float32([to_np(bone.prev_joint)]), rvec[0], tvec[0], cm, dist)[0][0][0]
                        xy2 = cv2.projectPoints(np.float32([to_np(bone.next_joint)]), rvec[0], tvec[0], cm, dist)[0][0][0]
                        """if bn == 3:
                            tip = (xy1[0],xy1[1])
                            #indicate the index finger
                            cv2.circle(img, tip, 15, (0,0,255), -1)"""
                        try:
                            cv2.line(img, (xy1[0],xy1[1]) , (xy2[0],xy2[1]), (255,255,255) , 3)
                            cv2.circle(img, (xy1[0],xy1[1]), 5, colors[bn], -1)
                            #cv2.circle(img, (xy2[0],xy2[1]), 5, colors[bn], -1)
                        except:
                            pass

            xy = cv2.projectPoints(np.float32([tip_pos]), rvec[0], tvec[0], cm, dist)[0][0][0]
            finger_x = xy[0]
            finger_y = xy[1]
            try:
                cv2.circle(img, (xy[0],xy[1]), 10, (0,0,255), -1)
            except:
                pass
            """for f in hand1.fingers.finger_type(1):
                tip = f.tip_position
                xy = cv2.projectPoints(np.float32([(tip[0], tip[1], tip[2])]), rvec[0], tvec[0], cm, dist)[0][0][0]
                try:
                    cv2.circle(img, (xy[0],xy[1]), 10, (0,0,255), -1)
                except:
                    pass"""

        keycode = cv2.waitKey(1) & 0xff
        if  keycode == ord('q'):
            break
        #img = cv2.flip(img, 0)
        #img = cv2.flip(img, 1)
        if DEBUG:
            outputvideo.write(img)
            outputfile.write('{},{},{},{}\n'.format(frameId, finger_x, finger_y, cmd.speech_cmd))
            #cmd.set("")

        cv2.imshow('frame', img)
        frameId = frameId + 1

    cv2.destroyWindow('frame')
    cap.release()

    if DEBUG:
        outputvideo.release()
        outputfile.close()

    cv2.destroyAllWindows()
    controller.clear_policy(Leap.Controller.POLICY_BACKGROUND_FRAMES)


if __name__ == "__main__":
    main()
