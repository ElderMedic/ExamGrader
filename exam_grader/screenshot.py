"""Screenshot functionality for cross-platform screen capture"""

import time
from typing import Optional
from PIL import Image
import mss


class ScreenshotCapture:
    """Cross-platform screenshot capture with adjustable region"""
    
    def __init__(self):
        self.sct = mss.mss()
        
    def capture_full_screen(self) -> Image.Image:
        """Capture the entire screen"""
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    def capture_region(self, left: int, top: int, width: int, height: int) -> Image.Image:
        """Capture a specific region of the screen"""
        monitor = {"left": left, "top": top, "width": width, "height": height}
        screenshot = self.sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    def capture_periodically(self, interval: float, duration: float, 
                           region: Optional[dict] = None, 
                           callback=None) -> list:
        """Capture screenshots periodically"""
        images = []
        start_time = time.time()
        capture_count = 0
        
        while time.time() - start_time < duration:
            img = self.capture_region(**region) if region else self.capture_full_screen()
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
