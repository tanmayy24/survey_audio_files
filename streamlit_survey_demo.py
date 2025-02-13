import streamlit as st
from streamlit_survey_main.streamlit_survey import StreamlitSurvey
import pandas as pd
import os
import random
from pydub import AudioSegment

# Load prompts
prompts_df = pd.read_csv('prompts.csv')  # CSV contains audiocap_id, youtube_id, start_time, caption

# Paths to audio files from 3 models
model_folders = {
    "Model O": "model_original",
    "Model QB": "model_quantized_best",
    "Model QF": "model_quantized_fast"
}

# Randomly select 10 prompts
selected_prompts = prompts_df.sample(n=5, random_state=42).reset_index(drop=True)

# Generate 30 (Prompt, Audio) pairs, 10 per model
audio_samples = []
for model_name, folder in model_folders.items():
    for _, row in selected_prompts.iterrows():
        audiocap_id = str(row["audiocap_id"])
        prompt = row["caption"]
        audio_path = os.path.join(folder, f"{audiocap_id}.wav")

        if os.path.exists(audio_path):
            audio_samples.append({
                "model": model_name,
                "prompt": prompt,
                "audiocap_id": audiocap_id,
                "audio_path": audio_path
            })

# Shuffle the 30 audio samples for random order
random.shuffle(audio_samples)

# Function to trim audio to the first 10 seconds
def trim_audio(audio_path):
    audio = AudioSegment.from_wav(audio_path)
    trimmed_audio = audio[:10000]  # Take the first 10 seconds (10,000 ms)
    temp_trimmed_path = f"{audio_path}_trimmed.wav"
    trimmed_audio.export(temp_trimmed_path, format="wav")
    return temp_trimmed_path

survey = StreamlitSurvey()

with survey.pages(len(audio_samples) + 1) as page:

    # -----------------------------------------------------------
    # PAGE 0: INTRO/INSTRUCTIONS PAGE
    # -----------------------------------------------------------
    if page.current == 0:
        st.title("🎵 Generated Audio Quality Survey")
        st.markdown("### **Instructions**")
        st.markdown("""
        - 🎧 Use **headphones** for the best experience.
        - 🔊 Ensure your **computer sound is on**.
        - 🚪 Take the survey in a **quiet environment**.

        You will hear **15 audio samples**, each paired with a text description. 
        For each question, you will listen to one sample and rate how well it matches the description.
        ...  
        
        **Rating Scale:**  
        - **No Relation**  
        - **Barely Related**  
        - **Somewhat Related**  
        - **Very Related**  
        - **Perfectly Related**  

        🚀 **Let's begin!** Click **Next** to start.
        """, unsafe_allow_html=True)

        if st.button("Next"):
            page.next()

    # -----------------------------------------------------------
    # PAGES 1..N: PROMPTS + AUDIO + RATING
    # -----------------------------------------------------------
    elif page.current <= len(audio_samples):
        # Get current (Prompt, Audio) pair
        sample_index = page.current - 1
        sample = audio_samples[sample_index]
        prompt = sample["prompt"]
        original_audio_path = sample["audio_path"]
        model_name = sample["model"]
        audiocap_id = sample["audiocap_id"]

        # Ensure the audio file exists
        if not os.path.exists(original_audio_path):
            st.error(f"Audio file for {model_name} (ID: {audiocap_id}) not found.")
        else:
            # Trim audio to first 10 seconds
            trimmed_audio_path = trim_audio(original_audio_path)

            # Display prompt
            st.subheader(f"Description: {prompt}")

            # Display audio
            st.audio(trimmed_audio_path, format="audio/wav")

            # Rating selection
            rating_key = f"Q{sample_index}_AudiocapID={audiocap_id}_Model={model_name}"
            rating = survey.selectbox(
                "How well does the audio match the description?",
                options=["----", "No relation", "Barely related", 
                         "Somewhat related", "Very related", "Perfectly related"],
                id=rating_key
            )

            # "Next" button - Enforce rating
            if st.button("Next"):
                if rating == "----" or rating is None:
                    st.warning("⚠️ Please select a rating before proceeding.")
                    st.stop()  # <-- Stop execution so Streamlit won't advance
                else:
                    page.next()

    # -----------------------------------------------------------
    # LAST PAGE: SUBMIT/DOWNLOAD RESULTS
    # -----------------------------------------------------------
    else:
        st.markdown(":warning: **Final Step:** Please download your responses and submit them.")
        survey.download_button(
            "Download Survey Data", 
            file_name='audio_survey_results.json',
            use_container_width=True
        )
