# eudis-2025
# SKYGUARD C2 – Target Deconfliction

A real-time air defense simulation built with **Pygame**.  
You command an automated defense system where **cameras** detect intrusions and **interceptor drones** autonomously investigate and neutralize enemy drones before they cross the national border.

---

## 🎯 Features

- **Autonomous Drone AI** — Interceptors patrol, investigate, engage, and return to base automatically.  
- **Dynamic Threat Spawning** — Enemy drones appear at random intervals and paths.  
- **Camera Surveillance Network** — Multiple cameras detect intrusions and trigger alerts.  
- **Task Assignment System** — Drones pick up queued investigation tasks from cameras.  
- **Real-Time Visualization** — See detection ranges, fields of view (FOV), lock-ons, and alerts.  
- **HUD Display** — Live info on border breaches, threats, drone availability, and task queue.

---

## 🧠 How It Works

1. **Cameras** monitor the upper zone of the map (above the yellow border).  
   When an enemy drone enters their detection range, they raise an alert.  

2. **Interceptors** automatically:
   - Receive investigation tasks from the task queue.
   - Travel to the alert location.
   - Search the area in a patrol pattern.
   - Lock onto and neutralize detected enemies.
   - Return to base when idle.

3. **Enemy Drones** spawn at random points and attempt to cross the border.  
   Each successful breach increases the counter shown in the HUD.

---

## 🕹️ Controls

| Action | Key / Input |
|--------|--------------|
| Quit game | **Close window** or **Alt+F4** |

No manual control is required — all drones operate autonomously.

---

## ⚙️ Installation

### Requirements
- Python 3.9+
- Pygame 2.0+

### Installation Steps
```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

# 2. Install dependencies
pip install pygame

# 3. Run the simulation
python main.py
```
