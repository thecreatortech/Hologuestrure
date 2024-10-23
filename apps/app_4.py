import pygame
from pygame import mixer
import time
import cv2
from camera_manager import CameraManager

def run(screen, camera_manager):
    # Initialize Pygame and mixer
    pygame.init()
    mixer.init()
    

    SCREEN_SIZE = (1024, 768)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    LIGHT_BLUE = (173, 216, 230)
    NAVY_BLUE = (20, 20, 40)
    RED = (255, 0, 0)

    def play_sound(file_path):
        try:
            mixer.music.load(file_path)
            mixer.music.play()
        except pygame.error as e:
            print(f"Error playing sound {file_path}: {e}")

    running = True
    current_number = ""
    operation = None
    result = 0
    index_pos = None
    last_button_press = 0
    button_cooldown = 0.5  # Cooldown time in seconds

    button_size = 80
    button_margin = 20
    start_x = (SCREEN_SIZE[0] - (4 * button_size + 3 * button_margin)) // 2
    start_y = 300

    buttons = [
        '7', '8', '9', '/',
        '4', '5', '6', '*',
        '1', '2', '3', '-',
        '0', 'C', '=', '+'
    ]

    button_rects = {}
    for i, button in enumerate(buttons):
        x = start_x + (i % 4) * (button_size + button_margin)
        y = start_y + (i // 4) * (button_size + button_margin)
        button_rects[button] = pygame.Rect(x, y, button_size, button_size)

    # Add exit button
    exit_button_rect = pygame.Rect(SCREEN_SIZE[0] - 100, 40, 80, 40)

    font = pygame.font.Font(None, 36)
    large_font = pygame.font.Font(None, 72)

    while running:
        if not camera_manager.update():
            continue

        current_time = time.time()
        button_pressed = None

        transformed_landmarks = camera_manager.get_transformed_landmarks()
        if transformed_landmarks:
            for hand_landmarks in transformed_landmarks:
                new_index_pos = (int(hand_landmarks[8][0]), int(hand_landmarks[8][1]))  # INDEX_FINGER_TIP

                if index_pos is None:  # Finger just entered
                    index_pos = new_index_pos
                elif index_pos != new_index_pos:  # Finger moved
                    for button, rect in button_rects.items():
                        if rect.collidepoint(index_pos) and not rect.collidepoint(new_index_pos):
                            if current_time - last_button_press > button_cooldown:
                                button_pressed = button
                                last_button_press = current_time
                                play_sound('./audio/quick_click.wav')
                    
                    # Check for exit button
                    if exit_button_rect.collidepoint(index_pos) and not exit_button_rect.collidepoint(new_index_pos):
                        if current_time - last_button_press > button_cooldown:
                            play_sound('./audio/back.wav')
                            return  # Exit the calculator app
                    
                    index_pos = new_index_pos

        if button_pressed:
            if button_pressed.isdigit():
                current_number += button_pressed
            elif button_pressed == 'C':
                current_number = ""
                operation = None
                result = 0
            elif button_pressed in ['+', '-', '*', '/']:
                if current_number:
                    if operation:
                        result = eval(f"{result} {operation} {current_number}")
                    else:
                        result = float(current_number)
                    current_number = ""
                operation = button_pressed
            elif button_pressed == '=':
                if operation and current_number:
                    result = eval(f"{result} {operation} {current_number}")
                    current_number = str(result)
                    operation = None

        screen.fill(BLACK)

        # Draw calculator display
        display_text = current_number if current_number else str(result)
        text_surface = large_font.render(display_text, True, WHITE)
        text_rect = text_surface.get_rect(center=(SCREEN_SIZE[0] // 2, 150))
        screen.blit(text_surface, text_rect)

        # Draw current operation
        if operation:
            op_surface = font.render(f"Operation: {operation}", True, WHITE)
            op_rect = op_surface.get_rect(center=(SCREEN_SIZE[0] // 2, 220))
            screen.blit(op_surface, op_rect)

        # Draw buttons
        for button, rect in button_rects.items():
            pygame.draw.rect(screen, NAVY_BLUE, rect)
            pygame.draw.rect(screen, LIGHT_BLUE, rect, 2)
            text_surface = font.render(button, True, WHITE)
            text_rect = text_surface.get_rect(center=rect.center)
            screen.blit(text_surface, text_rect)

        # Draw exit button
        pygame.draw.rect(screen, NAVY_BLUE, exit_button_rect)
        pygame.draw.rect(screen, LIGHT_BLUE, exit_button_rect, 2)
        exit_text = font.render("Exit", True, WHITE)
        exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
        screen.blit(exit_text, exit_text_rect)

        # Draw index finger pointer
        if index_pos:
            pygame.draw.circle(screen, RED, index_pos, 10)

        pygame.display.flip()
        pygame.time.delay(50)

        # Display camera frame using OpenCV
        # frame = camera_manager.frame
        # if frame is not None:
        #     cv2.imshow("Camera View", frame)
        
        # Break out of loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

    cv2.destroyAllWindows()

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption('Calculator App')
    camera_manager = CameraManager('./M.npy', 1024, 768)
    run(screen, camera_manager)
    pygame.quit()
