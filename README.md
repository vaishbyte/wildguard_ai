# WildGuard AI – Wildlife & Illegal Logging Monitoring (Sundarbans)

WildGuard AI is an AI-powered wildlife protection system designed to monitor threats in the Sundarbans. It combines computer vision, audio classification, forest-cover monitoring, virtual sensors, and real-time alerts to support wildlife protection and forest conservation.

## Features and Technology Stack

| Component | Technology |
|---|---|
| Human and animal detection | YOLOv8n (pretrained COCO model) |
| Audio threat detection | YAMNet (Google AudioSet model) |
| Forest-cover monitoring | Global Forest Watch API, UMD/Hansen data, simulated fallback |
| Backend | FastAPI, WebSocket |
| Database | Firebase Firestore Emulator with in-memory fallback |
| Dashboard | React, Vite, Recharts |
| Virtual hardware | Python sensor simulator, ESP32 on Wokwi |
| Mapping | Folium |

**Monitoring area:** Sundarbans National Park, coordinates `21.9497, 88.8958`, radius 25 km. Configure the area in `backend/.env` if supported by your application.

**Pretrained animal classes:** Bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, and giraffe. Detection depends on the classes supported by the model.

## Prerequisites

- Python 3.11
- Node.js 18 or later
- Java JDK 21 for the Firebase Emulator
- Git
- ngrok (optional, for Wokwi connectivity)

## 1. Start Firebase Emulator

Open Terminal 1:

```powershell
npm install -g firebase-tools
cd firebase
firebase emulators:start --project demo-wildguard
```

Open the Emulator UI at http://localhost:4000 and select Firestore to inspect collections.

The demo project does not require Google authentication. Emulator data may reset when the emulator stops, depending on your persistence configuration.

## 2. Start the Backend

Open Terminal 2 from the project root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If PowerShell blocks virtual-environment activation, use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment again.

API documentation: http://localhost:8000/docs

The first run may download the YOLO model and audio-model files. Internet access may be required.

## 3. Start the Dashboard

Open Terminal 3 from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the dashboard at http://localhost:5173.

## 4. Test the Project

| Test | Procedure | Expected result |
|---|---|---|
| Test alert | Click **Send test alert** on the dashboard | A test alert appears |
| Human detection | Stand in front of the webcam | Human detection box and alert |
| Animal detection | Show a supported animal image to the webcam | Animal detection result |
| Audio detection | Play a suitable chainsaw or engine recording near the microphone | Audio classification and alert, if configured |
| Forest monitoring | Inspect the forest-cover panel and map | Forest statistics and map visualization |
| Firestore | Open the Emulator UI | Alert and sensor documents, if writes are configured |

Alerts of the same type may be rate-limited by `ALERT_COOLDOWN_SEC`.

## 5. Run the Virtual Sensor Simulator

Open Terminal 4 from the project root:

```powershell
cd simulator
..\backend\venv\Scripts\Activate.ps1
python sensor_sim.py
```

Example scenarios:

```powershell
python sensor_sim.py --scenario logging
python sensor_sim.py --scenario poaching
```

The configured backend rules may use vibration, sound levels, and PIR motion to generate threat alerts. Check `backend/app/sensors.py` for the actual thresholds.

## 6. Run the ESP32 Simulation on Wokwi

Wokwi runs remotely, so it cannot normally access your computer's `localhost` address. Use ngrok to expose the backend temporarily.

1. Start the backend on port 8000.
2. Open another terminal and run:

   ```powershell
   ngrok http 8000
   ```

3. Copy the HTTPS forwarding URL provided by ngrok.
4. Open [Wokwi](https://wokwi.com/) and create an ESP32 project.
5. Copy the contents of `wokwi/sketch.ino` and `wokwi/diagram.json` into the corresponding Wokwi files.
6. Configure `BACKEND_URL` in the sketch using your ngrok URL and the correct sensor endpoint.
7. Start the simulation and inspect the serial monitor.

**Example circuit connections:**

- PIR OUT → GPIO 27
- Potentiometer 1 signal → GPIO 34
- Potentiometer 2 signal → GPIO 35
- LED → GPIO 2 through a 220 Ω resistor
- Sensor power → 3.3 V where appropriate
- All grounds connected together

Use only the pins and endpoint supported by your actual sketch and circuit configuration.

## 7. Optional: Connect Real Forest-Cover Data

1. Obtain an API key from the [Global Forest Watch Data API](https://data-api.globalforestwatch.org/).
2. Configure `GFW_API_KEY` in `backend/.env`.
3. Restart the backend.
4. If implemented in your application, refresh forest statistics using:

   http://localhost:8000/api/forest?refresh=true

The application may use simulated data when the external service is unavailable. Verify the backend response to determine which data source is active.

## Troubleshooting

| Problem | Possible fix |
|---|---|
| Webcam not detected | Try another `CAMERA_INDEX` in `.env` and close other camera applications |
| Microphone error | Allow desktop applications to access the microphone in Windows settings |
| TensorFlow installation failure | Use the supported Python version and check package compatibility |
| Dashboard cannot reach backend | Verify that the backend is running on port 8000 and check the frontend API URL |
| In-memory storage appears | Verify the Firebase Emulator address and backend configuration |
| Map is empty | Check your internet connection and map tile configuration |
| Wokwi returns HTTP -1 | Verify the ngrok URL, backend endpoint, and network connectivity |

## Project Structure

```text
wildguard-ai/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── db.py
│       ├── events.py
│       ├── sensors.py
│       ├── detection/
│       │   ├── vision.py
│       │   └── audio.py
│       └── geo/
│           ├── forest.py
│           └── map_builder.py
├── frontend/
│   └── src/
├── simulator/
│   └── sensor_sim.py
├── wokwi/
│   ├── sketch.ino
│   └── diagram.json
└── firebase/
```

## Project Goal

WildGuard AI aims to combine AI-based threat detection, environmental monitoring, and real-time alerting to support wildlife protection and reduce illegal logging risks in the Sundarbans.