import cv2
from detection import AccidentDetectionModel
import numpy as np
import os
import winsound
import threading
import time
import tkinter as tk
from twilio.rest import Client
from PIL import Image, ImageTk  # Import PIL modules for image handling
from logger import get_logger
logger = get_logger()

emergency_timer = None
alarm_triggered = False  # Flag to track if an alarm has been triggered

model = AccidentDetectionModel("model.json", "model_weights.keras")
font = cv2.FONT_HERSHEY_SIMPLEX

def save_accident_photo(frame):
    try:
        current_date_time = time.strftime("%Y-%m-%d-%H%M%S")
        directory = "accident_photos"
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = f"{directory}/{current_date_time}.jpg"
        cv2.imwrite(filename, frame)
        logger.info(f"Accident photo saved: {filename}")
    except Exception as e:
        logger.error(f"Error saving accident photo: {e}")

def call_ambulance():
    try:
        account_sid = "your_twilio_account_sid"
        auth_token = "your_twilio_account_auth_token"
        client = Client(account_sid, auth_token)
        
        call = client.calls.create(
            url="twilio_handler_url",  # Sample TwiML URL
            to="sender_number",  # add verified ambulance number 
            from_="receiver_number"
        )
        logger.info(f"Ambulance call initiated: {call.sid}")
    except Exception as e:
        logger.error(f"Error calling ambulance: {e}")
def show_alert_message():
    def on_call_ambulance():
        call_ambulance()
        alert_window.destroy()

    # Play the beep sound
    frequency = 2500  
    duration = 2000  
    winsound.Beep(frequency, duration)

    alert_window = tk.Tk()
    alert_window.title("Alert")
    alert_window.geometry("500x250")  # Adjust window size to fit the GIF and message box
    alert_label = tk.Label(alert_window, text="Alert: Accident Detected!\n\nIs the Accident Critical?", fg="black", font=("Helvetica", 16))
    alert_label.pack()

    # Load and display the GIF
    gif_path =   "" # Replace with the actual path to your GIF
    gif = Image.open(gif_path)
    resized_gif = gif.resize((150, 100), Image.BICUBIC)  # Use Image.BICUBIC for resizing

    try:
        global gif_image  # Create a global variable to hold the reference to the image object
        gif_image = ImageTk.PhotoImage(resized_gif)
        gif_label = tk.Label(alert_window, image=gif_image)
        gif_label.pack()
    except Exception as e:
        logger.error(f"Error loading GIF: {e}")


    call_ambulance_button = tk.Button(alert_window, text="Call Ambulance", command=on_call_ambulance)
    call_ambulance_button.pack()

    cancel_button = tk.Button(alert_window, text="Cancel", command=alert_window.destroy)
    cancel_button.pack()

    alert_window.mainloop()
    
def start_alert_thread():
    alert_thread = threading.Thread(target=show_alert_message)
    alert_thread.daemon = True  # Set the thread as daemon so it doesn't block the main thread
    alert_thread.start()

def startapplication():
    global alarm_triggered
    try:
        logger.info("Application started")

        video = cv2.VideoCapture("test_video_path")
        logger.info("Video source opened")

        while True:
            ret, frame = video.read()
            if not ret:
                logger.warning("No more frames to read")
                break

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            roi = cv2.resize(gray_frame, (250, 250))

            pred, prob = model.predict_accident(roi[np.newaxis, :, :])

            if pred == "Accident" and not alarm_triggered:
                prob = round(prob[0][0] * 100, 2)
                logger.info(f"Accident detected with confidence {prob}%")

                if prob > 99:
                    save_accident_photo(frame)
                    alarm_triggered = True
                    start_alert_thread()
                    logger.info("Alert thread started")

                cv2.rectangle(frame, (0, 0), (280, 40), (0, 0, 0), -1)
                cv2.putText(
                    frame,
                    pred + " " + str(prob),
                    (20, 30),
                    font,
                    1,
                    (255, 255, 0),
                    2
                )

            if cv2.waitKey(33) & 0xFF == ord('q'):
                logger.info("Application stopped by user")
                return

            cv2.imshow('Video', frame)

    except Exception as e:
        logger.critical(f"Application crashed: {e}")


if __name__ == '__main__':
    startapplication()

