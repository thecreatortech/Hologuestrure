import cv2
import numpy as np
import mediapipe as mp

class CameraManager:
    def __init__(self, transformation_matrix_path, width, height):
        self.width = width
        self.height = height
        self.cap = cv2.VideoCapture(1)
        
        # Get the frame rate from the camera
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if not self.fps > 0:
            self.fps = 30  # Default to 30 FPS if the frame rate cannot be obtained

        self.M = np.load(transformation_matrix_path)
        
        # Initialize mediapipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False,
                                         max_num_hands=2,
                                         min_detection_confidence=0.1,
                                         min_tracking_confidence=0.1)
        self.mp_drawing = mp.solutions.drawing_utils

        self.frame = None
        self.results = None

        # Initialize VideoWriter for original and warped feeds
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out_original = cv2.VideoWriter('original_feed.avi', fourcc, self.fps, (int(self.cap.get(3)), int(self.cap.get(4))))
        # self.out_warped = cv2.VideoWriter('warped_feed.avi', fourcc, self.fps, (width, height))

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture frame")
            return False

        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run inference for hand detection
        self.results = self.hands.process(rgb_frame)

        # Draw hand landmarks on the frame
        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        # Save the original frame
        self.frame = frame

        # Warp the frame
        warped_frame = cv2.warpPerspective(frame, self.M, (self.width, self.height))
        
        # Draw hand landmarks on the warped frame
        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    warped_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        # Show the frames
        cv2.imshow("Camera View", frame)
        # cv2.imshow("Warped View", warped_frame)

        # Write the frames to the video files
        self.out_original.write(frame)
        # self.out_warped.write(warped_frame)

        return True

    def get_transformed_landmarks(self):
        if self.results and self.results.multi_hand_landmarks:
            transformed_landmarks = []
            for hand_landmarks in self.results.multi_hand_landmarks:
                # Extract landmark coordinates
                landmark_coords = []
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * self.frame.shape[1])
                    y = int(landmark.y * self.frame.shape[0])
                    landmark_coords.append([x, y])
                
                landmark_coords = np.array(landmark_coords, dtype=np.float32)

                # Apply M transformation to landmark coordinates
                transformed_coords = cv2.perspectiveTransform(np.array([landmark_coords]), self.M)[0]
                
                # Clip coordinates to be within the screen bounds
                transformed_coords = np.clip(transformed_coords, [0, 0], [self.width - 1, self.height - 1])
                transformed_landmarks.append(transformed_coords)

            return transformed_landmarks
        
        return None

    def release(self):
        self.cap.release()
        self.out_original.release()
        # self.out_warped.release()
        cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    transformation_matrix_path = 'M.npy'
    width, height = 1070, 700
    camera_manager = CameraManager(transformation_matrix_path, width, height)

    while True:
        if not camera_manager.update():
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera_manager.release()
