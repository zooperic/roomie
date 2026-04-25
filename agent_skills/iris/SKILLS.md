# Iris — Skills & Knowledge Base

> Iris controls smart home devices — lights, fans, AC, smart plugs. She bridges Alfred to your physical home environment.

**Status: Phase 4 — Not yet implemented. Requires smart home hardware.**

---

## Identity

- **Name**: Iris
- **Domain**: Smart home device control and automation
- **Persona**: Responsive and precise. Executes what you ask, confirms what she can't reverse.

---

## Prerequisite Hardware

Iris is useless without at least one of the following:

| Hardware | Cost | What it enables |
|---------|------|----------------|
| Smart plugs (TP-Link Tapo, Sonoff) | ₹800–1,500/plug | Control any plugged device: fan, lamp, charger |
| Smart bulbs (Philips Wiz, Syska) | ₹500–1,200/bulb | Lights on/off, brightness, colour temp |
| AC IR blaster (Switchbot, Broadlink) | ₹2,000–3,500 | Control AC, TV via infrared — works with any brand |
| Raspberry Pi as local hub | ₹4,500 | Run Home Assistant locally, Iris integrates via its API |

**Recommended entry point:** One Sonoff smart plug + Sonoff S31 power monitoring plug (tells Iris how much power a device is drawing). That alone unlocks basic control + energy monitoring.

---

## Planned Skills

### 1. `control_device`
Turn a device on or off, or set a specific state.

**Triggers:** "turn off the fan", "switch on the lamp", "turn AC to 24 degrees", "lights off"

**Requires confirmation for:** Devices that were manually set (Iris won't override a state you set in the last 5 minutes without asking).

**Does not require confirmation for:** Simple on/off commands with clear intent.

---

### 2. `device_status`
Report the current state of a device or all devices.

**Triggers:** "is the AC on", "what devices are on", "home status", "what's running right now"

---

### 3. `scene`
Activate a predefined scene (a group of device states).

**Triggers:** "movie mode", "sleep mode", "morning routine", "I'm leaving"

**Scenes are user-defined** — you tell Iris what "sleep mode" means (AC at 22, lights off, fan on). She stores it and executes on command.

---

### 4. `energy_report`
Report energy consumption for a device or all smart plugs.

**Triggers:** "how much power is the AC using", "energy report", "what's drawing the most power"

**Requires:** Smart plugs with power monitoring (e.g., Sonoff S31, TP-Link Tapo P115).

---

### 5. `schedule`
Set a timed action for a device.

**Triggers:** "turn off the AC in 2 hours", "switch on the lamp at 6pm", "turn off everything at midnight"

**Note:** Schedules stored in DB. Iris checks on a cron loop, not sleep/wake. Alfred triggers Iris on schedule events.

---

## Integration Options (in order of preference)

| Option | Complexity | Cost | Notes |
|--------|-----------|------|-------|
| **Home Assistant (local)** | Medium | Free (self-hosted) | Best long-term option. Runs on Pi. Iris calls its REST API. Supports 1000+ device types. |
| **Tuya API** | Low | Free tier | Works with most cheap smart plugs sold in India. Cloud-dependent. |
| **Sonoff eWeLink API** | Low | Free | Sonoff-specific. Stable, well-documented. |
| **MQTT direct** | High | Free | For DIY hardware. Maximum control, maximum work. |

Recommendation: Start with Home Assistant on a Raspberry Pi. It abstracts device brands — Iris talks to one API regardless of whether you have TP-Link, Sonoff, or Philips hardware.

---

## What Iris Does NOT Do

- Iris does not make autonomous decisions about device states (e.g., turn off AC when you leave). That's a scene or schedule you set.
- Iris does not monitor your presence or location (Phase 4 consideration, not default).
- Iris does not control devices without at least one of the listed hardware options.

---

## Relationship with Alfred

Alfred routes "home control" intent to Iris. Iris handles it. A typical flow:

```
You (Telegram): "turn off everything, I'm going to sleep"
Alfred → routes to Iris (scene, "sleep")
Iris → executes scene: AC to 24, fan on, lights off
Iris → returns: "Sleep mode activated. AC at 24°, fan on, lights off."
Alfred → relays to Telegram
```

For irreversible or ambiguous commands ("turn off everything"), Iris sets `requires_confirmation: true` and Alfred presents a confirm button before acting.
