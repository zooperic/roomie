# ROOMIE Hardware Integration Checklist

**Phase:** 4 (Planned)  
**Status:** 📋 Not Started  
**Last Updated:** April 26, 2026

---

## Overview

Phase 4 will add physical sensors and cameras for automatic inventory tracking without manual photo uploads.

---

## Hardware Shopping List

### Core Components

| Item | Specs | Est. Cost (₹) | Link/Notes |
|------|-------|--------------|------------|
| Raspberry Pi 4 | 4GB RAM minimum, 8GB recommended | 4,500 | Official store |
| Pi Camera Module V2 | 8MP, 1080p30 | 2,200 | Official camera |
| MicroSD Card | 64GB Class 10 | 600 | SanDisk/Samsung |
| Power Supply | 5V 3A USB-C | 800 | Official adapter |
| Case | With camera mount | 400 | Optional but recommended |

**Core Total: ~₹8,500**

---

### Sensors (Optional Upgrades)

| Item | Purpose | Est. Cost (₹) | Priority |
|------|---------|--------------|----------|
| Load Cells (x4) | Weight sensing | 1,200 | Medium |
| HX711 ADC | Weight sensor interface | 200 | Medium |
| Magnetic Door Sensor | Fridge open detection | 150 | High |
| DHT22 | Temperature/humidity | 300 | Low |
| PIR Motion Sensor | Presence detection | 200 | Low |
| LED Strip (optional) | Better lighting | 500 | Low |

**Sensors Total: ~₹2,550**

---

### Accessories

| Item | Purpose | Est. Cost (₹) |
|------|---------|--------------|
| Breadboard | Prototyping | 100 |
| Jumper Wires | Connections | 100 |
| Mounting Tape | Camera positioning | 100 |
| Cable Ties | Cable management | 50 |
| USB Extension | Power routing | 150 |

**Accessories Total: ~₹500**

---

## **Grand Total: ~₹11,550**

(Core + Sensors + Accessories)

---

## Installation Steps

### 1. Raspberry Pi Setup

```bash
# 1. Flash Raspberry Pi OS
# Use Raspberry Pi Imager
# Choose: Raspberry Pi OS Lite (64-bit)

# 2. Enable camera
sudo raspi-config
# Interface Options → Camera → Enable

# 3. Install dependencies
sudo apt update
sudo apt install python3-pip python3-picamera2
pip3 install picamera2 opencv-python

# 4. Test camera
libcamera-hello
# Should show camera preview
```

---

### 2. Camera Positioning

**Recommended Setup:**
```
┌─────────────────────────────────────┐
│         Fridge Interior              │
│                                      │
│  ┌──────────┐   ← Camera here       │
│  │  Camera  │   (top center)         │
│  └──────────┘                        │
│       ↓                              │
│  Captures full view                  │
│  of all shelves                      │
│                                      │
│  Shelf 1: ████████                   │
│  Shelf 2: ████████                   │
│  Shelf 3: ████████                   │
│                                      │
└─────────────────────────────────────┘
```

**Mounting:**
- Use adhesive mount or magnetic base
- Angle slightly downward (15-20°)
- Ensure LED/light doesn't reflect
- Cable management important

---

### 3. Door Sensor Wiring

```python
# Door sensor on GPIO 17
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def door_opened(channel):
    # Trigger camera
    capture_photo()

GPIO.add_event_detect(17, GPIO.FALLING, callback=door_opened, bouncetime=200)
```

---

### 4. Weight Sensors (Optional)

```python
# HX711 library
from hx711 import HX711

# Initialize
hx = HX711(dout_pin=5, pd_sck_pin=6)
hx.set_scale_ratio(scale_ratio=92)  # Calibrate this
hx.reset()
hx.tare()

# Read weight
weight = hx.get_weight_mean(20)
print(f"Weight: {weight}g")
```

**Calibration:**
1. Place known weight (e.g., 500g)
2. Adjust scale_ratio until accurate
3. Save calibration value

---

### 5. Software Integration

**New Components:**

```python
# interfaces/raspberry_pi/camera_capture.py
import picamera2
import requests

class FridgeCamera:
    def __init__(self):
        self.camera = picamera2.Picamera2()
        
    def capture_on_door_open(self):
        # Take photo
        image = self.camera.capture_array()
        
        # Send to Iris
        response = requests.post(
            "http://localhost:8000/message",
            json={
                "message": "scan fridge and add items",
                "user_id": "raspberry-pi",
                "force_agent": "iris",
                "image_data": base64_encode(image)
            }
        )
        
        return response.json()
```

---

### 6. MQTT Integration (Optional)

```bash
# Install Mosquitto
sudo apt install mosquitto mosquitto-clients

# Python MQTT client
pip3 install paho-mqtt
```

```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1883)

# Publish events
client.publish("roomie/fridge/door", "opened")
client.publish("roomie/fridge/weight", str(weight))
```

---

