import streamlit as st
from anthropic import Anthropic

# Page config
st.set_page_config(
    page_title="Climate Science Translator",
    page_icon="🌍",
    layout="centered"
)

def translate_text(text, from_lang, to_lang):
    """Basic translation function"""
    try:
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        prompt = f"""You are translating from {from_lang} to {to_lang}.
        Translate only the following text, with no additional comments:

        {text}"""
        
        response = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# UI
st.title("Climate Science Translator 🌍")

direction = st.radio(
    "Select translation direction:",
    ["English → Norwegian", "Norwegian → English"],
    horizontal=True
)

from_lang = "English" if direction.startswith("English") else "Norwegian"
to_lang = "Norwegian" if direction.startswith("English") else "English"

st.subheader(f"{from_lang} Text")
input_text = st.text_area(
    "Enter text to translate:",
    height=150,
    label_visibility="collapsed"
)

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
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
