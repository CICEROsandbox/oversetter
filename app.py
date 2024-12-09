import streamlit as st
from anthropic import Anthropic
import re

def clean_text(text):
    """Aggressively clean any formatting"""
    # First remove TextBlock wrapper
    text = re.sub(r'\[TextBlock\(text=[\'"](.*)[\'"].*?\)\]', r'\1', str(text))
    # Remove any remaining formatting
    text = re.sub(r'[\'"\\]', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_analysis(text, translation):
    """Get simple analysis without formatting"""
    client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0,
        messages=[{
            "role": "user",
            "content": f"""Analyze this translation pair:

            Original: {text}
            Translation: {translation}

            Provide a simple bulletted analysis with these headings only:
            
            Key Terms
            - list 2-3 key term translations
            
            Challenges
            - list 1-2 main challenges
            
            Suggestions
            - list 1-2 brief suggestions
            
            No additional text or formatting."""
        }]
    )
    
    return clean_text(response.content)

st.title("Climate Science Translator 🌍")

direction = st.radio(
    "Select translation direction:",
    ["Norwegian → English", "English → Norwegian"],
    horizontal=True,
    index=0
)

from_lang = "Norwegian" if direction.startswith("Norwegian") else "English"
to_lang = "English" if direction.startswith("Norwegian") else "Norwegian"

st.subheader(f"{from_lang} Text")
input_text = st.text_area(
    "",
    height=150,
    label_visibility="collapsed"
)

if st.button("Translate", type="primary"):
    if input_text:
        try:
            client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            
            # Get translation
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"Translate this from {from_lang} to {to_lang}. Provide only the direct translation:\n\n{text}"
                }]
            )
            
            translation = clean_text(response.content)
            
            # Show translation
            st.subheader(f"{to_lang} Translation")
            st.text_area(
                "",
                value=translation,
                height=150,
                label_visibility="collapsed"
            )
            
            # Get and show analysis
            st.subheader("Translation Analysis")
            analysis = get_analysis(input_text, translation)
            st.write(analysis)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
