"""Screenshot functionality for cross-platform screen capture"""

import time
from typing import Optional, List, Dict
from PIL import Image
import mss


class ScreenshotCapture:
    """Cross-platform screenshot capture with adjustable region and multi-monitor support"""
    
    def __init__(self):
        self.sct = mss.mss()
    
    def list_monitors(self) -> List[Dict]:
        """List all available monitors
        
        Returns:
            List of monitor dictionaries with index, position, and size
        """
        monitors = []
        # monitors[0] is all monitors combined, monitors[1:] are individual monitors
        for i, monitor in enumerate(self.sct.monitors):
            if i == 0:
                monitors.append({
                    "index": i,
                    "name": "All monitors (combined)",
                    "left": monitor["left"],
                    "top": monitor["top"],
                    "width": monitor["width"],
                    "height": monitor["height"]
                })
            else:
                monitors.append({
                    "index": i,
                    "name": f"Monitor {i}",
                    "left": monitor["left"],
                    "top": monitor["top"],
                    "width": monitor["width"],
                    "height": monitor["height"]
                })
        return monitors
    
    def print_monitors(self):
        """Print available monitors information"""
        monitors = self.list_monitors()
        print("\nAvailable Monitors:")
        print("-" * 70)
        for mon in monitors:
            print(f"  Index {mon['index']}: {mon['name']}")
            print(f"    Position: ({mon['left']}, {mon['top']})")
            print(f"    Size: {mon['width']}x{mon['height']}")
        print("-" * 70)
        
    def capture_full_screen(self, monitor_index: Optional[int] = None) -> Image.Image:
        """Capture the entire screen or a specific monitor
        
        Args:
            monitor_index: Monitor index (1-based, None for first monitor)
                          Use 0 for all monitors combined, 1 for first monitor, 2 for second, etc.
        """
        if monitor_index is None:
            # Default to first physical monitor (index 1)
            monitor_index = 1
        
        if monitor_index < 0 or monitor_index >= len(self.sct.monitors):
            raise ValueError(f"Invalid monitor index {monitor_index}. Use --list-monitors to see available monitors.")
        
        monitor = self.sct.monitors[monitor_index]
        screenshot = self.sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    def capture_region(self, left: int, top: int, width: int, height: int) -> Image.Image:
        """Capture a specific region of the screen"""
        monitor = {"left": left, "top": top, "width": width, "height": height}
        screenshot = self.sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    def capture_periodically(self, interval: float, duration: float, 
                           region: Optional[dict] = None,
                           monitor_index: Optional[int] = None,
                           callback=None) -> list:
        """Capture screenshots periodically
        
        Args:
            interval: Time between captures in seconds
            duration: Total duration in seconds
            region: Optional dict with left, top, width, height
            monitor_index: Optional monitor index (None uses default)
            callback: Optional callback function(img, index)
        """
        images = []
        start_time = time.time()
        capture_count = 0
        
        while time.time() - start_time < duration:
            if region:
                img = self.capture_region(**region)
            else:
                img = self.capture_full_screen(monitor_index)
            images.append(img)
            capture_count += 1
            
            if callback:
                callback(img, capture_count)
            
            if time.time() - start_time < duration:
                time.sleep(interval)
        
        return images
    
    def save_image(self, image: Image.Image, filepath: str):
        """Save image to file"""
        image.save(filepath)
