import pyautogui

from config import SCREENSHOT_PATH
from skills.base import Skill


class ScreenReaderSkill(Skill):
    name = "screen_reader"
    description = "Captures screen state"

    def run(self, input_data, context):
        screenshot = pyautogui.screenshot()
        screenshot.save(SCREENSHOT_PATH)
        return f"Screenshot captured and stored at {SCREENSHOT_PATH}, sir."
