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
    """Extract JSON from text using regex and parsing"""
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
            "content": "Could not generate a guide for the specified location. Please try again."
        }
    ]

def generate_monument_guide(location, duration, topic_focus, language):
    """Generate monument guide using Gemini API"""
    model = genai.GenerativeModel('gemini-pro')
    
    # Average reading speed is about 150 words per minute
    duration_mapping = {
        "Synopsis": {"time": "a brief 10-30 second overview", "words": "25-75 words"},
        "Story": {"time": "a 30 second to 2 minute narrative", "words": "75-300 words"},
        "Long": {"time": "a comprehensive 2-5 minute explanation", "words": "300-750 words"}
    }

    topic_prompts = {
        "History": f"Create a chronological historical guide focusing on key events, dates, and historical significance",
        "Fun Facts": f"Share genuinely entertaining and humorous facts. Each segment should be a standalone fun fact that would make someone laugh or say 'wow, that's cool!' Include unusual anecdotes, quirky incidents, or amusing stories. Avoid generic descriptions.",
        "Surprising Facts": f"Share truly shocking or unexpected facts that most people don't know. Each segment should be a standalone revelation that would make someone say 'I can't believe that!' Focus on counterintuitive information, hidden secrets, or mind-blowing statistics. Avoid basic historical facts or common knowledge.",
        "Architecture": f"Provide detailed architectural insights focusing on design elements, construction techniques, and unique structural features"
    }

    language_prompt = f"Respond in {language}. "
    prompt = f"""{language_prompt}Create a {duration_mapping[duration]['time']} guide for {location}, \
    {topic_prompts[topic_focus]}. The content should be {duration_mapping[duration]['words']} to match the intended duration. \
    Respond EXACTLY in this JSON format:\n    [\n      {{\n        "title": "Segment Title",
        "content": "Detailed content about this aspect"
      }}
    ]\n    IMPORTANT: 
    1. Ensure valid JSON with proper escaping
    2. Maintain the specified word count in the content to match the duration
    3. For Fun Facts and Surprising Facts, each segment MUST be a standalone fact (not a description)
    4. The first segment should NOT be a general description but should directly address the chosen topic focus
    5. Make sure each fact is genuinely entertaining or surprising, not just informative"""

    try:
        response = model.generate_content(prompt)
        return extract_json(response.text)
    except Exception as e:
        st.error(f"Error generating guide: {e}")
        return [
            {
                "title": "Error",
                "content": str(e)
            }
        ]

# Update the generate_audio function
# def generate_audio(text, language_code='en-US', voice_name='en-US-Wavenet-D'):
#     """Generate audio from text using Google's Gemini 2.0 TTS."""
#     try:
#         # Define the audio configuration
#         audio_config = {
#             'voice': voice_name,
#             'language_code': language_code
#         }
        
#         # Generate the audio content
#         response = genai.generate_text(
#             prompt=text,
#             model='models/gemini-2.0-flash',
#             output_modality='AUDIO',
#             audio_config=audio_config
#         )
        
#         # Extract the audio content from the response
#         audio_content = response.result.audio
        
#         return audio_content
#     except Exception as e:
#         raise Exception(f"Error generating audio: {str(e)}")

def generate_audio(text, language):
    """Generate audio from text using OpenAI TTS"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
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

    with col1:
        duration_options = {
            "Synopsis (10-30 secs)": "Synopsis",
            "Story (30 secs - 2 mins)": "Story",
            "Long Story (2-5 mins)": "Long"
        }
        
        duration = st.selectbox(
            "Select Duration",
            list(duration_options.keys())
        )

        topic_focus = st.selectbox(
            "Select Topic Focus",
            ["History", "Fun Facts", "Surprising Facts", "Architecture"]
        )

    with col2:
        language = st.selectbox(
            "Select Language",
            ["English", "Spanish", "French", "Hindi"]
        )

    if st.button("Generate Guide"):
        if not location:
            st.warning("Please enter a monument location")
            return

        duration_type = duration_options[duration]

        with st.spinner('Generating monument guide...'):
            guides = generate_monument_guide(location, duration_type, topic_focus, language)

        if guides:
            for i, guide in enumerate(guides, 1):
                with st.expander(f"Segment {i}: {guide.get('title', 'Untitled')}"):
                    st.markdown(f"<div class='segment-title'>{guide.get('title', 'Untitled')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='segment-content'>{guide.get('content', 'No content')}</div>", unsafe_allow_html=True)

                    try:
                        audio_text = f"{guide.get('title')}. {guide.get('content')}"
                        audio_bytes = generate_audio(audio_text, language)
                        st.markdown(create_audio_player(audio_bytes), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error generating audio: {str(e)}")

if __name__ == "__main__":
    main()
