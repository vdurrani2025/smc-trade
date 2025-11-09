# Setup Instructions for Other Systems

## Option 1: Clone Repository (Fresh Setup)

If you're setting up on a new system for the first time:

```bash
# Clone the repository
git clone https://github.com/vdurrani2025/smc-trade.git

# Navigate to the project directory
cd smc-trade

# Checkout the feature/init branch
git checkout feature/init

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Option 2: Pull Latest Changes (Existing Repository)

If you already have the repository cloned:

```bash
# Navigate to the project directory
cd smc-trade

# Fetch latest changes
git fetch origin

# Checkout the feature/init branch (if not already on it)
git checkout feature/init

# Pull latest changes
git pull origin feature/init

# Activate virtual environment (if not already activated)
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Update dependencies (if requirements.txt changed)
pip install -r requirements.txt --upgrade
```

## Option 3: Clone Specific Branch Directly

To clone only the feature/init branch:

```bash
# Clone only the feature/init branch
git clone -b feature/init https://github.com/vdurrani2025/smc-trade.git

# Navigate to the project directory
cd smc-trade

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Application

After setup, run the application:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the Streamlit app
streamlit run smc_trader/main.py

# Or use the run script
python run.py
```

## Troubleshooting

### If MetaTrader5 package fails to install:
The MetaTrader5 package may not be available on all platforms. You can install other dependencies first:

```bash
pip install streamlit pandas numpy plotly python-docx
```

Note: MetaTrader5 is primarily for Windows. On macOS/Linux, you can still use the CSV file upload feature.

### If you need to switch branches:
```bash
# List all branches
git branch -a

# Switch to a different branch
git checkout <branch-name>

# Pull latest from that branch
git pull origin <branch-name>
```

