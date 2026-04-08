# Setup Instructions for V2X-Predict Project

## Prerequisites
- Windows 10/11
- Python 3.8 or higher
- SUMO 1.12 or higher
- NS-3.35 or higher

## Step-by-Step Setup

### 1. Install Python
Download from https://www.python.org/downloads/
Ensure pip is installed.

### 2. Install SUMO
1. Download SUMO from https://sumo.dlr.de/releases/SUMO_1_12_0.msi (or latest)
2. Install and add to PATH
3. Verify: `sumo --version`

### 3. Install NS-3
1. Download NS-3.35 from https://www.nsnam.org/releases/ns-3-35/
2. Extract to a folder, e.g., C:\ns-3.35
3. Build: Open command prompt in ns-3 folder, run `./waf configure --enable-examples`, then `./waf build`
4. Verify: `./waf --run hello-simulator`

### 4. Install Python Dependencies
In the project root:
```
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Add SUMO_HOME and NS3_HOME to environment variables if needed.

### 6. Run the Project
Follow the usage instructions in README.md.

## Troubleshooting
- If SUMO not found, check PATH
- For NS-3 build issues, ensure all dependencies are installed (see NS-3 docs)
- Python import errors: ensure virtual environment or correct Python version