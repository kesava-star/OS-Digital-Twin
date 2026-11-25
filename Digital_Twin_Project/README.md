# Intelligent Self-Healing OS Digital Twin

A beginner-friendly Streamlit project that monitors this Windows computer, stores historical metrics in SQLite, compares the real system with a digital twin, and uses scikit-learn for anomaly detection and trend analysis.

## What the project includes

- Real-time CPU, RAM, disk, network, disk activity, and process monitoring
- Top CPU and memory processes
- SQLite storage for metrics, recommendations, and system events
- Digital twin synchronization and health states
- Isolation Forest anomaly detection
- Linear-regression trend forecasts
- Low, Medium, and High risk levels
- Safe recommendations with review and verification logging

## Safety

The application **never terminates processes**, closes applications, or changes system settings automatically. It only recommends safe actions for the user to review.

## Easy run method on Windows

1. Install Python 3.10 or newer.
2. During installation, select **Add Python to PATH**.
3. Open the `Digital_Twin_Project` folder in VS Code.
4. Double-click `run_windows.bat`.
5. Wait for the terminal to open Streamlit.
6. Open `http://localhost:8501` if it does not open automatically.

## Manual run method

Open VS Code Terminal in this folder and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Project files

- `app.py` — Streamlit dashboard
- `monitor.py` — real-time psutil monitoring
- `database.py` — SQLite database functions
- `analytics.py` — health, trend, anomaly, risk, and verification logic
- `digital_twin.db` — created automatically on first run
- `run_windows.bat` — easy Windows launcher

## First run

The app begins collecting immediately. Isolation Forest needs at least 10 samples. Linear forecasts improve as more metrics are collected. The project automatically refreshes live metrics by default every 5 seconds.

## Stop the project

Press `Ctrl+C` in the terminal, or close the terminal window.
