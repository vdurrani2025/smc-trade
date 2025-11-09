# MT5 Credentials Setup Guide

## Where to Enter MT5 Credentials

You have **two options** to enter your MT5 credentials:

---

## Option 1: Streamlit UI (Recommended - Easiest)

### Steps:

1. **Run the Streamlit app:**
   ```bash
   streamlit run smc_trader/main.py
   ```

2. **Open the sidebar** (left side of the browser)

3. **Find "MT5 Connection" section** in the sidebar

4. **Enter your credentials:**
   - **MT5 Login**: Your account number (e.g., `12345678`)
   - **MT5 Password**: Your account password (hidden input)
   - **MT5 Server**: Your broker's server name
     - Examples:
       - `MetaQuotes-Demo` (for demo accounts)
       - `ICMarkets-Demo` (IC Markets demo)
       - `ICMarkets-Live` (IC Markets live)
       - `FXOpen-Demo` (FXOpen demo)
       - Check your MT5 terminal: Tools → Options → Server tab
   - **MT5 Path** (Optional): Leave empty if MT5 is in default location
     - Windows default: `C:\Program Files\MetaTrader 5\terminal64.exe`
     - Only needed if MT5 is installed in a custom location

5. **Click "Connect to MT5"** button

6. **Status**: You'll see "✅ Connected" if successful, or an error message if credentials are wrong

---

## Option 2: Pre-fill in config.json

### Steps:

1. **Open** `smc_trader/config.json`

2. **Edit the MT5 section:**
   ```json
   {
     "mt5": {
       "login": 12345678,
       "password": "your_password_here",
       "server": "MetaQuotes-Demo",
       "path": ""
     }
   }
   ```

3. **Save the file**

4. **Run the app** - credentials will be pre-filled in the UI

5. **Click "Connect to MT5"** to connect

---

## How to Find Your MT5 Server Name

### Method 1: From MT5 Terminal
1. Open MetaTrader 5
2. Go to **Tools → Options**
3. Click **Server** tab
4. Your server name is displayed there

### Method 2: From Account History
1. Open MT5
2. Go to **View → Toolbox** (or press Ctrl+T)
3. Click **History** tab
4. Right-click on your account → **Properties**
5. Server name is shown there

### Method 3: Common Server Names

**Demo Accounts:**
- `MetaQuotes-Demo`
- `ICMarkets-Demo`
- `FXOpen-Demo`
- `XMGlobal-Demo`
- `Exness-Demo`

**Live Accounts:**
- `ICMarkets-Live`
- `FXOpen-Live`
- `XMGlobal-Live`
- `Exness-Live`

**Note**: Server names are case-sensitive and broker-specific. Always verify with your broker.

---

## Example Configuration

### Demo Account Example:
```json
{
  "mt5": {
    "login": 12345678,
    "password": "MySecurePassword123",
    "server": "MetaQuotes-Demo",
    "path": ""
  }
}
```

### Live Account Example:
```json
{
  "mt5": {
    "login": 87654321,
    "password": "MySecurePassword123",
    "server": "ICMarkets-Live",
    "path": ""
  }
}
```

---

## Troubleshooting

### ❌ "MT5 initialization failed"
- **Solution**: Make sure MetaTrader 5 is installed on your system
- **Windows**: Install MT5 from broker's website
- **macOS/Linux**: MT5 may not be available. Use CSV file upload instead.

### ❌ "MT5 login failed"
- **Solution**: Check your credentials:
  - Account number is correct
  - Password is correct (case-sensitive)
  - Server name matches exactly (case-sensitive)
  - Account is active (not expired for demo accounts)

### ❌ "Failed to get account info"
- **Solution**: 
  - Verify MT5 terminal is running
  - Check internet connection
  - Ensure account has trading permissions enabled

### ❌ Server name not found
- **Solution**: 
  - Contact your broker for the correct server name
  - Check MT5 terminal settings
  - Verify you're using the right server (demo vs live)

---

## Security Notes

⚠️ **Important Security Tips:**

1. **Never commit credentials to git** - `config.json` is in `.gitignore` for this reason
2. **Use demo account first** - Test with demo account before using live credentials
3. **Password is hidden** - UI uses password input type (masked)
4. **Credentials stored in session** - Not persisted unless you save config.json manually

---

## Alternative: CSV Mode (No MT5 Required)

If you don't have MT5 or want to test without connecting:

1. **Select "CSV File"** as data source in the sidebar
2. **Upload a CSV file** with 5-minute OHLCV data
3. **Analyze patterns** without live trading

This mode works on any system (Windows, macOS, Linux) and doesn't require MT5 installation.

