import socket
import mysql.connector
import cv2
import mediapipe as mp
from multiprocessing import Process, Queue, Value
from queue import Empty, Full
import os
import numpy as np
from deepface import DeepFace

# ================= CONFIG =================

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

rtsp_url = "rtsp://admin:admin123@10.101.0.12:554/avstream/channel=1/stream=0.sdp"
CAPTURED_IMAGE_PATH = "/home/st/jositg/captured_face.png"

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|max_delay;0"

FRAME_BUFFER = 15
MIN_FACE_WIDTH = 180

mp_face_detection = mp.solutions.face_detection

# ================= DATABASE =================

def query_database(epc):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="YourStrongPassword@123",
            database="testDB"
        )
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM uhfdatabase WHERE EPC = %s"
        cursor.execute(query, (epc,))
        record = cursor.fetchone()
        cursor.close()
        conn.close()
        return record
    except Exception as e:
        print(f"Database Error: {e}")
        return None

# ================= SHARPNESS =================

def sharpness_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

# ================= CONTINUOUS CAMERA PROCESS =================
# Camera runs non-stop in background, always capturing
# When trigger_flag is set, it captures the best face and saves it
# then sets done_flag to signal main process

def continuous_camera(trigger_flag, done_flag, stop_flag):
    detector = mp_face_detection.FaceDetection(
        model_selection=1,
        min_detection_confidence=0.7
    )

    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Cannot open RTSP stream")
        stop_flag.value = True
        return

    print("✅ RTSP Connected - Camera running continuously in background")

    frame_buffer = []

    while not stop_flag.value:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_buffer.append(frame)
        if len(frame_buffer) > FRAME_BUFFER:
            frame_buffer.pop(0)

        # Only process when triggered by an EPC
        if trigger_flag.value and len(frame_buffer) >= FRAME_BUFFER:
            trigger_flag.value = False  # Reset trigger

            best_frame = max(frame_buffer, key=sharpness_score)
            frame_buffer.clear()

            rgb = cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)

            if not results.detections:
                print("❌ No face detected")
                done_flag.value = True
                continue

            h, w, _ = best_frame.shape
            bbox = results.detections[0].location_data.relative_bounding_box

            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)

            if width < MIN_FACE_WIDTH:
                print("❌ Face too small")
                done_flag.value = True
                continue

            padding = 50
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(w, x + width + padding)
            y2 = min(h, y + height + padding)

            face = best_frame[y1:y2, x1:x2]
            if face.size == 0:
                done_flag.value = True
                continue

            face = cv2.resize(face, (400, 400), interpolation=cv2.INTER_CUBIC)
            face = cv2.convertScaleAbs(face, alpha=1.15, beta=10)

            cv2.imwrite(CAPTURED_IMAGE_PATH, face)
            print("✅ High-quality face captured and saved")

            done_flag.value = True  # Signal main that capture is done

    detector.close()
    cap.release()

# ================= IMAGE COMPARISON =================

def compare_faces(captured_path, database_image_path):
    try:
        print("Extracting embeddings... 🔄")

        emb1 = DeepFace.represent(
            img_path=captured_path,
            model_name="Facenet512",
            detector_backend="retinaface",
            enforce_detection=True
        )[0]["embedding"]

        emb2 = DeepFace.represent(
            img_path=database_image_path,
            model_name="Facenet512",
            detector_backend="retinaface",
            enforce_detection=True
        )[0]["embedding"]

        emb1 = np.array(emb1)
        emb2 = np.array(emb2)

        cosine_similarity = np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )
        euclidean_distance = np.linalg.norm(emb1 - emb2)

        print("\nEmbedding Length:", len(emb1))
        print("Cosine Similarity:", round(cosine_similarity, 4))
        print("Euclidean Distance:", round(euclidean_distance, 4))

        cosine_threshold = 0.60
        euclidean_threshold = 23

        if cosine_similarity > cosine_threshold and euclidean_distance < euclidean_threshold:
            print("\n✅ VERIFIED USER - Same Person (High Confidence)")
        else:
            print("\n❌ NOT VERIFIED - Different Person")

    except Exception as e:
        print("Comparison Error:", e)

# ================= MAIN =================

if __name__ == "__main__":

    # Shared flags between main and camera process
    trigger_flag = Value('b', False)   # Main sets this to trigger a capture
    done_flag    = Value('b', False)   # Camera sets this when capture is done
    stop_flag    = Value('b', False)   # Set to True to stop camera entirely

    # Start camera once, runs forever in background
    camera_p = Process(target=continuous_camera, args=(trigger_flag, done_flag, stop_flag))
    camera_p.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print("MEC Final Receiver (Option 2 - Continuous Camera) running...\n")

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            message = data.decode(errors="ignore")

            lines = message.strip().split("\n")
            epcs = lines[1:] if len(lines) > 1 else []

            for epc in epcs:
                print(f"\nEPC RECEIVED: {epc}")

                epc = epc.strip().upper()

                record = query_database(epc)

                if not record:
                    print("❌ EPC NOT FOUND IN DATABASE - Access Denied\n")
                    continue

                print("✅ EPC FOUND IN DATABASE")
                print("ID   :", record["ID"])
                print("NAME :", record["NAME"])
                print("IMAGE:", record["IMAGE"])

                database_image_path = record["IMAGE"]

                if not os.path.exists(database_image_path):
                    print(f"❌ Database image not found at path: {database_image_path}\n")
                    continue

                print("\n📷 Triggering camera capture...")

                # Trigger camera to capture now
                done_flag.value = False
                trigger_flag.value = True

                # Wait until camera signals done
                while not done_flag.value:
                    pass

                # Now compare
                if os.path.exists(CAPTURED_IMAGE_PATH):
                    compare_faces(CAPTURED_IMAGE_PATH, database_image_path)
                else:
                    print("❌ Captured image not found, skipping comparison")

                print("\n" + "=" * 50)
                print("Waiting for next EPC...\n")

    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_flag.value = True
        camera_p.join()
