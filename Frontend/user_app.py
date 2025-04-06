# user_app.py
import streamlit as st
import requests
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av

API_URL = "http://127.0.0.1:8000"

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
        st.write("You can either upload a voice file or record your voice in real-time.")

        # Option to upload a voice file
        voice_file = st.file_uploader("Upload a voice file:", type=["wav", "mp3"])

        # Option to record voice in real-time
        st.write("Or record your voice:")
        webrtc_ctx = webrtc_streamer(key="voice-recorder", mode="sendonly", audio_processor_factory=AudioProcessor)

        if st.button("Send Voice"):
            if voice_file:
                response = requests.post(
                    f"{API_URL}/submit_ticket/",
                    data={"customer_name": "User"},
                    files={"voice": voice_file}
                )
                if response.ok:
                    st.write(f"Response: {response.json().get('message')}")
                else:
                    st.error("Error submitting voice file")
            elif webrtc_ctx and webrtc_ctx.audio_receiver:
                st.write("Recording submitted successfully.")
                # Save or process the recorded audio here
            else:
                st.warning("Please upload a voice file or use the recording option.")
                
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
                    st.write(f"Response: {response.json().get('message')}")
                else:
                    st.error("Error submitting image")
            else:
                st.warning("Please upload an image.")
