import numpy as np
import glob
import json
import cv2
import os


class CameraCalib:
    def __init__(self, fpath, viewCalib=True):
        self.fpath = fpath
        self.viewCalib = viewCalib
        self.K = []
        self.D = []

    # Load
    def calibParams(self):
        fpath = self.fpath
        with open(fpath) as f:
            data = json.load(f)
        self.K = np.array(data['K']) # camera matrix
        self.D = np.array(data['D']) # distortion matrix
        return self.K, self.D

    # dump
    def dumpParams(self, fpath, K, D):
        if not os.path.exists(fpath):
            directory = fpath.split('/')[0]
            os.mkdir(directory)
        self.K = K
        self.D = D
        data = dict()
        K = K.tolist()
        D = D.tolist()
        data['K'] = K
        data['D'] = D
        to_json = json.dumps(data, indent=4)
        with open(fpath, 'w') as f:
            f.write(to_json)

    # calibrate
    def calib(self, imgspath):
        # termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
        objp = np.zeros((6*7,3), np.float32)
        objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

        # Arrays to store object points and image points from all the images.
        objpoints = [] # 3d point in real world space
        imgpoints = [] # 2d points in image plane.
         
        imagespath = os.path.join(imgspath, '*.jpg')
        images = glob.glob(imagespath)

        for fname in images:
            img = cv2.imread(fname)
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (7,6),None)

            # If found, add object points, image points (after refining them)
            if ret == True:
                objpoints.append(objp)

                corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
                imgpoints.append(corners2)

                # Draw and display the corners
                if self.viewCalib:
                    orig = img.copy()
                    img = cv2.drawChessboardCorners(img, (7,6), corners2,ret)
                    cv2.putText(img, 'Press ESC to Abort', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                    cv2.imshow('calib',img)
                    k = cv2.waitKey(500)
                    if k == 27:
                        exit()
        cv2.destroyAllWindows()
        
        # calibration
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)

        print('camera matrix\n', mtx, '\n')
        print('distorsion matrix\n', dist, '\n')

        self.dumpParams(self.fpath, mtx, dist)
        dst = self.undistort(orig)

        orig = cv2.drawChessboardCorners(orig, (7,6), corners2, True)
        
        if self.viewCalib:            
            im_h = cv2.hconcat([orig, dst])
            cv2.putText(im_h, 'Press Any Key to Continue', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            cv2.imshow('result', im_h)
            cv2.waitKey(0)

        # reprojection error
        tot_error = 0
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
            error = cv2.norm(imgpoints[i],imgpoints2, cv2.NORM_L2)/len(imgpoints2)
            tot_error += error
        print ("total error: ", tot_error/len(objpoints))


    def undistort(self, img, method='CAM_UNDIS'):
        h,  w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.K,self.D,(w,h),1,(w,h)) # newcameramatrix, roi 
        dst = self.undistort_method1(img, newcameramtx) if method == 'CAM_UNDIS' else self.undistort_method2(img, newcameramtx)
        # crop the image
        x1,y1,w1,h1 = roi
        dst = dst[y1:y1+h1, x1:x1+w1]
        dst = cv2.resize(dst, (w, h))
        return dst

    def undistort_method1(self, img, cameramatrix):
        dst = cv2.undistort(img, self.K, self.D, None, cameramatrix)
        return dst

    def undistort_method2(self, img, cameramatrix):
        # undistort using remaping
        mapx,mapy = cv2.initUndistortRectifyMap(self.K,self.D,None,cameramatrix,(w,h),5)
        dst = cv2.remap(img,mapx,mapy,cv2.INTER_LINEAR)
        return dst