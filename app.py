import streamlit as st
from anthropic import Anthropic
import pandas as pd

def translate_text(text, from_lang, to_lang):
    """Simple translation function"""
    try:
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        prompt = f"""You are translating this {from_lang} text to {to_lang}.
        Provide only the translation, no other text:

        {text}"""
        
        response = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Get just the content
        translation = response.content
        
        if not translation:
            st.error("No translation received")
            return None
            
        return translation
        
    except Exception as e:
        st.error(f"Translation error: {e}")
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
                
                # Debug output
                with st.expander("Debug info"):
                    st.write("Input text:", input_text)
                    st.write("Raw response:", translation)
    else:
        st.warning("Please enter some text to translate")

st.caption("Created by CICERO • Powered by Claude API")
