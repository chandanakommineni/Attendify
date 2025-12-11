import cv2
from deepface import DeepFace
from attendance import mark_attendance
import numpy as np

cap = cv2.VideoCapture(0)

recognized = set()          # store recognized people
unknown_faces = 0           # counter for unknown

# Haar Cascade for drawing boxes (DeepFace.find does not provide boxes)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def generate_frames():

    while True:
        success, frame = cap.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ✅ detect faces for drawing boxes
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        detected_names = []

        try:
            result = DeepFace.find(
                img_path=frame,
                db_path="training_data",
                model_name="VGG-Face",
                enforce_detection=False
            )

            if len(result) > 0:
                identity = result[0]['identity'][0]
                name = identity.split("\\")[-2]
                detected_names.append(name)

                # ✅ Save attendance only once per person per session
                if name not in recognized:
                    recognized.add(name)
                    print(f"Detected: {name} → Saving attendance")
                    mark_attendance(recognized)

        except Exception:
            pass

        # ✅ Draw boxes for detection
        for (x, y, w, h) in faces:

            # ✅ If recognized → green box
            if len(detected_names) > 0:
                name = detected_names[0]

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{name} - Present",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2)

            else:
                # ✅ Unknown → red box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 255),
                            2)

        # ✅ Encode frame for Flask streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
