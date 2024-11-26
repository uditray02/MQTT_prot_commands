#!/usr/bin/env python
import cv2
import threading
import socket
import queue
import time

class Stream_publisher:
    
    def __init__(self, video_address="video.mp4", start_stream=True, host="127.0.0.1", port=1883) -> None:
        # Set up UDP socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (host, port)
        self.video_source = video_address

        self.cam = cv2.VideoCapture(self.video_source)
        
        # Initial frame rate
        self.frame_rate = 10  # Target 10 frames per second
        self.prev_time = time.time()

        self.frame_queue = queue.Queue(maxsize=2)  # Limit the size to prevent excessive memory usage

        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.publish_thread = threading.Thread(target=self.publish_frames)

        if start_stream:
            self.capture_thread.start()
            self.publish_thread.start()

    def capture_frames(self):
        print(f"Capturing from video file: {self.video_source}")
        while True:
            ret, img = self.cam.read()
            if not ret:
                print("End of video or failed to read frame")
                break  # Exit if the video source is not available
            current_time = time.time()
            if (current_time - self.prev_time) >= (1. / self.frame_rate):
                self.prev_time = current_time
                if not self.frame_queue.full():
                    self.frame_queue.put(img)
                else:
                    # Drop the oldest frame if the queue is full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put(img)
                    except queue.Empty:
                        pass

    def publish_frames(self):
        print(f"Publishing video frames to {self.server_address}")
        while True:
            if not self.frame_queue.empty():
                img = self.frame_queue.get()
                img_str = cv2.imencode('.jpg', img)[1].tobytes()
                try:
                    self.client_socket.sendto(img_str, self.server_address)
                except Exception as e:
                    print(f"Failed to publish: {e}")

if __name__ == "__main__":
    video_file = "video.mp4"  # Path to the pre-recorded video
    publisher = Stream_publisher(video_address=video_file)  # Streaming from a video file to the receiver
