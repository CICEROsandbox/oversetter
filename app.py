import streamlit as st
from anthropic import Anthropic
import re

def clean_text(text):
    """Clean any formatting"""
    text = re.sub(r'\[TextBlock\(text=[\'"](.*)[\'"].*?\)\]', r'\1', str(text))
    text = re.sub(r'[\'"\\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_translation_and_analysis(input_text, from_lang, to_lang):
    """Get translation and analysis"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Get translation
        translation_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user", 
                "content": f"Translate this from {from_lang} to {to_lang}:\n\n{input_text}"
            }]
        )
        
        translation = clean_text(translation_response.content)
        
        # Get analysis
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Analyze this translation:

                Original: {input_text}
                Translation: {translation}

                Provide analysis in these sections:
                
                Key Terms:
                - list 2-3 important terminology translations
                
                Challenges:
                - note 1-2 main translation challenges
                
                Suggestions:
                - provide 1-2 brief improvement ideas"""
            }]
        )
        
        analysis = clean_text(analysis_response.content)
        return translation, analysis
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, None

st.title("Climate Science Translator 🌍")

# Translation direction
direction = st.radio(
    "Select translation direction:",
    ["Norwegian → English", "English → Norwegian"],
    horizontal=True,
    index=0
)

from_lang = "Norwegian" if direction.startswith("Norwegian") else "English"
to_lang = "English" if direction.startswith("Norwegian") else "Norwegian"

# Input text area
st.subheader(f"{from_lang} Text")
input_text = st.text_area(
    label="Input text",  # Added label for accessibility
    height=150,
    label_visibility="collapsed",
    key="input_area"
)

# Translation
if st.button("Translate", type="primary"):
    if input_text:
        with st.spinner("Translating..."):
            translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang)
            
            if translation:
                # Show translation
                st.subheader(f"{to_lang} Translation")
                st.text_area(
                    label="Translation output",  # Added label for accessibility
                    value=translation,
                    height=150,
                    label_visibility="collapsed",
                    key="output_area"
                )
                
                # Show analysis
                st.subheader("Translation Analysis")
                st.text_area(
                    label="Translation analysis",  # Added label for accessibility
                    value=analysis,
                    height=200,
                    label_visibility="collapsed",
                    key="analysis_area"
                )
    else:
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
