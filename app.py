import streamlit as st
from anthropic import Anthropic
import pandas as pd
import re

def clean_response(response):
    """Aggressively clean Claude's response"""
    # Convert to string
    text = str(response)
    
    # Remove all common prefixes/formatting
    patterns_to_remove = [
        r'\[TextBlock\(text=\'.*?\'.*?\)\]',
        r'Here is the .* translation.*?:',
        r'Translation to .*?:',
        r'\\n',
        r'\n\n-\s*',
        r'^-\s*'
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text)
    
    # Clean up quotes and spaces
    text = text.replace("\'", "'").strip()
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text

def translate_text(text, from_lang, to_lang):
    """Translate text using Claude API"""
    try:
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        prompt = f"""Translate this text from {from_lang} to {to_lang}. 
        Provide ONLY the translation with no additional text, no explanations, and no formatting:

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
        
        return clean_response(message.content)
        
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None

# UI Components
st.title("Climate Science Translator 🌍")

# Translation direction
direction = st.radio(
    "Select translation direction:",
    ["English → Norwegian", "Norwegian → English"],
    horizontal=True
)

from_lang = "English" if direction.startswith("English") else "Norwegian"
to_lang = "Norwegian" if direction.startswith("English") else "English"

# Input text
st.subheader(f"{from_lang} Text")
input_text = st.text_area(
    "Enter text to translate:",
    height=150,
    label_visibility="collapsed"
)

# Translation
if st.button("Translate", type="primary"):
    if input_text:
        with st.spinner("Translating..."):
            translation = translate_text(input_text, from_lang, to_lang)
            if translation:
                st.subheader(f"{to_lang} Translation")
                st.text_area(
                    "Translation result",
                    value=translation,
                    height=150,
                    label_visibility="collapsed"
                )
    else:
        st.warning("Please enter some text to translate")

st.caption("Created by CICERO • Powered by Claude API")
