import cv2
import numpy as np

# Parameters
MIN_AREA = 150  # minimum contour area to be considered a larva
DIST_THRESH = 40  # min distance to existing tracker to be considered new

# Background subtractor
backSub = cv2.createBackgroundSubtractorMOG2()

# Load video
cap = cv2.VideoCapture("sample-video/testvideo2.mp4")
if not cap.isOpened():
    print("Error opening video file")
    exit()

# Use KCF tracker (can also try MIL or CSRT)
def create_tracker():
    return cv2.legacy.TrackerKCF_create()

trackers = []
boxes = []

while True:
    ret, frame = cap.read()
    if not ret:
        break

    fgMask = backSub.apply(frame)
    fgMask = cv2.erode(fgMask, None, iterations=1)
    fgMask = cv2.dilate(fgMask, None, iterations=2)

    contours, _ = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detections = []
    for cnt in contours:
        if cv2.contourArea(cnt) > MIN_AREA:
            x, y, w, h = cv2.boundingRect(cnt)
            detections.append((x, y, w, h))

    # Match new detections with existing boxes
    new_boxes = []
    for det in detections:
        dx, dy, dw, dh = det
        cx, cy = dx + dw // 2, dy + dh // 2
        matched = False
        for bx, by, bw, bh in boxes:
            bcx, bcy = bx + bw // 2, by + bh // 2
            dist = np.hypot(cx - bcx, cy - bcy)
            if dist < DIST_THRESH:
                matched = True
                break
        if not matched:
            tracker = create_tracker()
            tracker.init(frame, det)
            trackers.append(tracker)
            new_boxes.append(det)

    boxes.extend(new_boxes)

    # Update all trackers
    updated_boxes = []
    valid_trackers = []
    for tracker in trackers:
        success, box = tracker.update(frame)
        if success:
            x, y, w, h = map(int, box)
            updated_boxes.append((x, y, w, h))
            valid_trackers.append(tracker)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (x + w//2, y + h//2), 3, (0, 255, 0), -1)

    trackers = valid_trackers
    boxes = updated_boxes

    cv2.imshow("Tracked Larvae", frame)
    cv2.imshow("FG Mask", fgMask)
    if cv2.waitKey(30) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
