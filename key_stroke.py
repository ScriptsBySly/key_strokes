import pygame
import sys
import time
from pynput import keyboard

# =========================
# Configurable parameters
# =========================
WIDTH = 600
HEIGHT = 600

BG_COLOR = (0, 255, 0)
IMAGE_PATH = "key_cap.png"

VISIBLE_TIME = 1.5
FADE_TIME = 0.5

FPS = 60

FONT_SIZE = 48  # smaller for multiple caps
TEXT_COLOR = (0, 0, 0)

BOTTOM_LEFT_MARGIN = 0
VERTICAL_SPACING = 10
HORIZONTAL_SPACING = 0
# =========================


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Key Monitor Window")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, FONT_SIZE)


# =========================================================
# IMAGE PROCESSING FUNCTION
# =========================================================
def build_keycap_surface(key_string):
    """
    Creates a scaled keycap image with centered transparent text,
    rotated 40 degrees CCW, translated by (0, -30).
    Returns a pygame.Surface with alpha.
    """
    base = pygame.image.load(IMAGE_PATH).convert_alpha()

    # Scale to 1/3 window
    target_w = WIDTH // 3
    target_h = HEIGHT // 3
    img_w, img_h = base.get_size()
    scale = min(target_w / img_w, target_h / img_h)
    new_size = (int(img_w * scale), int(img_h * scale))
    base = pygame.transform.smoothscale(base, new_size)

    # Render text
    text_surface = font.render(key_string, True, TEXT_COLOR)
    rotated_text = pygame.transform.rotate(text_surface, 40)
    text_rect = rotated_text.get_rect(center=(new_size[0] // 2, new_size[1] // 2))
    text_rect.centery += -30

    final_surface = base.copy()
    final_surface.blit(rotated_text, text_rect)
    return final_surface


# =========================================================
# Stroke tracking (bottom-left stacking)
# Each stroke = dict with keys: images (list of surfaces), start_time
# =========================================================
strokes = []
MAX_STROKES = 3

combo_buffer = []
SPECIAL_KEYS = {"CTRL", "ALT", "SHIFT"}


# =========================================================
# Keyboard listener
# =========================================================
def key_to_string(key):
    try:
        return key.char.upper()
    except AttributeError:
        return str(key).replace("Key.", "").upper()


def on_press(key):
    global combo_buffer, strokes

    key_str = key_to_string(key)

    # Detect special keys (contains CTRL/ALT/SHIFT)
    if any(special in key_str for special in SPECIAL_KEYS):
        if len(combo_buffer) < 2:
            combo_buffer.append(key_str.split("_")[0])  # store "CTRL" instead of "CTRL_L"
        return

    # Normal key or combo completion
    if combo_buffer:
        combo_keys = combo_buffer + [key_str]
        combo_buffer = []
    else:
        combo_keys = [key_str]

    # Build one keycap per key
    images = [build_keycap_surface(k) for k in combo_keys]

    # Add as one row (stroke)
    strokes.append({"images": images, "start_time": time.time()})

    # Keep max strokes
    if len(strokes) > MAX_STROKES:
        strokes.pop(0)


listener = keyboard.Listener(on_press=on_press)
listener.start()


# =========================================================
# Main loop
# =========================================================
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)

    # Draw strokes from newest to oldest (bottom to top)
    y_pos = HEIGHT - BOTTOM_LEFT_MARGIN

    for stroke in reversed(strokes):
        elapsed = time.time() - stroke["start_time"]
        if elapsed >= VISIBLE_TIME:
            continue

        fade_start = VISIBLE_TIME - FADE_TIME
        if elapsed >= fade_start:
            fade_progress = (elapsed - fade_start) / FADE_TIME
            alpha = 255 * (1 - fade_progress)
        else:
            alpha = 255

        # Draw each keycap in the row
        x_pos = BOTTOM_LEFT_MARGIN
        for img in stroke["images"]:
            img_copy = img.copy()
            img_copy.set_alpha(int(max(0, min(255, alpha))))
            rect = img_copy.get_rect()
            rect.bottomleft = (x_pos, y_pos)
            screen.blit(img_copy, rect)
            x_pos += rect.width + HORIZONTAL_SPACING

        # Move up for next row
        max_height = max(img.get_height() for img in stroke["images"])
        y_pos -= max_height + VERTICAL_SPACING

    # Remove expired strokes
    strokes = [s for s in strokes if time.time() - s["start_time"] < VISIBLE_TIME]

    pygame.display.flip()
    clock.tick(FPS)


listener.stop()
pygame.quit()
sys.exit()
