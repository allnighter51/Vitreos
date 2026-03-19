#!/usr/bin/env python3
"""
Simple script to create a Mercury icon for the application
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_mercury_icon():
    """Create a simple Mercury-themed icon"""
    
    # Create a 256x256 image
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw mercury-themed design
    # Background gradient
    for y in range(size):
        # Blue to purple gradient
        r = int(0)
        g = int(242 * (y / size))
        b = int(255 * (1 - y / size) + 50 * (y / size))
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Mercury symbol in the center
    center = size // 2
    radius = size // 3
    
    # Draw the circle
    draw.ellipse([(center - radius, center - radius), (center + radius, center + radius)], 
                fill=(0, 242, 255, 200), outline=(255, 255, 255, 255), width=4)
    
    # Draw the cross
    cross_size = radius // 2
    draw.line([(center, center - cross_size), (center, center + cross_size)], 
             fill=(255, 255, 255, 255), width=4)
    draw.line([(center - cross_size, center), (center + cross_size, center)], 
             fill=(255, 255, 255, 255), width=4)
    
    # Draw the top line
    draw.line([(center, center - radius - 10), (center, center - radius - 30)], 
             fill=(255, 255, 255, 255), width=4)
    
    # Save as ICO
    img.save('mercury.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    
    print("Mercury icon created successfully!")

if __name__ == "__main__":
    try:
        from PIL import Image, ImageDraw
        create_mercury_icon()
    except ImportError:
        print("PIL/Pillow not installed. Creating a simple text-based icon file...")
        # Create a simple placeholder
        with open('mercury.ico', 'wb') as f:
            f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x10\x00\x01\x00\x20\x00\x68\x04\x00\x00\x26\x00\x00\x00')
        print("Placeholder icon created. Install PIL for better icon.")