import requests
import base64
import json
import webbrowser
import urllib.parse
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
from tqdm import tqdm
import threading
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === ACCOUNT CONFIGURATIONS ===
ACCOUNT_1 = {
    "name": "Account 1",
    "client_id": os.getenv("SPOTIFY_ACCOUNT1_CLIENT_ID"),
    "client_secret": os.getenv("SPOTIFY_ACCOUNT1_CLIENT_SECRET"),
    "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
    "scope": "user-library-read user-library-modify playlist-read-private playlist-modify-private playlist-modify-public user-read-private"
}

ACCOUNT_2 = {
    "name": "Account 2",
    "client_id": os.getenv("SPOTIFY_ACCOUNT2_CLIENT_ID"),
    "client_secret": os.getenv("SPOTIFY_ACCOUNT2_CLIENT_SECRET"),
    "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
    "scope": "user-library-read user-library-modify playlist-read-private playlist-modify-private playlist-modify-public user-read-private"
}

TOKEN_FILE = "spotify_tokens.json"
TRANSFER_LOG = "transfer_history.json"


def validate_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        "SPOTIFY_ACCOUNT1_CLIENT_ID",
        "SPOTIFY_ACCOUNT1_CLIENT_SECRET",
        "SPOTIFY_ACCOUNT2_CLIENT_ID",
        "SPOTIFY_ACCOUNT2_CLIENT_SECRET"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file and ensure all variables are set.")
        print("   See README.md for setup instructions.")
        return False

    return True


# ------------------- OAuth Handler -------------------
class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
                <head><title>Authorization Successful</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2 style="color: #1DB954;">Authorization Successful!</h2>
                    <p>You can close this tab and return to the application.</p>
                    <div style="background: #f0f0f0; padding: 20px; margin: 20px; border-radius: 10px;">
                        <p>Your Spotify account has been connected successfully!</p>
                    </div>
                </body>
            </html>
            """.encode('utf-8'))
        elif "error" in params:
            self.server.auth_code = None
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error = params.get("error", ["unknown"])[0]
            self.wfile.write(f"""
            <html>
                <head><title>Authorization Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2 style="color: #e22134;">Authorization Failed</h2>
                    <p>Error: {error}</p>
                    <p>Please close this tab and try again.</p>
                </body>
            </html>
            """.encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
                <head><title>Invalid Request</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2 style="color: #e22134;">Invalid Request</h2>
                    <p>No authorization code found.</p>
                </body>
            </html>
            """.encode('utf-8'))

    def log_message(self, format, *args):
        pass  # Suppress server logs


def get_auth_code_automatically(auth_url, port=8888, timeout=300):
    print(f"Opening authorization URL in your browser...")
    print(f"   If it doesn't open automatically, copy this URL:")
    print(f"   {auth_url}\n")

    server = HTTPServer(("127.0.0.1", port), OAuthHandler)
    server.auth_code = None
    server.timeout = 1

    try:
        webbrowser.open(auth_url)
    except Exception as e:
        print(f"Could not open browser: {e}")
        print("   Please open the URL manually.")

    print(f"Waiting for authorization (timeout: {timeout // 60} minutes)...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        server.handle_request()
        if hasattr(server, 'auth_code') and server.auth_code is not None:
            return server.auth_code
        time.sleep(0.1)

    print("Authorization timeout")
    return None


# ------------------- Helper Functions -------------------
def get_auth_url(account_config):
    params = {
        "client_id": account_config["client_id"],
        "response_type": "code",
        "redirect_uri": account_config["redirect_uri"],
        "scope": account_config["scope"],
        "show_dialog": "true"
    }
    return "https://accounts.spotify.com/authorize?" + urlencode(params)


def get_token(account_config, code):
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(
            f"{account_config['client_id']}:{account_config['client_secret']}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": account_config["redirect_uri"]
    }

    res = requests.post(url, data=data, headers=headers)
    if res.status_code != 200:
        print(f"Token request failed: {res.status_code}")
        print(f"   Response: {res.text}")

    res.raise_for_status()
    return res.json()


def refresh_token(account_config, refresh_token_val):
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(
            f"{account_config['client_id']}:{account_config['client_secret']}".encode()).decode()
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_val
    }
    res = requests.post(url, data=data, headers=headers)
    res.raise_for_status()
    return res.json()["access_token"]


