import pygame
from pygame import mixer
import time
import os
from camera_manager import CameraManager


def run(screen, camera_manager):
    pygame.init()
    mixer.init()

    SCREEN_SIZE = (1024, 768)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    LIGHT_BLUE = (173, 216, 230)
    NAVY_BLUE = (20, 20, 40)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)

    def play_sound(file_path):
        try:
            mixer.music.load(file_path)
            mixer.music.play()
        except pygame.error as e:
            print(f"Error playing sound {file_path}: {e}")

    def save_text_to_file(text, filename):
        if not os.path.exists('saved_texts'):
            os.makedirs('saved_texts')
        full_filename = f"saved_texts/{filename}.txt"
        with open(full_filename, 'w') as f:
            f.write(text)
        return full_filename

    running = True
    text = ""
    filename = ""
    index_pos = None
    last_button_press = 0
    button_cooldown = 0.5  # Cooldown time in seconds

    button_size = 60
    button_margin = 5
    start_x = (SCREEN_SIZE[0] - (14 * button_size + 13 * button_margin)) // 2
    start_y = SCREEN_SIZE[1] - 5 * (button_size + button_margin) - 20

    keys = [
        ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", 'Z', 'X'],
        ['C', 'V', 'B', 'N', 'M', ',', '.', '/', 'SPACE', '<-'],
        ['ENTER']
    ]

    button_rects = {}
    for row, key_row in enumerate(keys):
        x = start_x
        y = start_y + row * (button_size + button_margin)
        for key in key_row:
            if key == 'SPACE':
                width = button_size * 3
            elif key == '<-':
                width = button_size * 2
            elif key == 'ENTER':
                width = button_size * 2
                x = start_x  # Start ENTER key from the left
            else:
                width = button_size
            
            button_rects[key] = pygame.Rect(x, y, width, button_size)
            x += width + button_margin

    # Add exit and save buttons
    exit_button_rect = pygame.Rect(SCREEN_SIZE[0] - 100, 50, 80, 40)
    save_button_rect = pygame.Rect(SCREEN_SIZE[0] - 200, 50, 80, 40)

    # Distance from the top of the screen
    top_margin = 100

    # Adjust the x-coordinates to center the elements horizontally
    filename_input_rect = pygame.Rect(
        SCREEN_SIZE[0] // 2 - 150,  # Center horizontally
        top_margin,                 # Distance from the top
        300,                        # Width
        40                          # Height
    )

    save_confirm_rect = pygame.Rect(
        SCREEN_SIZE[0] // 2 - 160,  # Center horizontally
        top_margin + 50,            # Distance from the top (below the filename input)
        150,                        # Width
        40                          # Height
    )

    cancel_rect = pygame.Rect(
        SCREEN_SIZE[0] // 2 + 10,   # Center horizontally (to the right of the save confirm button)
        top_margin + 50,            # Distance from the top (aligned with save confirm button)
        150,                        # Width
        40                          # Height
    )

    font = pygame.font.Font(None, 36)
    large_font = pygame.font.Font(None, 48)

    save_message = ""
    save_message_time = 0
    is_saving = False

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
                    for key, rect in button_rects.items():
                        if rect.collidepoint(index_pos) and not rect.collidepoint(new_index_pos):
                            if current_time - last_button_press > button_cooldown:
                                button_pressed = key
                                last_button_press = current_time
                                play_sound('./audio/quick_click.wav')
                    
                    # Check for exit button
                    if exit_button_rect.collidepoint(index_pos) and not exit_button_rect.collidepoint(new_index_pos):
                        if current_time - last_button_press > button_cooldown:
                            play_sound('./audio/back.wav')
                            return  # Exit the text editor app
                    
                    # Check for save button
                    if save_button_rect.collidepoint(index_pos) and not save_button_rect.collidepoint(new_index_pos):
                        if current_time - last_button_press > button_cooldown:
                            is_saving = True
                            filename = ""
                            play_sound('./audio/save.wav')  # You'll need to add this sound file
                    
                    # Check for save confirm button
                    if is_saving and save_confirm_rect.collidepoint(index_pos) and not save_confirm_rect.collidepoint(new_index_pos):
                        if current_time - last_button_press > button_cooldown:
                            if filename:
                                full_filename = save_text_to_file(text, filename)
                                save_message = f"Saved to {full_filename}"
                                save_message_time = current_time
                                is_saving = False
                                play_sound('./audio/save.wav')
                    
                    # Check for cancel button
                    if is_saving and cancel_rect.collidepoint(index_pos) and not cancel_rect.collidepoint(new_index_pos):
                        if current_time - last_button_press > button_cooldown:
                            is_saving = False
                            play_sound('./audio/back.wav')
                    
                    index_pos = new_index_pos

        if button_pressed:
            if is_saving:
                if button_pressed == '<-':
                    filename = filename[:-1]
                elif button_pressed != 'SPACE' and len(filename) < 20:  # Limit filename length
                    filename += button_pressed
            else:
                if button_pressed == 'SPACE':
                    text += ' '
                elif button_pressed == '<-':
                    text = text[:-1]
                elif button_pressed == 'ENTER':
                    text += '\n'
                else:
                    text += button_pressed

        screen.fill(BLACK)

        # Get and display camera frame
        # frame = camera_manager.get_frame()
        # if frame is not None:
        #     frame_surface = pygame.surfarray.make_surface(frame)
        #     screen.blit(frame_surface, (0, 0))

        # Draw text area
        text_lines = text.split('\n')
        text_y = 50
        for line in text_lines:
            text_surface = large_font.render(line, True, WHITE)
            text_rect = text_surface.get_rect(center=(SCREEN_SIZE[0] // 2, text_y))
            screen.blit(text_surface, text_rect)
            text_y += 50

        # Draw keyboard
        for key, rect in button_rects.items():
            pygame.draw.rect(screen, NAVY_BLUE, rect)
            pygame.draw.rect(screen, LIGHT_BLUE, rect, 2)
            key_text = font.render(key, True, WHITE)
            key_rect = key_text.get_rect(center=rect.center)
            screen.blit(key_text, key_rect)

        # Draw exit button
        pygame.draw.rect(screen, NAVY_BLUE, exit_button_rect)
        pygame.draw.rect(screen, LIGHT_BLUE, exit_button_rect, 2)
        exit_text = font.render("Exit", True, WHITE)
        exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
        screen.blit(exit_text, exit_text_rect)

        # Draw save button
        pygame.draw.rect(screen, NAVY_BLUE, save_button_rect)
        pygame.draw.rect(screen, LIGHT_BLUE, save_button_rect, 2)
        save_button_text = font.render("Save", True, WHITE)
        save_button_text_rect = save_button_text.get_rect(center=save_button_rect.center)
        screen.blit(save_button_text, save_button_text_rect)

        # Display save message
        if not is_saving and current_time - save_message_time < 3:  # Display message for 3 seconds
            message_surface = font.render(save_message, True, GREEN)
            message_rect = message_surface.get_rect(center=(SCREEN_SIZE[0] // 2, 20))
            screen.blit(message_surface, message_rect)

        # Draw filename input area and buttons when saving
        if is_saving:
            pygame.draw.rect(screen, NAVY_BLUE, filename_input_rect)
            pygame.draw.rect(screen, LIGHT_BLUE, filename_input_rect, 2)
            filename_text = font.render(filename, True, WHITE)
            filename_text_rect = filename_text.get_rect(center=filename_input_rect.center)
            screen.blit(filename_text, filename_text_rect)

            pygame.draw.rect(screen, NAVY_BLUE, save_confirm_rect)
            pygame.draw.rect(screen, LIGHT_BLUE, save_confirm_rect, 2)
            save_confirm_text = font.render("Save", True, WHITE)
            save_confirm_text_rect = save_confirm_text.get_rect(center=save_confirm_rect.center)
            screen.blit(save_confirm_text, save_confirm_text_rect)

            pygame.draw.rect(screen, NAVY_BLUE, cancel_rect)
            pygame.draw.rect(screen, LIGHT_BLUE, cancel_rect, 2)
            cancel_text = font.render("Cancel", True, WHITE)
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            screen.blit(cancel_text, cancel_text_rect)

        # Draw index finger pointer
        if index_pos:
            pygame.draw.circle(screen, RED, index_pos, 10)

        pygame.display.flip()
        pygame.time.delay(50)

if __name__ == '__main__':
    # This block is for testing the text editor app independently
    import sys
    sys.path.append('..')  # Add parent directory to Python path
    from camera_manager import CameraManager

    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption('Text Editor App')
    camera_manager = CameraManager('./M.npy', 1024, 768)
    run(screen, camera_manager)
    pygame.quit()
