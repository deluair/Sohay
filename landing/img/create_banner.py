import os
from PIL import Image, ImageDraw, ImageFont

# Create banner dimensions
width = 1200
height = 300

# Create a new image with a gradient background
image = Image.new('RGB', (width, height), color=(30, 30, 40))
draw = ImageDraw.Draw(image)

# Create gradient background
for y in range(height):
    r = int(30 + (50 - 30) * y / height)
    g = int(30 + (100 - 30) * y / height)
    b = int(40 + (150 - 40) * y / height)
    for x in range(width):
        # Add some horizontal variation
        r_mod = min(255, r + int(10 * (x / width)))
        g_mod = min(255, g + int(20 * (x / width)))
        b_mod = min(255, b + int(30 * (x / width)))
        draw.point((x, y), fill=(r_mod, g_mod, b_mod))

# Try to use a nice font if available, otherwise use default
try:
    # Try to find a good system font
    system_fonts = []
    if os.name == 'nt':  # Windows
        font_dir = "C:\\Windows\\Fonts"
        for font_name in ['Arial.ttf', 'Segoe UI Bold.ttf', 'Verdana.ttf']:
            if os.path.exists(os.path.join(font_dir, font_name)):
                system_fonts.append(os.path.join(font_dir, font_name))
    elif os.name == 'posix':  # macOS/Linux
        font_dirs = [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            "/usr/share/fonts/truetype/",
            "~/.fonts/"
        ]
        for font_dir in font_dirs:
            font_dir = os.path.expanduser(font_dir)
            if os.path.exists(font_dir):
                for font_file in os.listdir(font_dir):
                    if font_file.endswith('.ttf'):
                        system_fonts.append(os.path.join(font_dir, font_file))
                        if len(system_fonts) >= 3:
                            break
                if len(system_fonts) >= 3:
                    break
    
    # Use first found font or default to None (PIL will use default bitmap font)
    font_file = system_fonts[0] if system_fonts else None
    font_large = ImageFont.truetype(font_file, 80) if font_file else ImageFont.load_default()
    font_small = ImageFont.truetype(font_file, 30) if font_file else ImageFont.load_default()
except Exception:
    # Fall back to default font
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Draw text shadow for main title
shadow_offset = 3
draw.text((width//2 - shadow_offset + 2, height//2 - 50 - shadow_offset), 
          "SOHAY", 
          font=font_large, 
          fill=(20, 20, 30), 
          anchor="mm")

# Draw main title
draw.text((width//2, height//2 - 50), 
          "SOHAY", 
          font=font_large, 
          fill=(220, 220, 255), 
          anchor="mm")

# Draw subtitle shadow
draw.text((width//2 - shadow_offset + 1, height//2 + 20 - shadow_offset), 
          "Autonomous AI Assistant", 
          font=font_small, 
          fill=(20, 20, 30), 
          anchor="mm")

# Draw subtitle
draw.text((width//2, height//2 + 20), 
          "Autonomous AI Assistant", 
          font=font_small, 
          fill=(180, 200, 255), 
          anchor="mm")

# Add some decorative elements
for i in range(10):
    size = 20 + i * 15
    opacity = 100 - i * 8
    x_pos = 100 + i * 100
    draw.rectangle(
        [x_pos, height - 80, x_pos + size, height - 80 + size], 
        outline=(100, 150, 200, opacity), 
        width=2
    )

# Save the image
image.save("landing/img/sohay-banner.png")
print("Banner created successfully at landing/img/sohay-banner.png") 