
import psutil

description = "Provides system status like CPU, RAM, and Battery."
triggers = ["system", "status", "cpu", "ram", "battery", "performance"]

def run(command: str):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()

    status = f"System is stable, sir. CPU usage is at {cpu} percent, and memory is at {ram} percent."

    if battery:
        status += f" Your battery is at {battery.percent} percent."
        if battery.percent < 20 and not battery.power_plugged:
            status += " I recommend connecting to a power source soon."

    return status
