import streamlit as st
from streamlit_survey_main.streamlit_survey import StreamlitSurvey
import pandas as pd
import os
import random

# Load prompts
prompts_df = pd.read_csv('prompts.csv')  # CSV contains audiocap_id, youtube_id, start_time, caption

# Paths to audio files
baseline_folder = "baseline_audio"
generated_folder = "generated_audio"

# Ensure only 10 prompts are used
num_questions = min(10, len(prompts_df))
selected_prompts = prompts_df.sample(n=num_questions, random_state=42).reset_index(drop=True)

survey = StreamlitSurvey()

with survey.pages(num_questions + 1) as page:

    if page.current == 0:
        st.session_state['disable_next'] = False
        st.title("Audio Quality Comparison Survey 🎵")
        st.markdown("<h5>Instructions</h5>", unsafe_allow_html=True)
        st.markdown("""
        Please:
        - 🎧 Use **headphones** for the best audio experience.
        - 🔊 Make sure your **computer sound is on**.
        - 🚪 Take the survey in a **quiet environment**.

        You will be given a **prompt** and two audio samples. Please listen to both and select which one matches the prompt **better**, or choose "Both sound similar". 

        Thank you for participating!
        """, unsafe_allow_html=True)
    
    else:
        # Get current prompt details
        row = selected_prompts.iloc[page.current - 1]
        audiocap_id = str(row["audiocap_id"])  # Convert to string for filename matching
        prompt = row["caption"]

        # Construct file paths
        baseline_audio_path = os.path.join(baseline_folder, f"{audiocap_id}.wav")
        generated_audio_path = os.path.join(generated_folder, f"{audiocap_id}.wav")

        # Check if files exist before proceeding
        if not os.path.exists(baseline_audio_path) or not os.path.exists(generated_audio_path):
            st.error(f"Audio files for {audiocap_id} not found.")
        else:
            # Display prompt
            st.subheader(f"Prompt: {prompt}")

            # Display audio options
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Audio 1 (Baseline Model)**")
                st.audio(baseline_audio_path, format="audio/wav")

            with col2:
                st.markdown("**Audio 2 (Generated Model)**")
                st.audio(generated_audio_path, format="audio/wav")

            # User selection
            st.markdown("### Which audio matches the prompt better?")
            result = survey.selectbox(
                "Choose an option:", 
                options=["----", "Audio 1 (Baseline)", "Audio 2 (Generated)", "Both sound similar"],
                id=f"Q{page.current-1}_AudiocapID={audiocap_id}"
            )

            if result == '----':
                st.warning("Please select an option before proceeding.")
            else:
                st.session_state['disable_next'] = False

        # Last page: Save and submit results
        if page.current == num_questions:
            st.markdown(":warning: **Final Step:** Please download your responses and submit them.")

            survey.download_button("Download Survey Data", file_name='audio_survey_results.json', use_container_width=True)