def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def load_tokens():
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_transfer_log(log_entry):
    try:
        with open(TRANSFER_LOG, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    log_entry["timestamp"] = datetime.now().isoformat()
    history.append(log_entry)

    with open(TRANSFER_LOG, "w") as f:
        json.dump(history, f, indent=2)


# ------------------- Spotify API Functions -------------------
def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get("https://api.spotify.com/v1/me", headers=headers)
    res.raise_for_status()
    return res.json()


def get_liked_tracks(access_token):
    url = "https://api.spotify.com/v1/me/tracks?limit=50"
    headers = {"Authorization": f"Bearer {access_token}"}
    tracks = []

    while url:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()
        tracks.extend([{
            "id": item["track"]["id"],
            "name": item["track"]["name"],
            "artist": ", ".join([artist["name"] for artist in item["track"]["artists"]]),
            "added_at": item["added_at"]
        } for item in data.get("items", []) if item.get("track") and item["track"].get("id")])
        url = data.get("next")

    return tracks


def get_playlists(access_token):
    url = "https://api.spotify.com/v1/me/playlists?limit=50"
    headers = {"Authorization": f"Bearer {access_token}"}
    playlists = []
    user_id = get_user_info(access_token)['id']

    while url:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()

        for playlist in data.get("items", []):
            if playlist["owner"]["id"] == user_id:  # Only user-owned playlists
                playlists.append({
                    "id": playlist["id"],
                    "name": playlist["name"],
                    "track_count": playlist["tracks"]["total"],
                    "public": playlist["public"],
                    "description": playlist.get("description", "")
                })

        url = data.get("next")

    return playlists


def get_playlist_tracks(access_token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=50"
    headers = {"Authorization": f"Bearer {access_token}"}
    tracks = []

    while url:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()

        for item in data.get("items", []):
            if item.get("track") and item["track"].get("id"):
                tracks.append({
                    "id": item["track"]["id"],
                    "name": item["track"]["name"],
                    "artist": ", ".join([artist["name"] for artist in item["track"]["artists"]]),
                    "added_at": item["added_at"]
                })

        url = data.get("next")

    return tracks


def save_liked_tracks(access_token, track_ids):
    url = "https://api.spotify.com/v1/me/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    failed_count = 0

    for i in tqdm(range(0, len(track_ids), 50), desc="Saving liked songs"):
        batch = track_ids[i:i + 50]
        res = requests.put(url, headers=headers, json={"ids": batch})

        if res.status_code not in (200, 201):
            failed_count += len(batch)
            print(f"\nBatch {i // 50 + 1} failed: {res.status_code}")

        time.sleep(0.1)  # Rate limiting

    return failed_count


def create_playlist(access_token, user_id, name, description="", public=False):
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "name": name,
        "description": description,
        "public": public
    }

    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return res.json()["id"]


def add_tracks_to_playlist(access_token, playlist_id, track_ids):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    failed_count = 0

    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i + 100]
        track_uris = [f"spotify:track:{track_id}" for track_id in batch]

        res = requests.post(url, headers=headers, json={"uris": track_uris})

        if res.status_code not in (200, 201):
            failed_count += len(batch)

        time.sleep(0.1)

    return failed_count


