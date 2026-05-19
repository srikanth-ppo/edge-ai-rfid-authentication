import socket
import time
import os

CSV_FILE = r"C:\Users\Darre\Documents\RFID_Tags_Test.csv"

UDP_IP = "192.168.10.12"
UDP_PORT = 5005

COOLDOWN = 3
last_seen = {}
file_position = 0


def should_process(epc):
    current_time = time.time()

    if epc not in last_seen:
        last_seen[epc] = current_time
        return True

    if current_time - last_seen[epc] > COOLDOWN:
        last_seen[epc] = current_time
        return True

    return False


print("Starting real-time CSV monitor...\n")

while True:
    try:
        if not os.path.exists(CSV_FILE):
            print("CSV file not found...")
            time.sleep(2)
            continue

        with open(CSV_FILE, "r", encoding="utf-8") as file:
            file.seek(file_position)  # move to last read position
            lines = file.readlines()
            file_position = file.tell()  # update position

        epcs_to_send = []

        for line in lines:
            if "E2" in line:  # crude EPC filter
                parts = line.split(",")
                if len(parts) > 1:
                    epc = parts[1].strip()

                    if should_process(epc):
                        epcs_to_send.append(epc)

        if epcs_to_send:
            message = "RFID_TAG_EVENT\n" + "\n".join(epcs_to_send)

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(message.encode(), (UDP_IP, UDP_PORT))

            print("Sent to MEC:")
            print(message)
            print("-" * 40)

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
