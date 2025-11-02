#!/usr/bin/env python3
"""Helper script to get window coordinates for screenshot region"""

import sys
import time
import mss

def get_mouse_position():
    """Simple helper - prints monitor info and waits for user input"""
    sct = mss.mss()
    
    print("\n=== Monitor Information ===")
    for i, monitor in enumerate(sct.monitors):
        if i == 0:
            print(f"Index {i}: All monitors combined")
        else:
            print(f"Index {i}: Monitor {i}")
        print(f"  Position: ({monitor['left']}, {monitor['top']})")
        print(f"  Size: {monitor['width']}x{monitor['height']}")
        print()
    
    print("=== Manual Method ===")
    print("To find window coordinates:")
    print("1. On macOS: Use Command+Shift+4, drag to select area")
    print("   The coordinates shown are relative to your screen")
    print()
    print("2. On Windows: Use Snipping Tool, it shows coordinates")
    print()
    print("3. On Linux: Use 'xdotool getmouselocation' or screenshot tools")
    print()
    print("=== Region Format ===")
    print("Format: left,top,width,height")
    print("Example for 2K screen (2560x1440) top-left 800x600 window:")
    print("  --region \"0,0,800,600\"")
    print()
    print("If window is at (100, 50) with size 800x600:")
    print("  --region \"100,50,800,600\"")

if __name__ == "__main__":
    get_mouse_position()

