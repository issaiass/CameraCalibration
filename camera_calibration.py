from CameraCalib.CameraCalib import CameraCalib
from xml.etree import ElementTree as et
import cv2
import argparse
import ast

parser = argparse.ArgumentParser(description='Camera Calibration Procedure')
parser.add_argument('--xml', help='Path to XML parameters for model excecution')
args = parser.parse_args()

tree = et.parse(args.xml)
root = tree.getroot()

xmlfile = root.findall('camera')
for params in xmlfile:
    calibrationfile = params.find('calibrationFile').text  # This is the path of the calibration file, generated or not
    imagesfolder = params.find('imagesFolder').text  # This is the path of the images folder with chessboard
    viewcalibration = ast.literal_eval(params.find('viewCalibration').text)  # save file or not

# Camera Calibration Usage
camc = CameraCalib(calibrationfile, viewcalibration)  # contruct the calibrator with the path to store the file, enable view calibration
camc.calib(imagesfolder)  # get the images from the current working directory

# Main Application usage
# construct the calibrator with the path to load the file, must exist!
#camc = CameraCalib(calibrationfile, viewcalibration) # contruct the calibrator with the path to load the file, second parameter unafects the usage
#camc.calibParams()  # load the camera calibration parameters
#img = cv2.imread('calibimgs/left03.jpg')  # load the image
#img = camc.undistort(img)  # undistort the image
#cv2.imshow('result', img)  # show the result
#cv2.waitKey(0)  # wait for finish by any key