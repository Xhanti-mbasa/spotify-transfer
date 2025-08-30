#  Spotify Transfer Tool

A powerful Python tool to transfer liked songs and playlists between Spotify accounts with a user-friendly interface and robust error handling.

##  Features

- **🎵 Liked Songs Transfer** - Transfer all your liked songs between accounts
- **🎶 Playlist Transfer** - Copy entire playlists with all tracks
- **🔄 Bidirectional Transfer** - Choose direction or merge both ways
- **📊 Account Verification** - View account info before transferring
- **📈 Progress Tracking** - Real-time progress bars and detailed status
- **🔒 Secure OAuth** - Automatic browser-based authentication
- **📝 Transfer Logging** - Complete history of all transfers
- **⚠️ Error Recovery** - Detailed error reporting and retry logic

## Quick Start

### Prerequisites

- Python 3.7+
- Two Spotify Developer Apps (one for each account)
- Spotify Premium (recommended for best experience)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/spotify-transfer-tool.git
cd spotify-transfer-tool
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Spotify Apps

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create **two separate apps** (one for each account you want to transfer between)
3. For each app:
   - Click "Edit Settings"
   - Add redirect URI: `http://127.0.0.1:8888/callback`
   - Save settings
   - Note down the Client ID and Client Secret

### 4. Configure Environment

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your Spotify app credentials:
   ```bash
   # Account 1 (Source Account)
   SPOTIFY_ACCOUNT1_CLIENT_ID=your_first_app_client_id
   SPOTIFY_ACCOUNT1_CLIENT_SECRET=your_first_app_client_secret
   
   # Account 2 (Destination Account)
   SPOTIFY_ACCOUNT2_CLIENT_ID=your_second_app_client_id
   SPOTIFY_ACCOUNT2_CLIENT_SECRET=your_second_app_client_secret
   ```

### 5. Run the Tool

```bash
python main.py
```

## 📖 Usage Guide

### Step-by-Step Process

1. **Account Authorization**
   - The tool will open your browser for each account
   - Log in to Account 1 when prompted
   - Switch browser sessions and log in to Account 2

2. **Account Verification**
   - View account details, liked songs count, and playlists
   - Confirm you're transferring between the correct accounts

3. **Transfer Configuration**
   - Choose transfer direction:
     - Account 1 → Account 2
     - Account 2 → Account 1  
     - Both directions
