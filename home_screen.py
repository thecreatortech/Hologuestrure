import pygame
from pygame import mixer
import time
import os
import sys
import math
from camera_manager import CameraManager
import apps.app_2

# Initialize Pygame and mixer
pygame.init()
mixer.init()

# Define constants
SCREEN_SIZE = (1024, 768)
NAVY_BLUE = (20, 20, 40)
LIGHT_BLUE = (173, 216, 230)
WHITE = (255, 255, 255)
HOME_TOGGLE_DELAY = 1.0  # Delay in seconds for home button toggle
APP_SELECT_DELAY = 1.0  # Delay to prevent immediate app launch
SELECTION_ANIMATION_DURATION = 0.3  # Duration of the selection animation in seconds

# Function to play sound
def play_sound(file_path):
    mixer.music.load(file_path)
    mixer.music.play()

# AppCircle class definition
class AppCircle:
    def __init__(self, center, radius, app_index, is_main=False):
        self.center = center
        self.radius = radius
        self.app_index = app_index
        self.text = 'Home' if is_main else f'App {app_index}'
        self.hover_time = 0
        self.is_hovered_flag = False
        self.is_main = is_main
        self.visible = is_main
        self.image = self.load_image()
        self.home_pos = center  # Store the home position for animation
        self.grid_pos = center  # Store the grid position for animation
        self.selection_start_time = None
        self.is_selected = False

    # Load image for the app circle
    def load_image(self):
        if self.is_main:
            return None  # No image for home circle
        else:
            image_path = f'resources/app_{self.app_index}.jpg'
        
        if os.path.exists(image_path):
            image = pygame.image.load(image_path)
            return pygame.transform.scale(image, (int(self.radius * 2), int(self.radius * 2)))
        return None

    # Draw the app circle
    def draw(self, screen):
        if self.visible:
            if self.is_main:
                color = self.get_animated_color() if self.is_selected else NAVY_BLUE
                pygame.draw.circle(screen, color, self.center, self.radius, 3)  # Outline for home circle
                font = pygame.font.Font(None, 36)  # Larger font for home text
                text_surface = font.render(self.text, True, color)
                text_rect = text_surface.get_rect(center=self.center)
                screen.blit(text_surface, text_rect)
            else:
                if self.image:
                    image_rect = self.image.get_rect(center=self.center)
                    screen.blit(self.image, image_rect)
                    if self.is_selected:
                        overlay = pygame.Surface((image_rect.width, image_rect.height), pygame.SRCALPHA)
                        overlay_color = self.get_animated_color()
                        overlay.fill((*overlay_color[:3], 128))  # Semi-transparent overlay
                        screen.blit(overlay, image_rect)
                else:
                    color = self.get_animated_color() if self.is_selected else LIGHT_BLUE
                    pygame.draw.circle(screen, color, self.center, self.radius)
            
            if self.is_hovered_flag:
                pygame.draw.circle(screen, LIGHT_BLUE, self.center, self.radius, 3)

            if not self.is_main:
                font = pygame.font.Font(None, 24)
                text_surface = font.render(self.text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(self.center[0], self.center[1] + self.radius + 20))
                screen.blit(text_surface, text_rect)

    def get_animated_color(self):
        if self.selection_start_time is None:
            return NAVY_BLUE if self.is_main else LIGHT_BLUE
        
        elapsed_time = time.time() - self.selection_start_time
        if elapsed_time > SELECTION_ANIMATION_DURATION:
            self.is_selected = False
            self.selection_start_time = None
            return NAVY_BLUE if self.is_main else LIGHT_BLUE
        
        progress = elapsed_time / SELECTION_ANIMATION_DURATION
        if progress < 0.5:
            return self.interpolate_color(NAVY_BLUE if self.is_main else LIGHT_BLUE, WHITE, progress * 2)
        else:
            return self.interpolate_color(WHITE, NAVY_BLUE if self.is_main else LIGHT_BLUE, (progress - 0.5) * 2)

    def interpolate_color(self, color1, color2, t):
        return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2))

    def start_selection_animation(self):
        self.is_selected = True
        self.selection_start_time = time.time()

    # Check if the circle is being hovered over
    def is_hovered(self, pos):
        return math.hypot(pos[0] - self.center[0], pos[1] - self.center[1]) <= self.radius