# ------------------- Transfer Functions -------------------
def transfer_liked_songs(source_token, dest_token):
    print("Transferring liked songs...")

    # Get liked songs from source
    liked_tracks = get_liked_tracks(source_token)
    if not liked_tracks:
        print("   No liked songs found")
        return {"success": True, "transferred": 0, "failed": 0}

    print(f"   Found {len(liked_tracks)} liked songs")

    # Save to destination
    track_ids = [track["id"] for track in liked_tracks]
    failed_count = save_liked_tracks(dest_token, track_ids)

    success_count = len(track_ids) - failed_count
    print(f"   {success_count} songs transferred successfully")
    if failed_count > 0:
        print(f"   {failed_count} songs failed to transfer")

    return {
        "success": failed_count == 0,
        "transferred": success_count,
        "failed": failed_count,
        "tracks": liked_tracks[:10]  # Sample for log
    }


def transfer_playlists(source_token, dest_token, dest_user_id, selected_playlists=None):
    print("Transferring playlists...")

    # Get playlists from source
    playlists = get_playlists(source_token)
    if not playlists:
        print("   No playlists found")
        return {"success": True, "transferred": 0, "failed": 0}

    if selected_playlists:
        playlists = [p for p in playlists if p["id"] in selected_playlists]

    print(f"   Found {len(playlists)} playlists to transfer")

    transfer_results = []

    for playlist in tqdm(playlists, desc="Creating playlists"):
        try:
            # Get tracks from source playlist
            tracks = get_playlist_tracks(source_token, playlist["id"])
            if not tracks:
                continue

            # Create playlist in destination
            new_playlist_id = create_playlist(
                dest_token,
                dest_user_id,
                f"{playlist['name']} (Transferred)",
                f"Transferred from {playlist['name']} - {playlist['description']}",
                playlist["public"]
            )

            # Add tracks to new playlist
            track_ids = [track["id"] for track in tracks]
            failed_count = add_tracks_to_playlist(dest_token, new_playlist_id, track_ids)

            transfer_results.append({
                "name": playlist["name"],
                "tracks_total": len(track_ids),
                "tracks_failed": failed_count,
                "success": failed_count == 0
            })

            print(f"   {playlist['name']}: {len(track_ids) - failed_count}/{len(track_ids)} tracks")

        except Exception as e:
            print(f"   Failed to transfer '{playlist['name']}': {e}")
            transfer_results.append({
                "name": playlist["name"],
                "success": False,
                "error": str(e)
            })

    successful = sum(1 for r in transfer_results if r.get("success", False))
    failed = len(transfer_results) - successful

    return {
        "success": failed == 0,
        "transferred": successful,
        "failed": failed,
        "results": transfer_results
    }


# ------------------- Main Application -------------------
def authorize_account(account_config, account_key, tokens):
    if f"{account_key}_refresh_token" in tokens:
        try:
            refresh_token(account_config, tokens[f"{account_key}_refresh_token"])
            print(f"   {account_config['name']} already authorized.")
            return True
        except Exception:
            print(f"   Refresh token for {account_config['name']} failed. Re-authorizing...")
            del tokens[f"{account_key}_refresh_token"]

    print(f"\nAuthorizing {account_config['name']}...")
    print("   Please log in to the correct account in your browser")

    auth_url = get_auth_url(account_config)
    code = get_auth_code_automatically(auth_url)

    if not code:
        return False

    try:
        token_data = get_token(account_config, code)
        tokens[f"{account_key}_refresh_token"] = token_data["refresh_token"]
        save_tokens(tokens)
        print(f"   {account_config['name']} authorized successfully!")
        return True
    except Exception as e:
        print(f"   Authorization failed: {e}")
        return False


def display_account_info(access_token, account_name):
    try:
        user_info = get_user_info(access_token)
        liked_count = len(get_liked_tracks(access_token))
        playlists_count = len(get_playlists(access_token))

        print(f"\n{account_name}")
        print(f"   User: {user_info['display_name']}")
        print(f"   ID: {user_info['id']}")
        print(f"   Followers: {user_info['followers']['total']}")
        print(f"   Liked Songs: {liked_count}")
        print(f"   Playlists: {playlists_count}")

        return user_info
    except Exception as e:
        print(f"   Error getting account info: {e}")
        return None


