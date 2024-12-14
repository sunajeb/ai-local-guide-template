import streamlit as st
import google.generativeai as genai
import json
import re
import base64
import os
from openai import OpenAI
import tempfile

# Retrieve API keys from the environment or Streamlit secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", st.secrets["OPENAI_API_KEY"])
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", st.secrets["GEMINI_API_KEY"])

# Validate API keys
if not OPENAI_API_KEY or not GEMINI_API_KEY:
    st.error("API keys are missing! Please ensure they are properly set in Streamlit Secrets.")

# Initialize OpenAI client with API key
client = OpenAI(api_key=OPENAI_API_KEY)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)


def extract_json(text):
    """
    Extract JSON from text using regex and parsing
    Handles various JSON formatting issues
    """
    text = text.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            json_match = re.search(r'\[{.*?}]', text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                json_text = json_text.replace("'", '"')
                return json.loads(json_text)
        except Exception:
            pass
    return [
        {
            "title": "Guide Generation Failed",
            "description": "Could not generate a guide for the specified location",
            "content": "Please try again or check your input."
        }
    ]

def generate_monument_guide(location, duration, topic_focus, language):
    """Generate monument guide using Gemini API"""
    model = genai.GenerativeModel('gemini-pro')
    duration_mapping = {
        "Synopsis": "a brief 10-30 second overview",
        "Story": "a 30 second to 2 minute narrative",
        "Long Story": "a comprehensive 2-5 minute explanation"
    }
    language_prompt = f"Respond in {language}. "
    prompt = f"""{language_prompt}Create a {duration_mapping[duration]} guide for {location} monument, \
    focusing primarily on {topic_focus}. \
    Respond EXACTLY in this JSON format:\n    [\n      {{\n        "title": "Segment Title",
        "description": "Short description of the segment",
        "content": "Detailed paragraph about this aspect of the monument"
      }}
    ]\n    IMPORTANT: Ensure valid JSON with proper escaping and maintain the specified duration in the content."""
    try:
        response = model.generate_content(prompt)
        return extract_json(response.text)
    except Exception as e:
        st.error(f"Error generating guide: {e}")
        return [
            {
                "title": "Error",
                "description": "Could not generate monument guide",
                "content": str(e)
            }
        ]

def generate_audio(text, voice_selection, language):
    """Generate audio from text using OpenAI TTS"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice_selection,
            input=text
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            response.stream_to_file(tmp_file.name)
            with open(tmp_file.name, 'rb') as audio_file:
                audio_bytes = audio_file.read()
            os.unlink(tmp_file.name)
            return audio_bytes
    except Exception as e:
        raise Exception(f"Error generating audio: {str(e)}")

def create_audio_player(audio_bytes):
    """Create an HTML audio player with the audio bytes"""
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_player = f"""
        <audio controls>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    """
    return audio_player

def main():
    st.set_page_config(page_title="AI Local Guide", page_icon="\U0001F3DB")
    st.markdown("""
        <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(to bottom, #e0f7fa, #e3f2fd);
            color: #333;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        .stSelectbox label {
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("\U0001F3DB AI Local Guide")

    location = st.text_input("Enter a Monument, Art Gallery, or Historical Site", placeholder="E.g., Eiffel Tower, Louvre Museum, Taj Mahal")
    col1, col2 = st.columns(2)

    # Voice mapping
    voice_map = {
        "Balanced and clear": "alloy",
        "Warm and rounded": "echo",
        "Authoritative": "fable",
        "Deep and powerful": "onyx",
        "Energetic and bright": "nova",
        "Gentle and soothing": "shimmer"
    }

    with col1:
        duration = st.selectbox(
            "Select Duration",
            ["Synopsis (10-30 secs)", "Story (30 secs - 2 mins)", "Long Story (2 mins- 5 mins)"],
            format_func=lambda x: x.split(" ")[0]
        )

        topic_focus = st.selectbox(
            "Select Topic Focus",
            ["History", "Fun Facts", "Surprising Facts", "Architecture"]
        )

    with col2:
        voice_description = st.selectbox(
            "Select Voice",
            list(voice_map.keys())
        )

        language = st.selectbox(
            "Select Language",
            ["English", "Spanish", "French", "Hindi"]
        )

    voice_selection = voice_map[voice_description]

    if st.button("Generate Guide"):
        if not location:
            st.warning("Please enter a monument location")
            return

        duration_type = duration.split(" ")[0]

        with st.spinner('Generating monument guide...'):
            guides = generate_monument_guide(location, duration_type, topic_focus, language)

        if guides:
            for i, guide in enumerate(guides, 1):
                with st.expander(f"Segment {i}: {guide.get('title', 'Untitled')}"):
                    st.markdown(f"**Description:** {guide.get('description', 'No description')}")
                    st.markdown(f"**Content:** {guide.get('content', 'No content')}\n")

                    try:
                        audio_text = f"{guide.get('title')}. {guide.get('description')}. {guide.get('content')}"
                        audio_bytes = generate_audio(audio_text, voice_selection, language)
                        st.markdown("**\U0001F50A Listen to Audio Guide:**")
                        st.markdown(create_audio_player(audio_bytes), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error generating audio: {str(e)}")

if __name__ == "__main__":
    main()