# Create app circles
def create_circles():
    circles = []
    num_circles = 10
    home_circle_radius = 75
    app_circle_radius = 70  # Increased size for app icons
    margin = 40  # Increased margin to accommodate larger icons
    circles_per_row = 5

    # Create home circle in the center
    home_circle = AppCircle((SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2), home_circle_radius, 0, is_main=True)
    home_circle.grid_pos = (SCREEN_SIZE[0] - home_circle_radius - margin, SCREEN_SIZE[1] - home_circle_radius - margin)
    circles.append(home_circle)

    # Calculate the total width and height of the app grid
    grid_width = circles_per_row * (app_circle_radius * 2 + margin) - margin
    grid_height = ((num_circles - 1) // circles_per_row + 1) * (app_circle_radius * 2 + margin) - margin

    # Calculate the top-left corner of the grid to center it horizontally and place it at the top
    grid_start_x = (SCREEN_SIZE[0] - grid_width) // 2
    grid_start_y = margin + 50  # Add some top margin

    # Create app circles and set their grid positions
    for i in range(num_circles):
        row = i // circles_per_row
        col = i % circles_per_row
        x = grid_start_x + (app_circle_radius * 2 + margin) * col + app_circle_radius
        y = grid_start_y + (app_circle_radius * 2 + margin) * row + app_circle_radius
        circle = AppCircle((SCREEN_SIZE[0] // 2, -app_circle_radius), app_circle_radius, i + 1)  # Start off-screen
        circle.grid_pos = (x, y)
        circles.append(circle)

    return circles

# Animation function
def animate_circles(circles, show_apps):
    animation_duration = 0.5
    start_time = time.time()
    
    while time.time() - start_time < animation_duration:
        t = (time.time() - start_time) / animation_duration
        t = math.sin(t * math.pi / 2)  # Easing function for smooth animation
        
        for circle in circles:
            if show_apps:
                circle.center = (
                    int(circle.home_pos[0] * (1 - t) + circle.grid_pos[0] * t),
                    int(circle.home_pos[1] * (1 - t) + circle.grid_pos[1] * t)
                )
            else:
                circle.center = (
                    int(circle.grid_pos[0] * (1 - t) + circle.home_pos[0] * t),
                    int(circle.grid_pos[1] * (1 - t) + circle.home_pos[1] * t)
                )
        
        yield

# Main function to run the home screen
def run_home_screen(screen, camera_manager):
    circles = create_circles()
    home_circle = circles[0]
    running = True
    apps_visible = False
    last_toggle_time = 0
    last_app_select_time = 0

    index_finger_pos = None
    play_sound("./audio/startup.wav")
    while running:
        if not camera_manager.update():
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                camera_manager.release()
                sys.exit()

        screen.fill((0, 0, 0))

        for circle in circles:
            circle.is_hovered_flag = False
            circle.draw(screen)

        transformed_landmarks = camera_manager.get_transformed_landmarks()
        if transformed_landmarks:
            for transformed_coords in transformed_landmarks:
                index_finger_tip = transformed_coords[camera_manager.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                screen_x = int(index_finger_tip[0])
                screen_y = int(index_finger_tip[1])
                index_finger_pos = (screen_x, screen_y)

                for circle in circles:
                    if circle.is_hovered((screen_x, screen_y)):
                        circle.is_hovered_flag = True
                        if circle.is_main:
                            print("Home circle hovered")
                            play_sound("./audio/home.wav")
                            if time.time() - last_toggle_time > HOME_TOGGLE_DELAY:
                                apps_visible = not apps_visible
                                print(f"Toggling apps visibility to: {apps_visible}")
                                last_toggle_time = time.time()
                                circle.start_selection_animation()
                                for app_circle in circles[1:]:
                                    app_circle.visible = apps_visible
                                for _ in animate_circles(circles, apps_visible):
                                    screen.fill((0, 0, 0))
                                    for circle in circles:
                                        circle.draw(screen)
                                    pygame.display.flip()
                                    pygame.time.delay(16)  # ~60 FPS
                                # Set last_app_select_time to ensure delay before selecting app
                                last_app_select_time = time.time() + APP_SELECT_DELAY
                        elif circle.visible and apps_visible:
                            if time.time() > last_app_select_time:
                                print(f"Circle {circle.app_index} hovered with visibility {circle.visible}")
                                circle.start_selection_animation()
                                try:
                                    app = f'app_{circle.app_index}'
                                    print(f"Launching app: {app}")
                                    mod = __import__(f'apps.{app}', fromlist=[''])
                                    play_sound("./audio/confirmation.wav")
                                    mod.run(screen, camera_manager)  # Pass camera_manager to the app
                                    last_app_select_time = time.time()
                                except ModuleNotFoundError:
                                    print(f"Module 'apps.{app}' not found.")
                                    play_sound("./audio/reject.wav")
                    else:
                        circle.hover_time = time.time() if circle.visible else 0

        if index_finger_pos:
            pygame.draw.circle(screen, LIGHT_BLUE, index_finger_pos, 15, 3)

        pygame.display.flip()
        pygame.time.delay(50)


# Main execution
if __name__ == '__main__':
    os.environ['SDL_VIDEO_WINDOW_POS'] = '-1024,0'
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('Home Screen')
    camera_manager = CameraManager('./M.npy', 1024, 768)
    run_home_screen(screen, camera_manager)