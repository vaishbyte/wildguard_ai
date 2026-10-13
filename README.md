# WildGuard AI – Wildlife & Illegal Logging Monitoring (Sundarbans)

| Part | Tech |
|---|---|
| Human / animal detection + species | YOLOv8n (pretrained COCO) on webcam |
| Chainsaw / engine / gunshot sound | YAMNet (Google AudioSet model) on microphone |
| Tree cover loss | Global Forest Watch (UMD/Hansen) API → simulated fallback, statistics with NumPy, map with Folium |
| Backend | FastAPI + WebSocket |
| Database | Firebase Firestore **Local Emulator** (auto-falls back to in-memory if emulator is off) |
| Dashboard | React (Vite) + Recharts |
| Virtual hardware | Python sensor simulator + ESP32 on Wokwi |

Monitoring area: Sundarbans National Park, 21.9497, 88.8958, radius 25 km (change in `backend/.env`).3

Detectable species (pretrained model): bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe.

---

## 0. Install once

- Python 3.11, Node.js 18+
- Java JDK 21 (needed by Firebase Emulator) – https://adoptium.net
- ngrok (only for Wokwi) – https://ngrok.com/download

Run each PowerShell command **one line at a time**.

## 1. Start Firebase Emulator (Terminal 1)

```powershell
npm install -g firebase-tools
```
```powershell
cd wildguard-ai\firebase
```
```powershell
firebase emulators:start --project demo-wildguard
```
Emulator UI: http://localhost:4000 → Firestore tab shows `alerts` and `sensor_nodes`.
(`demo-` project needs no Google login. Data resets when emulator stops.)

## 2. Start backend (Terminal 2)

```powershell
cd wildguard-ai\backend
```
```powershell
python -m venv venv
```
```powershell
.\venv\Scripts\Activate.ps1
```
(If blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again.)
```powershell
pip install -r requirements.txt
```
```powershell
copy .env.example .env
```
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Console should print `Using Firestore Emulator`. First run downloads `yolov8n.pt` and YAMNet (internet needed).
API docs: http://localhost:8000/docs

## 3. Start dashboard (Terminal 3)

```powershell
cd wildguard-ai\frontend
```
```powershell
npm install
```
```powershell
npm run dev
```
Open http://localhost:5173

---

## 4. Test the project

| Test | How | Expected |
|---|---|---|
| Quick check | Click **Send test alert** on dashboard | Red "Chainsaw" alert appears instantly |
| Human detection | Stand in front of webcam | Box on video + orange "Human" alert |
| Species | Show an elephant/zebra/giraffe/bear/cow picture on your phone to the webcam | Species chip + "Animal" alert |
| Chainsaw sound | Play a chainsaw video (YouTube) on phone speaker near the mic | Chainsaw meter rises above 25% → critical alert |
| Engine sound | Play truck/motorbike engine sound | Engine meter + "Engine" alert |
| Tree cover loss | Look at "Tree cover loss" panel and map heatmap | Yearly bars, trend line, anomaly years in red |
| Firestore | Open http://localhost:4000 → Firestore | `alerts` documents being added |

Alerts of the same type repeat only every 10 s (`ALERT_COOLDOWN_SEC`).

## 5. Virtual sensors – Python simulator (Terminal 4)

```powershell
cd wildguard-ai\simulator
```
```powershell
..\backend\venv\Scripts\Activate.ps1
```
```powershell
python sensor_sim.py
```
Scenarios:
```powershell
python sensor_sim.py --scenario logging
```
```powershell
python sensor_sim.py --scenario poaching
```
Rules on backend: vibration ≥ 0.6 **and** sound ≥ 80 dB → chainsaw (critical); sound ≥ 75 dB → loud noise; PIR motion → intrusion.

## 6. Virtual hardware – ESP32 on Wokwi

Wokwi runs in the cloud, so it cannot reach `localhost`. Use ngrok to expose the backend.

1. New terminal:
   ```powershell
   ngrok http 8000
   ```
   Copy the `https://....ngrok-free.app` URL.
2. Go to https://wokwi.com → **New Project → ESP32**.
3. Replace `sketch.ino` with `wokwi/sketch.ino`, and `diagram.json` with `wokwi/diagram.json`.
4. In `sketch.ino` set `BACKEND_URL` to `https://<your-ngrok-url>/api/sensors/reading`.
5. Press ▶ Start. Serial monitor shows readings every 3 s.
6. Interact:
   - Click PIR sensor → "Simulate motion" → intrusion alert
   - Pot 1 = sound level, Pot 2 = tree vibration → turn both to max → chainsaw alert, red LED on
7. Node `wokwi-esp32-1` appears in dashboard table and on the map.

Circuit: PIR OUT→D27, Pot1 SIG→D34, Pot2 SIG→D35, LED→D2 via 220 Ω, all VCC→3V3, GND→GND.

## 7. Real tree cover data (optional)

1. Create a free Global Forest Watch Data API key (docs: https://data-api.globalforestwatch.org).
2. Put it in `backend/.env` → `GFW_API_KEY=...`
3. Restart backend and open http://localhost:8000/api/forest?refresh=true
   Source changes to "Global Forest Watch (UMD/Hansen) - real". If the call fails, it falls back to simulated data and shows the reason.
   Note: spatial hotspots on the map are always simulated.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Camera "not found" | Set `CAMERA_INDEX=1` (or 2) in `.env`, close other apps using webcam |
| Microphone error | Windows Settings → Privacy → Microphone → allow desktop apps |
| TensorFlow install fails | Use Python 3.11 exactly; or set `ENABLE_MIC=0` to run without audio |
| Dashboard says backend not reachable | Backend must run on port 8000, or edit `frontend/.env` (`VITE_API_URL`) |
| Store shows "Memory store" | Firebase Emulator not running on 127.0.0.1:8080 – start it before backend |
| Map empty | Needs internet (map tiles & Leaflet load from CDN) |
| Wokwi HTTP -1 | ngrok not running or wrong URL in sketch |

## Project structure

```
wildguard-ai/
├── backend/app/
│   ├── main.py              FastAPI routes, WebSocket, video stream
│   ├── config.py / db.py    settings, Firestore emulator / memory store
│   ├── events.py            alert creation, cooldown, broadcast
│   ├── sensors.py           field sensor rules
│   ├── detection/vision.py  YOLOv8 human + species
│   ├── detection/audio.py   YAMNet chainsaw / engine / gunshot
│   └── geo/forest.py, map_builder.py   tree cover loss stats + Folium map
├── frontend/src/            React dashboard
├── simulator/sensor_sim.py  virtual sensor nodes
├── wokwi/                   ESP32 sketch + circuit
└── firebase/                emulator config
```
