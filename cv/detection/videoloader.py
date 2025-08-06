import cv2
import numpy as np

def box_centroid(box):
    x, y, w, h = box
    return (x + w/2, y + h/2)

def euclidean_distance(c1, c2):
    return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

cap = cv2.VideoCapture("sample-video/testvideo2.mp4")
fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

trackers = []
boxes = []
colors = {}
object_id = 0
frame_count = 0
distance_threshold = 60  # pixels, adjust as needed

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    fgmask = fgbg.apply(gray)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    fgmask = cv2.dilate(fgmask, None, iterations=2)

    # Update existing trackers, remove lost ones
    new_trackers = []
    new_boxes = []
    new_colors = {}

    for i, tracker in enumerate(trackers):
        ok, box = tracker.update(frame)
        if ok:
            x, y, w, h = [int(v) for v in box]

            # Optional: filter boxes outside frame or too small to reduce noise
            if w > 10 and h > 10 and 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                new_trackers.append(tracker)
                new_boxes.append(box)
                new_colors[len(new_trackers) - 1] = colors[i]

    trackers = new_trackers
    boxes = new_boxes
    colors = new_colors

    # Every 15 frames, detect new objects and add trackers if sufficiently far from existing
    if frame_count % 15 == 0:
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 20 < area < 500:  # Adjust based on larva size
                x, y, w, h = cv2.boundingRect(cnt)
                detected_boxes.append((x, y, w, h))

        for det_box in detected_boxes:
            det_centroid = box_centroid(det_box)
            too_close = False
            for trk_box in boxes:
                trk_centroid = box_centroid(trk_box)
                dist = euclidean_distance(det_centroid, trk_centroid)
                if dist < distance_threshold:
                    too_close = True
                    break
            if not too_close:
                tracker = cv2.legacy.TrackerCSRT_create()
                tracker.init(frame, det_box)
                trackers.append(tracker)
                boxes.append(det_box)
                colors[len(trackers) - 1] = tuple(np.random.randint(0, 255, 3).tolist())
                object_id += 1

    # Draw all tracked boxes with IDs
    for i, box in enumerate(boxes):
        x, y, w, h = [int(v) for v in box]
        color = colors.get(i, (0, 255, 0))
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, f"ID: {i}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.imshow("Larva Tracking", frame)
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
