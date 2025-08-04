import cv2
import numpy as np

# Load video
video_path = "image_2025-08-04T13-24-06.8.mp4"
cap = cv2.VideoCapture(video_path)

# Background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25, detectShadows=False)

# Setup blob detector parameters
params = cv2.SimpleBlobDetector_Params()
params.filterByArea = True
params.minArea = 20
params.maxArea = 500
params.filterByCircularity = False
params.filterByConvexity = False
params.filterByInertia = False

detector = cv2.SimpleBlobDetector_create(params)

# Tracking setup
next_id = 0
tracked_objects = {}  # id: (x, y)

def euclidean(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def assign_ids(centroids, tracked_objects, max_distance=50):
    global next_id
    new_objects = {}

    for c in centroids:
        matched = False
        for obj_id, pos in tracked_objects.items():
            if euclidean(c, pos) < max_distance:
                new_objects[obj_id] = c
                matched = True
                break
        if not matched:
            new_objects[next_id] = c
            next_id += 1
    return new_objects

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    fgmask = fgbg.apply(frame)

    # Clean mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel, iterations=2)

    # Blob detection
    keypoints = detector.detect(fgmask)

    # Get centroids
    centroids = [tuple(map(int, kp.pt)) for kp in keypoints]
    tracked_objects = assign_ids(centroids, tracked_objects)

    # Draw results
    for obj_id, (x, y) in tracked_objects.items():
        cv2.circle(frame, (x, y), 10, (0, 255, 0), 2)
        cv2.putText(frame, f"ID: {obj_id}", (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    cv2.imshow("Tracking", frame)
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
