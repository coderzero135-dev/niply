"""
Create the Niply app logo as a crisp, HD Windows .ico file.

This script generates each icon size independently using simple geometric
shapes for maximum crispness at every resolution.

Run:
    python create_logo.py

Output:
    icon.ico
"""

from PIL import Image, ImageDraw


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def draw_gradient_background(draw, size, color1, color2):
    """Draw a vertical gradient background."""
    for y in range(size):
        ratio = y / size
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))


def draw_logo(size):
    """
    Draw the Niply logo at a specific size.
    Uses simple, bold shapes that stay crisp at all icon sizes.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors
    bg_top = hex_to_rgb("#0a0a14")
    bg_bottom = hex_to_rgb("#151525")
    card_color = hex_to_rgb("#1e3a5f")
    accent = hex_to_rgb("#00d4ff")
    n_color = (255, 255, 255, 255)

    # Background gradient
    draw_gradient_background(draw, size, bg_top, bg_bottom)

    # Card square with rounded corners
    padding = max(2, int(size * 0.12))
    radius = max(2, int(size * 0.15))
    border_width = max(1, int(size * 0.025))

    # Main card
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=radius,
        fill=card_color
    )

    # Accent border
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=radius,
        outline=accent,
        width=border_width
    )

    # Draw bold "N" using simple rectangles
    # Calculate N area inside card
    n_padding = int(size * 0.28)
    left = padding + n_padding
    right = size - padding - n_padding
    top = padding + int(size * 0.22)
    bottom = size - padding - int(size * 0.22)

    bar_width = max(2, int((right - left) * 0.28))

    # Left vertical bar
    draw.rounded_rectangle(
        [left, top, left + bar_width, bottom],
        radius=max(1, bar_width // 4),
        fill=n_color
    )

    # Right vertical bar
    draw.rounded_rectangle(
        [right - bar_width, top, right, bottom],
        radius=max(1, bar_width // 4),
        fill=n_color
    )

    # Diagonal bar - drawn as a filled polygon
    diagonal_points = [
        (left + bar_width, top),
        (right, top),
        (right - bar_width, bottom),
        (left, bottom),
    ]
    draw.polygon(diagonal_points, fill=n_color)

    return img


def create_ico(filename="icon.ico"):
    """Create a multi-size .ico file."""
    sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 192, 256]
    images = []

    for size in sizes:
        img = draw_logo(size)
        images.append(img)

    images[0].save(
        filename,
        format="ICO",
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )

    print(f"Created crisp HD logo: {filename}")
    print(f"Included sizes: {sizes}px")


if __name__ == "__main__":
    create_ico()
