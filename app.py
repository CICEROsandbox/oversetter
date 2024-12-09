import streamlit as st
from anthropic import Anthropic
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Climate Science Translator",
    page_icon="🌍",
    layout="centered"
)

def load_reference_text():
    """Load IPCC parallel text for reference"""
    try:
        df = pd.read_csv('data/ipcc_parallel_text (1).csv')
        # Clean and prepare reference text
        df = df[['english', 'norwegian']].dropna()
        return df
    except Exception as e:
        st.error(f"Error loading reference text: {e}")
        return None

def create_translation_prompt(text, from_lang, to_lang, reference_df):
    """Create prompt with IPCC reference examples"""
    # Get a few relevant reference examples
    examples = ""
    if reference_df is not None:
        for _, row in reference_df.head(3).iterrows():
            examples += f"\nExample {from_lang}: {row[from_lang.lower()]}\n"
            examples += f"Example {to_lang}: {row[to_lang.lower()]}\n"

    prompt = f"""You are translating climate science content from {from_lang} to {to_lang}.
    Use these IPCC translation examples for reference and terminology:
    {examples}
    
    Translate this text, maintaining scientific accuracy and IPCC style:
    {text}
    """
    return prompt

def translate_text(text, from_lang, to_lang):
    """Translate text using Claude API with IPCC reference"""
    try:
        # Load reference text
        reference_df = load_reference_text()
        
        # Create prompt with examples
        prompt = create_translation_prompt(text, from_lang, to_lang, reference_df)
        
        # Get translation
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return str(message.content)
        
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
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
    height=150,
    label_visibility="collapsed"
)

# Translation button
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
