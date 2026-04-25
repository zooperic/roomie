# 🛒 Hardware Checklist — Project Roomy

> Buy nothing until Phase 3. Phase 1 and 2 are fully software. This list is for when you're ready to add physical hardware.

---

## Elsa — Fridge Camera Unit

### The problem with fridges
- Internal temperature: 2–5°C
- Humidity: high (condensation likely)
- **LiPo batteries perform poorly below 5°C** — capacity drops 20–30%, and they can fail permanently if discharged in cold. Don't put your battery inside the fridge.
- Power cables can be routed through the door seal — fridge seals are flexible and a thin USB cable won't break the seal enough to affect temperature meaningfully.

### Recommended Option (Cheapest viable)

| Item | Estimated Price | Notes |
|------|----------------|-------|
| **ESP32-CAM** (AI-Thinker module) | ₹300–400 | Has built-in camera + WiFi. Mount inside fridge facing shelves. |
| **USB-C cable (thin, flat)** | ₹150 | Route through door seal to power source outside |
| **5V USB power adapter** | ₹200 | Stays outside fridge. Powers ESP32-CAM. |
| **Small acrylic mount / bracket** | ₹100 | Stick to fridge inner wall with 3M tape |
| **Total** | **~₹750–900** | |

### Why not Raspberry Pi for the camera?
- Pi Zero 2W costs ~₹1500+, is overkill for just capturing images
- ESP32-CAM is purpose-built for camera + WiFi and uses 10x less power
- Pi makes more sense as a central hub (see future hub section below)

### Alternative: Old Android Phone
- If you have a spare Android phone lying around: use it
- Install an IP camera app (e.g., DroidCam, Alfred)
- Endpoint returns JPEG — Elsa can poll it directly
- **No purchase needed**. Free if you have a spare phone.
- Downside: needs charging every 1–2 days (can be solved with a charging cable through the seal)

---

## Future: Central Hub (Phase 3+)

When you have multiple agents needing local compute (Remy, future agents):

| Item | Estimated Price | Notes |
|------|----------------|-------|
| **Raspberry Pi 4 (2GB)** | ₹4,000–5,500 | Runs Ollama locally, MQTT broker, local DB |
| **32GB microSD** | ₹400 | Boot drive |
| **Pi case with fan** | ₹400 | Passive cooling is not enough for sustained LLM |
| **5V 3A power supply** | ₹350 | Official Pi PSU to avoid undervolt issues |
| **Total** | **~₹5,500–6,500** | |

**Why Pi 4 over Pi 5?**
Pi 5 costs significantly more. For hosting Ollama with small models (Phi-3, Llama 3.2 3B), Pi 4 2GB is sufficient. Upgrade if you want to run 7B+ models locally.

---

## Remy — Pantry/Kitchen Counter

### Options

| Approach | Hardware | Cost | Notes |
|---------|---------|------|-------|
| Camera-based (like Elsa) | ESP32-CAM | ₹750 | Mount above pantry shelf |
| Weight sensor | Load cell + HX711 + ESP32 | ₹600 | More precise for bulk items (rice, dal) |
| Barcode scanner | Any USB barcode scanner | ₹800–1,500 | Manual scan when adding items. Low maintenance. |

**Recommended for Phase 2:** Start with manual input (software only, no hardware). Add weight sensor later if you want it to be passive.

---

## MQTT Broker (For hardware communication)

When you add hardware, you need a message broker so devices can publish events to your backend.

| Option | Cost | Notes |
|--------|------|-------|
| **Mosquitto on your laptop** | Free | Fine for dev/local use |
| **Mosquitto on Raspberry Pi** | Free | Better for always-on |
| **HiveMQ Cloud (free tier)** | Free | Up to 100 connections. Good for early prod. |

---

## What NOT to buy (yet)

- ❌ Any cloud-connected smart fridge / IoT appliance — overpriced, locked ecosystems
- ❌ Dedicated NAS for storage — SQLite on your laptop is fine until Phase 4
- ❌ Raspberry Pi 5 — cost not justified for this workload in Phase 3
- ❌ Any camera with its own AI chip (like Google Coral) — the LLM inference happens on your server, not the camera

---

## Phase 1 Hardware Requirements

**None.** Everything in Phase 1 is software. You manually tell Elsa what's in your fridge. That's intentional — get the software right before adding hardware complexity.
