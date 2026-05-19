# Edge AI RFID Authentication System

Private 5G and MEC-based RFID + Face Verification Authentication System using Edge AI and UDP communication.

---

## Overview

This project demonstrates an end-to-end distributed authentication pipeline integrating:

- UHF RFID sensing
- Edge AI facial verification
- UDP-based real-time communication
- MEC (Multi-access Edge Computing) concepts
- Private 5G-oriented architecture

The system was designed to explore low-latency authentication workflows suitable for industrial and smart infrastructure deployments.

---

## System Architecture

RFID Reader → Edge Device (Khadas VIM3) → Face Verification Engine → MEC Server → Authentication Decision

---

## Key Features

- Real-time RFID identity acquisition
- Face verification using Edge AI inference
- UDP-based lightweight transport layer
- Low-latency authentication workflow
- Modular MEC-compatible pipeline
- Edge-device compute offloading
- Multi-factor authentication logic

---

## Technologies Used

### Hardware
- Khadas VIM3
- UHF RFID Reader

### Software & Frameworks
- Python
- OpenCV
- FaceNet
- UDP/IP Communication
- Edge AI Inference

### Concepts
- MEC (Multi-access Edge Computing)
- Private 5G Architecture
- Distributed Edge Systems
- Real-Time Authentication

---

## Workflow

1. RFID tag is scanned using UHF RFID reader.
2. Identity event is transmitted to edge node.
3. Facial embedding extraction is performed on-device.
4. Authentication payload is transmitted using UDP.
5. MEC server validates RFID + facial verification results.
6. Final authentication decision is generated.

---

## Performance Highlights

- Sub-100 ms authentication latency
- Reduced cloud dependency using edge inference
- Lightweight communication pipeline using UDP
- Designed for scalable edge-node aggregation

---

## Future Improvements

- FPGA acceleration for inference pipeline
- Secure encrypted communication layer
- Real-time dashboard monitoring
- Multi-user edge authentication
- Integration with actual 5G testbed

---

## Author

E. Velavasrikanth  
ECE Engineer | FPGA | Edge AI | Embedded Systems | MEC Architecture
