# user_app.py
import streamlit as st
import requests
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode, WebRtcStreamerContext
import av
import sounddevice as sd
import logging
import traceback

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

API_URL = "http://127.0.0.1:8000"

# Function to list available audio input devices accurately with debugging
def list_audio_devices():
    devices = sd.query_devices()
    input_devices = [
        f"{i}: {device['name']}" for i, device in enumerate(devices) if device['max_input_channels'] > 0
    ]
    if not input_devices:
        st.error("No audio input devices detected. Please check your microphone settings.")
    return input_devices

class AudioProcessor(AudioProcessorBase):
    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        # Process the audio frame here if needed
        return frame

st.sidebar.title("User Navigation")
page = st.sidebar.radio("Go to", ["User Chatbot"])

if page == "User Chatbot":
    st.title("User Chatbot")
    st.write("Interact with the chatbot.")
    input_type = st.radio("Select input type:", ["Text", "Voice", "Image"])

    if input_type == "Text":
        user_input = st.text_input("Enter your message:")
        if st.button("Send"):
            try:
                response = requests.post(
                    f"{API_URL}/chat/",
                    json={"message": user_input, "customer_name": "User"}  # Send data as JSON
                )
                if response.ok:
                    res_json = response.json()
                    actions = res_json.get('actions', [])
                    recommendation = res_json.get('recommendation', {})

                    st.subheader("Actions to be taken")
                    if actions:
                        for action in actions:
                            st.write(f"**Type:** {action.get('type', 'Unknown')}")
                            st.write(f"**Description:** {action.get('description', 'No description available')}")
                            st.write("---")
                    else:
                        st.write("No actions available.")

                    st.subheader("Recommendation")
                    solution = recommendation.get('solution', 'No solution available')
                    steps = recommendation.get('steps', [])

                    st.write(f"**Solution:** {solution}")
                    if steps:
                        st.write("**Steps:**")
                        for i, step in enumerate(steps, start=1):
                            st.write(f"{i}. {step}")
                    else:
                        st.write("No steps available.")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Unable to connect to the backend server. Please ensure the server is running.")
                
    elif input_type == "Voice":
        # Initialize webrtc_ctx and combined_audio in session state
        if "webrtc_ctx" not in st.session_state:
            st.session_state["webrtc_ctx"] = None
        if "combined_audio" not in st.session_state:
            st.session_state["combined_audio"] = b""
        if "audio_device" not in st.session_state:
            st.session_state["audio_device"] = None

        # List available audio devices with debugging
        available_devices = list_audio_devices()
        if not available_devices:
            st.error("No audio input devices found. Please ensure your microphone is connected and enabled.")
            logging.error("No audio input devices detected. Please check microphone connection and permissions.")
        else:
            selected_device = st.selectbox("Select Audio Input Device:", available_devices)
            st.session_state["audio_device"] = selected_device.split(": ")[0]  # Extract device index
            logging.debug(f"Selected audio device: {selected_device}")

        if st.button("Start Listening"):
            if not st.session_state.get("audio_device"):
                st.error("Please select an audio input device before starting.")
            else:
                try:
                    logging.debug(f"Attempting to start WebRTC with device: {st.session_state['audio_device']}")
                    st.session_state["webrtc_ctx"] = webrtc_streamer(
                        key="voice-recorder",
                        mode=WebRtcMode.SENDONLY,
                        audio_processor_factory=AudioProcessor,
                        async_processing=True,
                        media_stream_constraints={"audio": {"deviceId": {"exact": st.session_state["audio_device"]}}},
                        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                        audio_receiver_size=20  # Increased receiver size to handle larger queues
                    )
                    st.session_state["listening"] = True
                    logging.debug("WebRTC started successfully.")
                except Exception as e:
                    error_details = traceback.format_exc()
                    logging.error(f"Error accessing audio input: {e}\nDetails: {error_details}")
                    st.error("Unable to access audio input. Please check your device settings and permissions.")

        if st.button("Stop Listening"):
            st.session_state["listening"] = False

        # Show listening status
        if st.session_state.get("listening", False):
            st.write("Listening...")
            logging.debug("Listening state active.")

            if st.session_state["webrtc_ctx"] and st.session_state["webrtc_ctx"].audio_receiver:
                try:
                    logging.debug("Attempting to retrieve audio frames.")
                    audio_frames = st.session_state["webrtc_ctx"].audio_receiver.get_frames(timeout=1)
                    for frame in audio_frames:
                        st.session_state["combined_audio"] += frame.to_ndarray().tobytes()

                    if st.session_state["combined_audio"]:
                        st.write("Audio detected. Processing...")
                        st.text("[Voice-to-text translation placeholder]")
                        logging.debug("Audio successfully processed.")
                    else:
                        st.warning("No voice detected. Please ensure your microphone is working and selected correctly.")
                        logging.debug("No audio detected in frames.")
                except Exception as e:
                    error_details = traceback.format_exc()
                    logging.error(f"Error during audio processing: {e}\nDetails: {error_details}")
                    st.error("An error occurred while processing audio. Please try again.")
            else:
                st.warning("Unable to access audio input. Please check your device settings.")
                logging.debug("WebRTC context or audio receiver not available.")

        # Send button
        if st.button("Send"):
            if not st.session_state.get("listening", False):
                st.write("Processing your voice input...")
                response = requests.post(
                    f"{API_URL}/submit_ticket/",
                    data={"customer_name": "User"},
                    files={"voice": ("recording.wav", st.session_state["combined_audio"], "audio/wav")}
                )
                if response.ok:
                    res_json = response.json()
                    actions = res_json.get('AI Response', {}).get('actions', [])
                    recommendation = res_json.get('AI Response', {}).get('recommendation', {})

                    st.subheader("Actions")
                    if actions:
                        for action in actions:
                            st.write(f"**Type:** {action.get('type', 'Unknown')}\n**Description:** {action.get('description', 'No description available')}\n")
                    else:
                        st.write("No actions available.")

                    st.subheader("Recommendation")
                    solution = recommendation.get('solution', 'No solution available')
                    steps = recommendation.get('steps', [])

                    st.write(f"**Solution:** {solution}")
                    if steps:
                        st.write("**Steps:**")
                        for i, step in enumerate(steps, start=1):
                            st.write(f"{i}. {step}")
                    else:
                        st.write("No steps available.")
                else:
                    st.error("Error submitting voice file")
            else:
                st.warning("Please stop listening before sending.")
                
    elif input_type == "Image":
        image_file = st.file_uploader("Upload an image:", type=["png", "jpg", "jpeg"])
        if st.button("Send Image"):
            if image_file:
                response = requests.post(
                    f"{API_URL}/submit_ticket/",
                    data={"customer_name": "User"},
                    files={"image": image_file}
                )
                if response.ok:
                    res_json = response.json()
                    actions = res_json.get('AI Response', {}).get('actions', [])
                    recommendation = res_json.get('AI Response', {}).get('recommendation', {})

                    st.subheader("Actions")
                    if actions:
                        for action in actions:
                            st.write(f"**Type:** {action.get('type', 'Unknown')}")
                            st.write(f"**Description:** {action.get('description', 'No description available')}")
                            st.write("---")
                    else:
                        st.write("No actions available.")

                    st.subheader("Recommendation")
                    solution = recommendation.get('solution', 'No solution available')
                    steps = recommendation.get('steps', [])

                    st.write(f"**Solution:** {solution}")
                    if steps:
                        st.write("**Steps:**")
                        for i, step in enumerate(steps, start=1):
                            st.write(f"{i}. {step}")
                    else:
                        st.write("No steps available.")
                else:
                    st.error("Error submitting image")
            else:
                st.warning("Please upload an image.")
