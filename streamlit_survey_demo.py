import streamlit as st
from streamlit_survey_main.streamlit_survey import StreamlitSurvey
import pandas as pd
import os
import random
from pydub import AudioSegment

# -----------------------------------------------------------
# 1) DATA LOADING / PROMPT SELECTION
# -----------------------------------------------------------
prompts_df = pd.read_csv('prompts.csv')  # must have columns: audiocap_id, youtube_id, start_time, caption

model_folders = {
    "Model O": "model_original",
    "Model QB": "model_quantized_best",
    "Model QF": "model_quantized_fast"
}

# Randomly select N prompts (change 5 -> 10 or your desired number)
selected_prompts = prompts_df.sample(n=5, random_state=42).reset_index(drop=True)

# Build our list of audio samples. We'll get 1 sample per prompt per model -> 3*N total.
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

# Shuffle them to get random order
random.shuffle(audio_samples)

# -----------------------------------------------------------
# 2) HELPER: TRIM AUDIO TO FIRST 10s
# -----------------------------------------------------------
def trim_audio(audio_path):
    audio = AudioSegment.from_wav(audio_path)
    trimmed_audio = audio[:10000]  # first 10 seconds (ms)
    temp_trimmed_path = f"{audio_path}_trimmed.wav"
    trimmed_audio.export(temp_trimmed_path, format="wav")
    return temp_trimmed_path

# -----------------------------------------------------------
# 3) INITIALIZE THE SURVEY
# -----------------------------------------------------------
survey = StreamlitSurvey()

# We'll have (total samples) + 1 pages: Page 0 for instructions, pages 1..N for each sample,
# then page N+1 for final submission.
num_pages = len(audio_samples) + 1

# NOTE: If 'nav=False' doesn't exist in your version, you must hide or override
# the built-in nav in another way (e.g., CSS or advanced hooking).
with survey.pages(num_pages, nav=False) as page:

    # -------------------------------------------------------
    # PAGE 0: INTRO/INSTRUCTIONS
    # -------------------------------------------------------
    if page.current == 0:
        st.title("🎵 Generated Audio Quality Survey")
        st.markdown("### **Instructions**")
        st.markdown("""
        - 🎧 Use **headphones** for the best experience.
        - 🔊 Ensure your **computer sound is on**.
        - 🚪 Take the survey in a **quiet environment**.

        You will hear **N audio samples**, each with a text description. 
        For each question, please rate **how well the audio matches the description**.

        **Rating Scale:**  
        - **No relation**  
        - **Barely related**  
        - **Somewhat related**  
        - **Very related**  
        - **Perfectly related**  

        When you're ready, click **Next** below.
        """, unsafe_allow_html=True)

        if st.button("Next"):
            page.next()

    # -------------------------------------------------------
    # PAGES 1..N: PROMPT + AUDIO + RATING
    # -------------------------------------------------------
    elif page.current <= len(audio_samples):
        # Which sample are we on?
        sample_index = page.current - 1
        sample = audio_samples[sample_index]

        prompt = sample["prompt"]
        original_audio_path = sample["audio_path"]
        model_name = sample["model"]
        audiocap_id = sample["audiocap_id"]

        # Double check the file path
        if not os.path.exists(original_audio_path):
            st.error(f"Audio file not found for {model_name} (Audiocap ID: {audiocap_id}).")
        else:
            # Trim audio to 10s
            trimmed_audio_path = trim_audio(original_audio_path)

            # Show the prompt
            st.subheader(f"Description: {prompt}")

            # Play the audio
            st.audio(trimmed_audio_path, format="audio/wav")

            # Provide rating question
            rating_key = f"Q{sample_index}_AudiocapID={audiocap_id}_Model={model_name}"
            rating = survey.selectbox(
                "How well does the audio match the description?",
                options=["----", "No relation", "Barely related", "Somewhat related", "Very related", "Perfectly related"],
                id=rating_key
            )

            # Provide Next button
            if st.button("Next"):
                # Enforce rating selection
                if rating == "----" or rating is None:
                    st.warning("⚠️ Please select a rating before proceeding.")
                    st.stop()  # Stop script execution here, user remains on the same page
                else:
                    # Rating is valid; go to next page
                    page.next()

    # -------------------------------------------------------
    # LAST PAGE: SUBMISSION / DOWNLOAD
    # -------------------------------------------------------
    else:
        st.markdown("**Final Step:** Please download your survey data and submit it.")
        survey.download_button(
            label="Download Survey Data",
            file_name="audio_survey_results.json",
            use_container_width=True
        )
        st.markdown("_Thank you for participating!_")
