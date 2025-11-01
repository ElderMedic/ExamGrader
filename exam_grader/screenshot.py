"""Screenshot functionality for cross-platform screen capture"""

import time
import platform
from typing import Optional, Tuple
from PIL import Image
import mss
import mss.tools


class ScreenshotCapture:
    """Cross-platform screenshot capture with adjustable region"""
    
    def __init__(self):
        self.system = platform.system()
        self.sct = mss.mss()
        
    def capture_full_screen(self) -> Image.Image:
        """Capture the entire screen"""
        monitor = self.sct.monitors[1]  # Primary monitor
        screenshot = self.sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img
    
    def capture_region(self, left: int, top: int, width: int, height: int) -> Image.Image:
        """Capture a specific region of the screen
        
        Args:
            left: Left coordinate
            top: Top coordinate  
            width: Width of the region
            height: Height of the region
            
        Returns:
            PIL Image of the captured region
        """
        monitor = {
            "left": left,
            "top": top,
            "width": width,
            "height": height
        }
        screenshot = self.sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img
    
    def capture_with_interactive_selection(self) -> Tuple[Image.Image, dict]:
        """Interactive region selection for screenshot
        
        Returns:
            Tuple of (PIL Image, region dict with left, top, width, height)
        """
        print("Interactive region selection not implemented yet.")
        print("Using full screen capture as fallback.")
        print("You can manually specify region using capture_region()")
        img = self.capture_full_screen()
        monitor = self.sct.monitors[1]
        region = {
            "left": monitor["left"],
            "top": monitor["top"],
            "width": monitor["width"],
            "height": monitor["height"]
        }
        return img, region
    
    def capture_periodically(self, interval: float, duration: float, 
                           region: Optional[dict] = None, 
                           callback=None) -> list:
        """Capture screenshots periodically
        
        Args:
            interval: Time interval between captures in seconds
            duration: Total duration to capture in seconds
            region: Optional dict with left, top, width, height. If None, captures full screen
            callback: Optional callback function(img, index) called after each capture
            
        Returns:
            List of captured PIL Images
        """
        images = []
        start_time = time.time()
        capture_count = 0
        
        print(f"Starting periodic capture: interval={interval}s, duration={duration}s")
        
        while time.time() - start_time < duration:
            if region:
                img = self.capture_region(
                    region["left"], region["top"],
                    region["width"], region["height"]
                )
            else:
                img = self.capture_full_screen()
            
            images.append(img)
            capture_count += 1
            
            if callback:
                callback(img, capture_count)
            
            if time.time() - start_time < duration:
                time.sleep(interval)
        
        print(f"Captured {len(images)} screenshots")
        return images
    
    def save_image(self, image: Image.Image, filepath: str):
        """Save image to file"""
        image.save(filepath)
        print(f"Image saved to {filepath}")


def select_region_interactive() -> dict:
    """Interactive region selection using mouse (simplified version)
    
    Note: This is a basic implementation. For better UX, consider using tkinter
    or other GUI libraries for visual region selection.
    """
    print("\n=== Region Selection ===")
    print("This is a simplified version. Please manually enter coordinates.")
    print("You can also use capture_full_screen() for full screen capture.")
    
    try:
        left = int(input("Enter left coordinate: "))
        top = int(input("Enter top coordinate: "))
        width = int(input("Enter width: "))
        height = int(input("Enter height: "))
        
        return {
            "left": left,
            "top": top,
            "width": width,
            "height": height
        }
    except ValueError:
        print("Invalid input. Using full screen.")
        return None
