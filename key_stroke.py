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

FONT_SIZE = 72
TEXT_COLOR = (0, 0, 0)

BOTTOM_LEFT_MARGIN = 10  # space from bottom-left
VERTICAL_SPACING = 10    # space between stacked keycaps
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
    rotated 45 degrees CCW, and translated by (5, -5).
    Returns a pygame.Surface with alpha.
    """

    # Load base image
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

    # Rotate text 45 degrees CCW
    rotated_text = pygame.transform.rotate(text_surface, 40)

    # Center rotated text on the keycap
    text_rect = rotated_text.get_rect(center=(new_size[0] // 2, new_size[1] // 2))

    # Apply translation offset (X=5, Y=-5)
    text_rect.centerx += 0
    text_rect.centery += -30

    # Blit rotated and translated text onto the keycap
    final_surface = base.copy()
    final_surface.blit(rotated_text, text_rect)

    return final_surface


# =========================================================
# Stroke tracking (bottom-left stacking)
# Each stroke = dict with keys: image, start_time
# =========================================================
strokes = []
MAX_STROKES = 3


# =========================================================
# Global keyboard listener
# =========================================================
def key_to_string(key):
    try:
        return key.char.upper()
    except AttributeError:
        return str(key).replace("Key.", "").upper()


def on_press(key):
    key_str = key_to_string(key)

    # Build the keycap image
    image_surf = build_keycap_surface(key_str)

    # Add new stroke to list
    strokes.append({"image": image_surf, "start_time": time.time()})

    # Keep max 3 active strokes
    if len(strokes) > MAX_STROKES:
        strokes.pop(0)  # remove oldest


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

    for stroke in reversed(strokes):  # reversed = newest last
        elapsed = time.time() - stroke["start_time"]
        if elapsed >= VISIBLE_TIME:
            continue  # skip expired

        fade_start = VISIBLE_TIME - FADE_TIME
        if elapsed >= fade_start:
            fade_progress = (elapsed - fade_start) / FADE_TIME
            alpha = 255 * (1 - fade_progress)
        else:
            alpha = 255

        img = stroke["image"].copy()
        img.set_alpha(int(max(0, min(255, alpha))))

        rect = img.get_rect()
        rect.bottomleft = (BOTTOM_LEFT_MARGIN, y_pos)
        screen.blit(img, rect)

        # Move up for the next (older) key
        y_pos -= rect.height + VERTICAL_SPACING


    # Remove fully expired strokes
    strokes = [s for s in strokes if time.time() - s["start_time"] < VISIBLE_TIME]

    pygame.display.flip()
    clock.tick(FPS)


listener.stop()
pygame.quit()
sys.exit()
