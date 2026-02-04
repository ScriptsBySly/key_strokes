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
# =========================


# =========================
# Stroke tracking
# =========================
strokes = [
    [None, None, None],
    [None, None, None],
    [None, None, None]
]
# =========================


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Key Monitor Window")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, FONT_SIZE)


# =========================================================
# IMAGE PROCESSING FUNCTION (NEW)
# Builds the final image with key text overlay
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


current_image = None
img_rect = None
last_key_time = -999
showing = False


# =========================
# Global keyboard listener
# =========================
def key_to_string(key):
    """Convert pynput key to readable string"""
    try:
        return key.char.upper()
    except AttributeError:
        return str(key).replace("Key.", "").upper()


def on_press(key):
    global last_key_time, showing, current_image, img_rect

    key_str = key_to_string(key)

    # Build new image with text
    current_image = build_keycap_surface(key_str)

    img_rect = current_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    last_key_time = time.time()
    showing = True


listener = keyboard.Listener(on_press=on_press)
listener.start()


# =========================
# Main loop
# =========================
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)

    if showing and current_image:
        elapsed = time.time() - last_key_time

        if elapsed < VISIBLE_TIME:
            fade_start = VISIBLE_TIME - FADE_TIME

            if elapsed >= fade_start:
                fade_progress = (elapsed - fade_start) / FADE_TIME
                alpha = 255 * (1 - fade_progress)
            else:
                alpha = 255

            temp_img = current_image.copy()
            temp_img.set_alpha(int(max(0, min(255, alpha))))
            screen.blit(temp_img, img_rect)
        else:
            showing = False

    pygame.display.flip()
    clock.tick(FPS)


listener.stop()
pygame.quit()
sys.exit()
