import streamlit as st
from anthropic import Anthropic
import pandas as pd
import requests
import re

def load_ipcc_examples():
    """Load IPCC parallel text from local file or GitHub"""
    # Try local file first
    try:
        df = pd.read_csv('data/ipcc_parallel_text.csv')
        st.success("✓ Using local IPCC reference text")
        return df[['english', 'norwegian']].head(3).to_dict('records')
    except Exception:
        # If local file fails, try GitHub
        try:
            url = "https://raw.githubusercontent.com/CICEROsandbox/oversetter/refs/heads/main/data/ipcc_parallel_text.csv"
            df = pd.read_csv(url)
            st.success("✓ Using IPCC reference text from GitHub")
            return df[['english', 'norwegian']].head(3).to_dict('records')
        except Exception as e:
            st.error("✗ Could not load IPCC reference text")
            return []

def clean_response(response):
    """Clean Claude's response"""
    text = str(response)
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
    text = text.replace("\'", "'").strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def translate_text(text, from_lang, to_lang):
    """Translate text using Claude API with IPCC examples"""
    try:
        # Load IPCC examples
        ipcc_examples = load_ipcc_examples()
        
        # Create example context
        example_text = ""
        if ipcc_examples:
            example_text = "Use these IPCC translation examples as reference:\n"
            for ex in ipcc_examples:
                example_text += f"\nEnglish: {ex['english']}\nNorwegian: {ex['norwegian']}\n"

        prompt = f"""You are a climate science translator. {example_text}

        Translate this text from {from_lang} to {to_lang}, 
        using IPCC terminology and style when applicable.
        Provide ONLY the translation with no additional text or formatting:

        {text}
        """
        
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
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