def choose_transfer_options():
    print("\nTransfer Options")
    print("=" * 30)
    print("1. Account 1 → Account 2")
    print("2. Account 2 → Account 1")
    print("3. Both directions (merge)")
    print("4. Cancel")

    while True:
        choice = input("\nSelect transfer direction (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        print("Invalid choice. Please enter 1, 2, 3, or 4.")


def choose_content_type():
    print("\nWhat to transfer:")
    print("1. Liked songs only")
    print("2. Playlists only")
    print("3. Both liked songs and playlists")

    while True:
        choice = input("\nSelect content type (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("Invalid choice. Please enter 1, 2, or 3.")


def main():
    print("Advanced Spotify Transfer Tool")
    print("=" * 40)
    print("Transfer liked songs and playlists between accounts!")

    # Validate environment variables
    if not validate_environment():
        return

    tokens = load_tokens()

    # Step 1: Authorize accounts
    print("\nStep 1: Account Authorization")
    print("-" * 30)

    if not authorize_account(ACCOUNT_1, "account1", tokens):
        return

    print("\n   Please switch to your second account in the browser!")
    print("   (Log out of the first account if needed)")
    input("   Press Enter when ready to authorize Account 2...")

    if not authorize_account(ACCOUNT_2, "account2", tokens):
        return

    # Step 2: Get access tokens and display account info
    print("\nStep 2: Account Information")
    print("-" * 30)

    try:
        token1 = refresh_token(ACCOUNT_1, tokens["account1_refresh_token"])
        token2 = refresh_token(ACCOUNT_2, tokens["account2_refresh_token"])
        print("   Access tokens refreshed successfully!")
    except Exception as e:
        print(f"Error refreshing tokens: {e}")
        print("   Try deleting spotify_tokens.json and running again")
        return

    user1 = display_account_info(token1, "Account 1")
    user2 = display_account_info(token2, "Account 2")

    if not user1 or not user2:
        print("\nTip: If you see 403 errors, delete 'spotify_tokens.json' and restart")
        return

    # Step 3: Choose transfer direction
    direction = choose_transfer_options()
    if direction == '4':
        print("Transfer cancelled.")
        return

    # Step 4: Choose content type
    content_type = choose_content_type()

    # Step 5: Execute transfers
    print(f"\nStep 3: Starting Transfer")
    print("-" * 25)

    transfers = []

    if direction == '1':  # Account 1 → Account 2
        transfers.append((token1, token2, user2['id'], "Account 1", "Account 2"))
    elif direction == '2':  # Account 2 → Account 1
        transfers.append((token2, token1, user1['id'], "Account 2", "Account 1"))
    elif direction == '3':  # Both directions
        transfers.append((token1, token2, user2['id'], "Account 1", "Account 2"))
        transfers.append((token2, token1, user1['id'], "Account 2", "Account 1"))

    for source_token, dest_token, dest_user_id, source_name, dest_name in transfers:
        print(f"\nTransferring {source_name} → {dest_name}")
        print("-" * 40)

        transfer_log = {
            "source": source_name,
            "destination": dest_name,
            "content_type": content_type
        }

        # Transfer liked songs
        if content_type in ['1', '3']:
            liked_result = transfer_liked_songs(source_token, dest_token)
            transfer_log["liked_songs"] = liked_result

        # Transfer playlists
        if content_type in ['2', '3']:
            playlist_result = transfer_playlists(source_token, dest_token, dest_user_id)
            transfer_log["playlists"] = playlist_result

        save_transfer_log(transfer_log)

    print(f"\nTransfer Complete!")
    print("=" * 20)
    print(f"Transfer log saved to: {TRANSFER_LOG}")
    print("You can run this tool again anytime to transfer more content!")


if __name__ == "__main__":
    main()