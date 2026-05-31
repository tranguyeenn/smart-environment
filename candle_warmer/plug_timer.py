import subprocess
import time

PLUG_IP = "192.168.1.183"

def plug(command: str):
    subprocess.run(['kasa', '--host', PLUG_IP, command], check=True)

minutes = int(input("Run for how many minutes? "))

plug("on")
print(f"Plug on for {minutes} minutes")

time.sleep(minutes * 60)

plug("off")
print("Plug off.")