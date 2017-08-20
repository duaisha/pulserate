#!/usr/bin/env python2.7

from lib.device import VideoStream
from lib.processors import findFaceGetPulse
from lib.interface import plotXY, imshow, waitKey,destroyWindow, moveWindow
from pprint import pprint
import numpy as np
import datetime
import sys

class Pulse(object):

    def __init__(self,filename=(sys.argv[1] if len(sys.argv) > 1 else None)):
        if (filename is None):
            raise Exception("Filename unset")

        self.camera = VideoStream(filename=filename) #first camera by default
        self.bpms = []

        #Containerized analysis of recieved image frames (an openMDAO assembly)
        #is defined next.

        #This assembly is designed to handle all image & signal analysis,
        #such as face detection, forehead isolation, time series collection,
        #heart-beat detection, etc.

        #Basically, everything that isn't communication
        #to the camera device or part of the GUI
        self.processor = findFaceGetPulse(bpm_limits = [50,160],
                                          data_spike_limit = 2500.,
                                          face_detector_smoothness = 10.)


        while (self.main_loop()):
            sys.stderr.write(". ")
        sys.stderr.write("\n\n")

    def write_csv(self):
        """
        Writes current data to a csv file
        """
        bpm = " " + str(int(self.processor.measure_heart.bpm))
        fn = str(datetime.datetime.now()).split(".")[0] + bpm + " BPM.csv"
        
        data = np.array([self.processor.fft.times, 
                         self.processor.fft.samples]).T
        np.savetxt(fn, data, delimiter=',')

    def median(self):
        return np.median(self.bpms)

    def toggle_search(self):
        """
        Toggles a motion lock on the processor's face detection component.

        Locking the forehead location in place significantly improves
        data quality, once a forehead has been sucessfully isolated. 
        """
        state = self.processor.find_faces.toggle()
        if not state:
        	self.processor.fft.reset()
        print "face detection lock =",not state


    def capture_bpms(self):
        try:
            if 300 > self.processor.measure_heart.bpm > 10:
                self.bpms.append(self.processor.measure_heart.bpm)
            else:
                sys.stderr.write("D")
        except NameError:
            return



    def main_loop(self):
        """
        Single iteration of the application's main loop.
        """
        # Get current image frame from the camera
        try:
            frame = self.camera.get_frame()
            if ( frame is None ):
                print ("EOF")
                return False
            self.h,self.w,_c = frame.shape
        except AttributeError:
            print ("ERR01 yo")
            return False
        

        #display unaltered frame
        imshow("Original",frame)

        #set current image frame to the processor's input
        self.processor.frame_in = frame
        #process the image frame to perform all needed analysis
        self.processor.run()
        #collect the output frame for display
        output_frame = self.processor.frame_out

        #show the processed/annotated output frame
        imshow("Processed",output_frame)
        self.capture_bpms()

        #create and/or update the raw data display if needed
        #if self.bpm_plot:
        #    testfk = self.make_bpm_plot()
        #    print(testfk)

        #handle any key presses
        #self.key_handler()
        return True

if __name__ == "__main__":
    App = Pulse()
    print App.median()

