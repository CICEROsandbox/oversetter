import streamlit as st
from anthropic import Anthropic
import re

# Page configuration
st.set_page_config(
    page_title="Climate Science Translator",
    page_icon="🌍",
    layout="centered"
)

def clean_translation(response):
    """Clean up the translation response"""
    try:
        # Remove the formatting prefix
        cleaned = re.sub(r'.*?terminology:\s*\n*', '', str(response))
        # Remove any remaining [TextBlock...] formatting
        cleaned = re.sub(r'\[TextBlock\(.*?\)\]', '', cleaned)
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    except:
        return response

def translate_text(text, from_lang, to_lang):
    """Translate text using Claude API"""
    if not text:
        return None
        
    try:
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        prompt = f"""Translate this {from_lang} text to {to_lang}. 
        Provide ONLY the translation, with no additional text or context:

        {text}
        """
        
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return clean_translation(message.content)
    except Exception as e:
        st.error("Translation error. Please try again.")
        return None

# Main UI
st.title("Climate Science Translator 🌍")

# Translation direction selector
direction = st.radio(
    "Select translation direction:",
    ["English → Norwegian", "Norwegian → English"],
    horizontal=True
)

# Set languages based on direction
from_lang = "English" if direction.startswith("English") else "Norwegian"
to_lang = "Norwegian" if direction.startswith("English") else "English"

# Input text area
st.subheader(f"{from_lang} Text")
input_text = st.text_area(
    "Enter text to translate:",
    height=150
)

# Translation button
if st.button("Translate", type="primary"):
    if input_text:
        with st.spinner("Translating..."):
            translation = translate_text(input_text, from_lang, to_lang)
            if translation:
                st.subheader(f"{to_lang} Translation")
                st.text_area(
                    "",
                    value=translation,
                    height=150
                )
    else:
        st.warning("Please enter some text to translate")

st.caption("Created by CICERO • Powered by Claude API")
