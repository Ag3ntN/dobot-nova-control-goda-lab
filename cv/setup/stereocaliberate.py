import cv2
import numpy as np
import glob

CHECKERBOARD = (9, 6)
SQUARE_SIZE = 25  # mm

# Prepare 3D object points
objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

objpoints = []       # 3D points
imgpoints_left = []  # Left 2D points
imgpoints_right = [] # Right 2D points

# Load image pairs
left_images = sorted(glob.glob("calib/lcam/*.png"))
right_images = sorted(glob.glob("calib/rcam/*.png"))

assert len(left_images) == len(right_images), "Mismatched number of images"

for left_path, right_path in zip(left_images, right_images):
    imgL = cv2.imread(left_path)
    imgR = cv2.imread(right_path)
    grayL = cv2.cvtColor(imgL, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY)

    # Find checkerboard corners
    retL, cornersL = cv2.findChessboardCorners(grayL, CHECKERBOARD, None)
    retR, cornersR = cv2.findChessboardCorners(grayR, CHECKERBOARD, None)

    if retL and retR:
        objpoints.append(objp)

        cornersL = cv2.cornerSubPix(grayL, cornersL, (11, 11), (-1, -1),
                                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
        cornersR = cv2.cornerSubPix(grayR, cornersR, (11, 11), (-1, -1),
                                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))

        imgpoints_left.append(cornersL)
        imgpoints_right.append(cornersR)

# Load your individual calibration results
# Replace these with your actual calibrated values
K1 = np.load("K_left.npy")
dist1 = np.load("dist_left.npy")
K2 = np.load("K_right.npy")
dist2 = np.load("dist_right.npy")

image_size = grayL.shape[::-1]

# Stereo calibration
flags = (cv2.CALIB_FIX_INTRINSIC)

ret, K1, dist1, K2, dist2, R, T, E, F = cv2.stereoCalibrate(
    objpoints,
    imgpoints_left,
    imgpoints_right,
    K1,
    dist1,
    K2,
    dist2,
    image_size,
    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5),
    flags=flags
)

print("Rotation (R):\n", R)
print("Translation (T):\n", T)
