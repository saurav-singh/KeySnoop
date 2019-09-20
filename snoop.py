#IMPORTS:
import sys
import pyaudio
import time
import random
import os
import wave
#import threa
from pyAudioAnalysis3 import audioTrainTest as aT
import threading
import time
from pydub import AudioSegment
import numpy
import queue
#from multiprocessing import Queue
from os import listdir
from os.path import isfile, join

#Thread Control
lo = threading.Lock()
onlyfiles = []

#Thread Class to play Audio segment
class playThread (threading.Thread):
    def __init__(self, file):
        threading.Thread.__init__(self)
        self.file = file
    def run(self):
        CHUNK = 1024

        wf = wave.open(self.file, 'rb')

        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data = wf.readframes(CHUNK)

        while data != '':
            stream.write(data)
            data = wf.readframes(CHUNK)

        stream.stop_stream()
        stream.close()

        p.terminate()




#Thread Class to queue record stream
class recordQThread (threading.Thread):
    def __init__(self, frames = []):
        threading.Thread.__init__(self)
        self.frames = frames
    def run(self):
           
            global q
            RATE = 44100           
            audiofile = AudioSegment(data=b''.join(self.frames),sample_width=2,frame_rate=RATE,channels=2)
            data = numpy.fromstring(audiofile._data, numpy.int16)
            x = []
            for chn in range(audiofile.channels):
                x.append(data[chn::audiofile.channels])
            x = numpy.array(x).T
           # print "X: " + str(len(x))
            lo.acquire()
            #print "Q: " + str(q.qsize())
            q.put(x)
            lo.release()


#Thread Class to record Audio Segment
class recordThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global q
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 44100
        RECORD_SECONDS = 0.3
        WAVE_OUTPUT_FILENAME = "output.wav"

        p = pyaudio.PyAudio()


        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK)

           # print("* HIT!")
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)  
            frames.append(data) 
   
        #recordQThread(frames).start()

        while True:
                frames.remove(frames[0])
                data = stream.read(CHUNK)  
                frames.append(data)
                recordQThread(frames).start()

def find(x):
    l = x[1].tolist()
    
    maX = max(l)
    if (maX > 0.65 and maX < 0.99):
        match_index = l.index(max(l))
        Sens = x[2][match_index]

        # if (Sens != "NOISE"):
        #     print(Sens)
    time.sleep(1)
    print(x)

#Thread Class to Analyse Audio Segment
class analyseThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global q

        # while True:
            
        #     lo.acquire()
            
        #     if not q.empty():
        #         f = q.get()
        #         x = aT.fileClassification(f,"svmTaps","svm")
        #         print(x)
            
        #     lo.release()
            
        # flagStart = False

        while True:
            lo.acquire()

            while not q.empty():
                f = q.get()
                x = aT.fileClassification(f, "svmTaps", "svm")
                
                q.task_done()
                flagStart = True
                if flagStart:
                    flagStart = False 
                    onlyObj = [f for f in listdir('.') if not isfile(join('.', f))]
                    onlyObj.remove("pyAudioAnalysis3")
                    counter = 2

                    find(x)
            
                    
                        # if (Sens != "Noise"):
                        #     print(Sens)

                   

                        
            lo.release()






##############
##############       
#MAIN FUNCTION:

def mainTap(ch):

    onlyfiles = [f for f in listdir('.') if not isfile(join('.', f))]
    #onlyfiles.remove("drums")
    onlyfiles.remove("pyAudioAnalysis3")
    onlyfiles.remove("__pycache__")
    #onlyfiles.remove("images")
    startMode = False
    
    global q 
    q = queue.Queue(0)
     
    #ch = A (start Thread for drums) | B (Record new Data) | C (Start Thread for LaunchPad)   
    if(str(ch)=='A'):
        print("**************************")
        print(onlyfiles)
        print("***************************")
        aT.featureAndTrain(onlyfiles, 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm", "svmTaps", False)
        
    elif(str(ch)=='B'):
        ch = 'x'
        surfaceName = input("Surface Name: ")
        while(surfaceName != 'x'):
            numberOfInputs = input("Number of Data Points: ")
            for i in range(0,int(numberOfInputs)):
                print ("Input " + str(i+1))
                addSurfacePoint(surfaceName)
            surfaceName = input("Surface Name: ")

    elif(str(ch)=='C'):
        startMode = True
        print("Started\n\n")
    

    if (startMode):
        recordThread().start()
        analyseThread().start()
        #analyseThread().start( )



def addSurfacePoint(surfacePointName):
    print ("Starting Record")
    recordSurfacePoint(surfacePointName)

def recordSurfacePoint(surfacePointName):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 0.9
    randomFileName = str((random.random() * 100) * (random.random() * 100))
    WAVE_OUTPUT_FILENAME = randomFileName + ".wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK)

    print("* Recording in ")
    print (".. 2")
    time.sleep(0.2)
    print (".. 1")
    time.sleep(0.2  )
    print ("Tap!")
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    if not os.path.exists (surfacePointName):
        os.mkdir(str(surfacePointName))

    os.rename(WAVE_OUTPUT_FILENAME, surfacePointName + "/" + WAVE_OUTPUT_FILENAME)
