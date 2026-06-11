import pyautogui
import pygetwindow as gw

# Safety Settings
pyautogui.FAILSAFE = True  # Move to corner (0,0 etc.) to abort

class DesktopController:
    """[BACKEND] Advanced Desktop Automation Engine"""

    def __init__(self):
        pass

    def move_mouse(self, x, y, duration=0, smooth=True):
        """Move mouse to absolute coordinates."""
        pyautogui.moveTo(x, y, duration=duration)
        return f"Mouse moved to ({x}, {y})"

    def click(self, x=None, y=None, button='left', clicks=1):
        """Perform mouse click(s)."""
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)
        return f"Clicked {button} at {x or 'current'}, {y or 'current'} ({clicks}x)"

    def type_text(self, text, wpm=None):
        """Type text with optional WPM simulation."""
        interval = 60 / (wpm * 5) if wpm else 0
        pyautogui.write(text, interval=interval)
        return f"Typed: {text[:20]}..."

    def hotkey(self, keys):
        """Execute hotkey combination (e.g. ['ctrl', 'c'])."""
        pyautogui.hotkey(*keys)
        return f"Hotkey executed: {keys}"

    def screenshot(self, path="screenshot.png", region=None):
        """Capture screen or region."""
        img = pyautogui.screenshot(region=region)
        img.save(path)
        return f"Screenshot saved to {path}"

    def find_on_screen(self, template_path, confidence=0.8):
        """Find image on screen via OpenCV."""
        try:
            loc = pyautogui.locateOnScreen(template_path, confidence=confidence)
            if loc: return {"x": loc.left, "y": loc.top, "w": loc.width, "h": loc.height}  # noqa: E701
        except: pass  # noqa: E701, E722
        return None

    def window_activate(self, title):
        """Bring window to front by title substring."""
        try:
            win = gw.getWindowsWithTitle(title)
            if win:
                win[0].activate()
                return f"Window '{title}' activated."
        except: pass  # noqa: E701, E722
        return f"Error: Window '{title}' not found."

    def window_list(self):
        """Return list of all open window titles."""
        return [w.title for w in gw.getAllWindows() if w.title]

    def clipboard_copy(self, text):
        pyautogui.write(text) # PyAutoGUI doesn't direct copy, but we can type.
        # For real clipboard, usually need 'pyperclip'
        return "Text copied to clipboard logic (typed)."

def desktop_interact(action, params):
    """[BACKEND] Universal Desktop Interaction Interface"""
    dc = DesktopController()
    if action == "move": return dc.move_mouse(**params)  # noqa: E701
    if action == "click": return dc.click(**params)  # noqa: E701
    if action == "type": return dc.type_text(**params)  # noqa: E701
    if action == "hotkey": return dc.hotkey(**params)  # noqa: E701
    if action == "window_activate": return dc.window_activate(**params)  # noqa: E701
    if action == "window_list": return dc.window_list()  # noqa: E701
    if action == "screenshot": return dc.screenshot(**params)  # noqa: E701
    if action == "find": return dc.find_on_screen(**params)  # noqa: E701
    return f"Error: Unrecognized desktop action '{action}'"
