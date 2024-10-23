import pygame
import cv2
import numpy as np
import torch
from PIL import Image
from datetime import datetime
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
from pygame import mixer
import sys

# Initialize Pygame
pygame.init()
SCREEN_SIZE = (1024, 768)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_BLUE = (173, 216, 230)
NAVY_BLUE = (20, 20, 40)

# Initialize the mixer
mixer.init()

# Initialize the model and processor
checkpoint = "vinvino02/glpn-nyu"
image_processor = AutoImageProcessor.from_pretrained(checkpoint)
model = AutoModelForDepthEstimation.from_pretrained(checkpoint)

def play_sound(file_path):
    try:
        mixer.music.load(file_path)
        mixer.music.play()
    except pygame.error as e:
        print(f"Error playing sound {file_path}: {e}")

def perform_depth_estimation(image):
    pixel_values = image_processor(image, return_tensors="pt").pixel_values

    with torch.no_grad():
        outputs = model(pixel_values)
        predicted_depth = outputs.predicted_depth

    prediction = torch.nn.functional.interpolate(
        predicted_depth.unsqueeze(1),
        size=image.size[::-1],
        mode="bicubic",
        align_corners=False,
    ).squeeze()
    output = prediction.numpy()

    min_depth = np.min(output)
    max_depth = np.max(output)
    print(f"Min depth: {min_depth}, Max depth: {max_depth}")

    output_normalized = (output - min_depth) / (max_depth - min_depth)
    output_normalized = (output_normalized * 255).astype("uint8")

    output_equalized = cv2.equalizeHist(output_normalized)
    depth_cv = np.array(output_equalized)

    depth_resized = cv2.resize(depth_cv, (image.width, image.height))
    depth_colored = cv2.applyColorMap(depth_resized, cv2.COLORMAP_JET)

    return depth_colored, depth_cv

def save_images(depth_map):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    depth_map_path = f'./scans/depth_map_{timestamp}.png'
    cv2.imwrite(depth_map_path, depth_map)
    print(f"Saved depth map as {depth_map_path}")

def run(screen, camera_manager):
    running = True
    depth_image = None
    scanning = False

    circle_radius = 55
    home_button_center = (35 + circle_radius, SCREEN_SIZE[1] - 35 - circle_radius)
    scan_button_rect = pygame.Rect((SCREEN_SIZE[0] // 2 - 140, SCREEN_SIZE[1] - 100, 280, 55))

    font = pygame.font.Font(None, 28)

    while running:
        if not camera_manager.update():
            continue

        transformed_landmarks = camera_manager.get_transformed_landmarks()
        index_pos = None
        if transformed_landmarks:
            for hand_landmarks in transformed_landmarks:
                index_pos = (int(hand_landmarks[8][0]), int(hand_landmarks[8][1]))  # INDEX_FINGER_TIP

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)

        if index_pos:
            if scan_button_rect.collidepoint(index_pos):
                scanning = True
                depth_image = None  # Clear the previous depth map

                play_sound('audio/drawing.wav')

                for y in range(0, SCREEN_SIZE[1], 20):
                    screen.fill(BLACK)
                    pygame.draw.line(screen, WHITE, (0, y), (SCREEN_SIZE[0], y), 5)
                    pygame.display.flip()
                    pygame.time.delay(10)

                screen.fill(BLACK)
                pygame.display.flip()

                play_sound('audio/quick_click.wav')

                ret, frame = camera_manager.cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_transformed = cv2.warpPerspective(frame_rgb, camera_manager.M, (SCREEN_SIZE[0], SCREEN_SIZE[1]))
                    image = Image.fromarray(frame_transformed)
                    depth_colored, depth_cv = perform_depth_estimation(image)

                    save_images(depth_cv)

                    depth_image = depth_colored

                scanning = False

            if (index_pos[0] - home_button_center[0])**2 + (index_pos[1] - home_button_center[1])**2 <= circle_radius**2:
                running = False

        if depth_image is not None:
            depth_surface = pygame.surfarray.make_surface(depth_image.transpose((1, 0, 2)))
            depth_surface = pygame.transform.scale(depth_surface, (SCREEN_SIZE[0], SCREEN_SIZE[1]))
            screen.blit(depth_surface, (0, 0))

        pygame.draw.rect(screen, BLACK, (0, SCREEN_SIZE[1] - 150, SCREEN_SIZE[0], 150))

        pygame.draw.rect(screen, NAVY_BLUE, scan_button_rect, border_radius=15)
        pygame.draw.rect(screen, LIGHT_BLUE, scan_button_rect, 5, border_radius=15)
        button_text = 'Scanning...' if scanning else 'Start Scan'
        text_surface = font.render(button_text, True, WHITE)
        text_rect = text_surface.get_rect(center=scan_button_rect.center)
        screen.blit(text_surface, text_rect)

        pygame.draw.circle(screen, NAVY_BLUE, home_button_center, circle_radius)
        pygame.draw.circle(screen, LIGHT_BLUE, home_button_center, circle_radius, 5)
        text_surface = font.render('Home', True, WHITE)
        text_rect = text_surface.get_rect(center=home_button_center)
        screen.blit(text_surface, text_rect)

        if index_pos:
            pygame.draw.circle(screen, LIGHT_BLUE, index_pos, 10, 3)

        pygame.display.flip()
        pygame.time.delay(1)

if __name__ == '__main__':
    from camera_manager import CameraManager  
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('Depth Estimation App')
    camera_manager = CameraManager('./M.npy', 1024, 768)
    run(screen, camera_manager)
