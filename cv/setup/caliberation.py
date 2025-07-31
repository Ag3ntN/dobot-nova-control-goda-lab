import numpy as np
import glob
import cv2

# Setup checkerboard dimensions
CHECKERBOARD = (9, 6)  # 9 inner corners per row, 6 per column
SQUARE_SIZE = 25  # in mm

# 3D points in real-world space (z=0 since it's a flat board)
objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

# Arrays to store 3D and 2D points
objpoints = []  # 3D points
imgpoints = []  # 2D points
# Load all images
images = glob.glob('rcam/*.png')

if not images:
    raise ValueError("No images found. Check your folder path or file extension.")

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Save image size from the first image
    if 'img_shape' not in locals():
        img_shape = gray.shape[::-1]  # width, height

    # Find corners
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    if ret:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
        imgpoints.append(corners2)

        # Draw and show
        cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
        cv2.imshow('img', img)
        cv2.waitKey(100)

cv2.destroyAllWindows()

# Check if any corners were detected
if not objpoints:
    raise ValueError("No checkerboard corners were detected in any image.")

# Calibrate
ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img_shape, None, None)

print("Camera matrix:\n", K)
print("Distortion coefficients:\n", dist)
