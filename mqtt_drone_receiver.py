import paho.mqtt.client as mqtt
import json
import cv2
import numpy as np
import sounddevice as sd
import pygame  # Add pygame for joystick handling

# Initialize joystick
pygame.init()
pygame.joystick.init()
joystick_connected = pygame.joystick.get_count() > 0
if joystick_connected:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Joystick connected: {joystick.get_name()}")
else:
    print("No joystick connected.")

# List to store all messages
received_messages = []

# Camera control variables
cam_pitch = 30  # Initial pitch value
cam_yaw = 0  # Initial yaw value

# Define callback for when the client receives a message
def on_message(client, userdata, message):
    payload = message.payload
    message_info = f"Received message from {message.topic}: {payload}"

    # Store message for later printing
    received_messages.append(message_info)

    try:
        if message.topic == "/drone/video":
            print(f"Raw Video Data Length: {len(payload)} bytes")
            img_array = np.frombuffer(payload, dtype=np.uint8)
            decoded_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if decoded_img is not None:
                cv2.imshow("Drone Video Feed", decoded_img)
                cv2.waitKey(1)
            else:
                print("Failed to decode video data.")

        elif message.topic == "/drone/gps":
            gps_data = json.loads(payload)
            print(f"GPS Data: lat={gps_data['lat']}, lon={gps_data['lon']}")

        elif message.topic == "/drone/battery":
            battery_data = json.loads(payload)
            print(f"Battery Level: {battery_data['voltage']}V, {battery_data['level']}%")

        elif message.topic == "/drone/velocity":
            velocity_data = json.loads(payload)
            print(f"Velocity: North={velocity_data['north']} m/s, East={velocity_data['east']} m/s, Down={velocity_data['down']} m/s")

        elif message.topic == "/drone/flight_time":
            flight_time_data = json.loads(payload)
            print(f"Flight Time: {flight_time_data['flight_time']} seconds")

        elif message.topic == "/drone/lte_signal":
            lte_data = json.loads(payload)
            print(f"LTE Signal Strength: {lte_data['signal_strength']}")

        else:
            print(f"Unrecognized topic {message.topic}: {payload}")

    except Exception as e:
        print(f"Error processing message from topic {message.topic}: {e}")


# Callback to capture and publish audio
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Audio status: {status}")
    audio_bytes = indata.tobytes()
    client.publish("/drone/audio", audio_bytes)

# Function to handle joystick input
def handle_joystick_input():
    global cam_pitch, cam_yaw
    pygame.event.pump()  # Update joystick state
    if joystick_connected:
        for button in range(joystick.get_numbuttons()):
            if joystick.get_button(button):  # If button is pressed
                if button == 0:  # Button 1
                    client.publish("/drone/commands", json.dumps({"action": "fly"}))
                    print("Button 1 pressed: Sending fly command")
                elif button == 1:  # Button 2
                    client.publish("/drone/commands", json.dumps({"action": "land"}))
                    print("Button 2 pressed: Sending land command")
                elif button == 2:  # Button 3
                    client.publish("/drone/commands", json.dumps({"action": "hover"}))
                    print("Button 3 pressed: Sending hover command")
                elif button == 3:  # Button 4
                    client.publish("/drone/commands", json.dumps({"action": "stop"}))
                    print("Button 4 pressed: Sending stop command")
                
                # Camera control for pitch and yaw
                elif button == 4:  # Button 5 (cam_pitch up)
                    if cam_pitch < 30:
                        cam_pitch += 1
                    client.publish("/drone/camera", json.dumps({"action": "cam_pitch", "value": cam_pitch}))
                    print(f"Button 5 pressed: Sending cam_pitch up command with value {cam_pitch}")
                elif button == 5:  # Button 6 (cam_pitch down)
                    if cam_pitch > -90:
                        cam_pitch -= 1
                    client.publish("/drone/camera", json.dumps({"action": "cam_pitch", "value": cam_pitch}))
                    print(f"Button 6 pressed: Sending cam_pitch down command with value {cam_pitch}")
                elif button == 6:  # Button 7 (cam_yaw left)
                    if cam_yaw > 0:
                        cam_yaw -= 1
                    client.publish("/drone/camera", json.dumps({"action": "cam_yaw", "value": cam_yaw}))
                    print(f"Button 7 pressed: Sending cam_yaw left command with value {cam_yaw}")
                elif button == 7:  # Button 8 (cam_yaw right)
                    if cam_yaw < 270:
                        cam_yaw += 1
                    client.publish("/drone/camera", json.dumps({"action": "cam_yaw", "value": cam_yaw}))
                    print(f"Button 8 pressed: Sending cam_yaw right command with value {cam_yaw}")

# Create MQTT client
client = mqtt.Client()
client.on_message = on_message
client.connect("3.110.177.25", 1883)
client.subscribe("/drone/video")
client.subscribe("/drone/gps")
client.subscribe("/drone/battery")
client.subscribe("/drone/velocity")
client.subscribe("/drone/flight_time")
client.subscribe("/drone/lte_signal")

client.loop_start()

print("Capturing and publishing audio...")
sample_rate = 44100  # 44.1 kHz
channels = 1  # Mono

with sd.InputStream(samplerate=sample_rate, channels=channels, callback=audio_callback):
    try:
        while True:  # Main loop
            handle_joystick_input()
            sd.sleep(10)  # Small delay to prevent excessive CPU usage
    except KeyboardInterrupt:
        print("Stopping program.")
        client.loop_stop()  # Stop MQTT loop
        client.disconnect()  # Disconnect from MQTT broker
        pygame.quit()  # Clean up pygame resources

        # Print all stored messages after termination
        print("\nAll MQTT messages received and processed:")
        for message in received_messages:
            print(message)
