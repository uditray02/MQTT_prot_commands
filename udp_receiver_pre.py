#!/usr/bin/env python
import cv2
import socket
import numpy as np

class Stream_receiver:
    def __init__(self, host="0.0.0.0", port=1883, buffer_size=65536):
        # UDP setup
        self.server_address = (host, port)
        self.buffer_size = buffer_size

        # Create a UDP socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(self.server_address)

        print(f"Listening on {host}:{port}")

    def receive_and_display(self):
        while True:
            try:
                # Receive the frame data
                data, addr = self.udp_socket.recvfrom(self.buffer_size)

                # Decode the received frame
                np_data = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

                if frame is not None:
                    # Display the frame
                    cv2.imshow("UDP Video Stream", frame)

                    # Close the window on pressing 'q'
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    print("Failed to decode frame")
            except Exception as e:
                print(f"Error receiving frame: {e}")
                break

        # Clean up
        self.udp_socket.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Initialize and start the receiver
    receiver = Stream_receiver(host="0.0.0.0", port=1883)  # Listening on all interfaces, port 1883
    receiver.receive_and_display()
