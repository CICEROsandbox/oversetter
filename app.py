import streamlit as st
from anthropic import Anthropic
import pandas as pd
import requests
import re

@st.cache_data
def load_ipcc_examples():
    """Load and cache IPCC parallel text"""
    try:
        df = pd.read_csv('data/ipcc_parallel_text.csv')
        st.success("✓ Using local IPCC reference text")
        return df[['english', 'norwegian']].head(3).to_dict('records')
    except Exception:
        st.error("✗ Could not load IPCC reference text")
        return []

def clean_response(response):
    """Clean and validate Claude's response"""
    if not response:
        return None
        
    text = str(response)
    
    # Remove formatting
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
    
    # Clean up text
    text = text.replace("\'", "'")
    text = text.replace('\\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Validate we have actual content
    if len(text) < 1:
        return None
        
    return text

def translate_text(text, from_lang, to_lang):
    """Translate text using Claude API with validation"""
    if not text or len(text.strip()) < 1:
        st.error("No text provided for translation")
        return None
        
    try:
        # Load IPCC examples
        ipcc_examples = load_ipcc_examples()
        
        # Create prompt
        prompt = f"""Translate this text from {from_lang} to {to_lang}:

        {text}

        Guidelines:
        1. Provide ONLY the direct translation
        2. No explanations or metadata
        3. Maintain scientific accuracy
        4. Use climate science terminology correctly
        """
        
        if ipcc_examples:
            prompt += "\n\nReference examples:\n"
            for ex in ipcc_examples:
                prompt += f"\n{from_lang}: {ex[from_lang.lower()]}\n{to_lang}: {ex[to_lang.lower()]}\n"
        
        # Get translation
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        response = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Clean and validate response
        translation = clean_response(response.content)
        
        if not translation:
            st.error("Got empty translation response")
            return None
            
        return translation
        
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
                
                # Debug info
                if st.checkbox("Show debug info"):
                    st.write("Input length:", len(input_text))
                    st.write("Output length:", len(translation))
                    st.write("Translation successful")
    else:
        st.warning("Please enter some text to translate")

st.caption("Created by CICERO • Powered by Claude API")