## Wiring Diagrams

### Door Sensor
```
Raspberry Pi          Magnetic Sensor
GPIO 17 ────────────── Signal
GND ───────────────── GND
```

### Load Cell (HX711)
```
Raspberry Pi          HX711          Load Cell
GPIO 5 ─────────────  DT
GPIO 6 ─────────────  SCK
5V ──────────────────  VCC
GND ─────────────────  GND ─────────  Black
                       E+ ──────────  Red
                       E- ──────────  White
                       A- ──────────  Green
                       A+ ──────────  Blue
```

---

## Testing Procedures

### Camera Test
```bash
# Capture test image
libcamera-jpeg -o test.jpg

# Check quality
# Should clearly show items on shelves
```

### Door Sensor Test
```python
# Run listener
python3 test_door_sensor.py

# Open fridge
# Should print: "Door opened!"
```

### Weight Sensor Test
```python
# Run weight test
python3 test_weight.py

# Place 500g weight
# Should read: ~500g (±10g)
```

---

## Power Management

### Option 1: USB Power
```
Fridge → USB Power Bank → Pi
Pros: Simple, portable
Cons: Need to recharge
```

### Option 2: Wall Power
```
Nearby Outlet → USB Adapter → Pi
Pros: Continuous power
Cons: Need outlet access
```

### Option 3: Fridge Internal (Advanced)
```
Fridge 12V → Buck Converter → 5V USB → Pi
Pros: Always powered with fridge
Cons: Complex, warranty concerns
```

**Recommended:** Option 2 (Wall Power)

---

## Safety Considerations

### Electrical Safety
- ⚠️ Never splice into fridge power without expertise
- ✅ Use certified USB power supplies
- ✅ Keep wiring away from cooling elements
- ✅ Use proper insulation on all connections

### Food Safety
- ✅ Use food-safe materials for mounting
- ✅ Ensure camera doesn't block airflow
- ✅ Don't drill into fridge walls
- ✅ Keep sensors away from food contact

### Data Safety
- ✅ Secure WiFi connection
- ✅ Encrypt camera feed
- ✅ No cloud storage of photos (GDPR/privacy)

---

## Expected Workflow (Phase 4)

### Automatic Capture
```
1. User opens fridge door
2. Magnetic sensor triggers Pi
3. Camera captures photo
4. Photo sent to Iris agent
5. Items detected automatically
6. Inventory updated
7. No user action needed!
```

### Weight Tracking
```
1. Item placed on shelf
2. Weight sensor reads change
3. Calculate item weight
4. Match with known items
5. Update quantity
6. Low stock alert if needed
```

---

## Maintenance

### Weekly
- [ ] Clean camera lens
- [ ] Check door sensor alignment
- [ ] Verify power supply

### Monthly
- [ ] Recalibrate weight sensors
- [ ] Check all wire connections
- [ ] Update Raspberry Pi OS
- [ ] Backup configuration

### Quarterly
- [ ] Full system test
- [ ] Review sensor accuracy
- [ ] Check for condensation/moisture
- [ ] Replace worn components

---

## Troubleshooting

### Camera not working
```bash
# Check camera detected
vcgencmd get_camera
# Should show: supported=1 detected=1

# Test capture
libcamera-hello -t 0

# If fails, check:
- Cable connection
- Camera enabled in raspi-config
- Pi powered properly
```

### Door sensor not triggering
```bash
# Test GPIO
gpio readall

# Check wiring
# Sensor should show closed/open states

# Add debug logging
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
print(GPIO.input(17))  # Should change on door open/close
```

### Weight sensor inaccurate
```python
# Recalibrate
# 1. Remove all weight (tare)
hx.reset()
hx.tare()

# 2. Place known weight
# 3. Adjust scale ratio
```

---

## Phase 4 Timeline (Estimated)

**Week 1:** Hardware procurement  
**Week 2:** Pi setup, camera mounting  
**Week 3:** Sensor installation, testing  
**Week 4:** Software integration  
**Week 5:** Calibration, fine-tuning  
**Week 6:** Live testing, monitoring

**Total:** ~6 weeks from start to production

---

## Cost Breakdown by Feature

| Feature | Hardware Cost | Complexity | Value |
|---------|--------------|------------|-------|
| Auto-capture on door open | ₹7,650 | Medium | High |
| Weight tracking | ₹1,400 | High | Medium |
| Temperature monitoring | ₹300 | Low | Low |

**Recommended:** Start with auto-capture only.

---

## Future Enhancements (Phase 5+)

- Multiple cameras (shelves, door, freezer)
- Barcode scanner integration
- RFID tags for item tracking
- Voice commands ("Hey Alfred, scan my fridge")
- Smart fridge light integration
- Energy usage monitoring

---

**Status:** Hardware not yet purchased  
**Next Step:** Order Raspberry Pi 4 kit  
**Estimated Start:** After Phase 3 testing complete

**Last Updated:** April 26, 2026
