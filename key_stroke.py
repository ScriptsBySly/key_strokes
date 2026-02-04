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
MAX_STROKES = 3
# =========================

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Key Monitor Window")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, FONT_SIZE)
# Add at the top (after strokes and combo_buffer)
pressed_keys = set()

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
combo_buffer = []

# =========================================================
# Modifier keys currently pressed
# =========================================================
current_modifiers = set()
MODIFIER_KEYS = {"CTRL_L", "CTRL_R", "SHIFT", "SHIFT_R", "ALT_L", "ALT_R"}

# =========================================================
# Helpers for key handling
# =========================================================
def fix_control_char(char):
    """Convert control characters from CTRL+letter combos to normal letters"""
    if char and len(char) == 1 and ord(char) <= 26:
        return chr(ord(char) + 64)  # \x01 -> 'A', \x02 -> 'B', etc.
    return char

def key_to_string(key):
    """
    Converts a pynput key to a readable string.
    Fixes CTRL+letter combos, KeyCode.vk integers, and numpad numbers.
    """
    # 1️⃣ Regular character
    if hasattr(key, 'char') and key.char is not None:
        key_str = fix_control_char(key.char)
        key_str = key_str.upper()

    # 2️⃣ KeyCode with vk (virtual key)
    elif hasattr(key, 'vk') and key.vk is not None:
        # Numpad 0-9
        if 96 <= key.vk <= 105:
            key_str = f"Num{key.vk - 96}"
        # Letters A-Z
        elif 65 <= key.vk <= 90:
            key_str = chr(key.vk).upper()
        else:
            key_str = str(key.vk)

    # 3️⃣ Named keys like Key.enter
    elif hasattr(key, 'name') and key.name is not None:
        key_str = key.name.upper()

    # 4️⃣ Fallback
    else:
        key_str = str(key).replace("Key.", "").upper()
        if len(key_str) == 1:
            key_str = key_str

    print(f"[DEBUG] key_to_string: {key} -> {key_str}")
    return key_str



def on_press(key):
    global combo_buffer, strokes, current_modifiers, pressed_keys

    key_str = key_to_string(key)

    # Ignore repeats if key is already pressed
    if key_str in pressed_keys:
        return
    pressed_keys.add(key_str)

    # Modifier key pressed
    if any(mod in key_str for mod in ["CTRL", "ALT", "SHIFT"]):
        current_modifiers.add(key_str.split("_")[0])  # store just CTRL/ALT/SHIFT
        print(f"[DEBUG] Current modifiers: {current_modifiers}")
        return

    # Regular key pressed → combine with current modifiers
    combo_keys = list(current_modifiers) + [key_str]
    current_modifiers.clear()  # reset after combo

    print(f"[DEBUG] Combo keys to display: {combo_keys}")

    # Build keycaps for each key
    images = [build_keycap_surface(k) for k in combo_keys]
    strokes.append({"images": images, "start_time": time.time()})

    # Limit max strokes
    if len(strokes) > MAX_STROKES:
        strokes.pop(0)


def on_release(key):
    key_str = key_to_string(key)
    pressed_keys.discard(key_str)

    # Remove released modifier from set
    if any(mod in key_str for mod in ["CTRL", "ALT", "SHIFT"]):
        current_modifiers.discard(key_str.split("_")[0])
        print(f"[DEBUG] Released modifier: {key_str}, current_modifiers: {current_modifiers}")


listener = keyboard.Listener(on_press=on_press, on_release=on_release)
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
