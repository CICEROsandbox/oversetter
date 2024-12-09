import streamlit as st
from anthropic import Anthropic
import re

def clean_response(text):
    """Clean the translation response"""
    text = str(text)
    text = re.sub(r'\[TextBlock\(text=["\'](.*)["\'].*?\)\]', r'\1', text)
    text = text.replace("\\'", "'").replace('\\"', '"')
    text = re.sub(r',\s*type=\'text\'.*', '', text)
    text = text.replace('\\n', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_translation_and_analysis(text, from_lang, to_lang):
    """Get both translation and analysis"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # First get the translation
        translation_prompt = f"""Translate this {from_lang} text to {to_lang}. 
        Provide only the plain translation text without any formatting or metadata:

        {text}"""
        
        translation_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": translation_prompt}]
        )
        
        translation = clean_response(translation_response.content)
        
        # Then get the analysis
        analysis_prompt = f"""Analyze this translation from {from_lang} to {to_lang}:

        Original: {text}
        Translation: {translation}

        Provide brief insights about:
        1. Key terminology choices
        2. Cultural considerations
        3. Climate science specific considerations
        4. Potential alternative translations for key terms
        5. Suggestions for improvement

        Format your response in clear bullet points."""
        
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        
        return translation, analysis_response.content
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, None

st.title("Climate Science Translator 🌍")

# Set default to Norwegian->English
if 'direction' not in st.session_state:
    st.session_state.direction = "Norwegian → English"

direction = st.radio(
    "Select translation direction:",
    ["Norwegian → English", "English → Norwegian"],
    horizontal=True,
    key='direction'
)

from_lang = "Norwegian" if direction.startswith("Norwegian") else "English"
to_lang = "English" if direction.startswith("Norwegian") else "Norwegian"

input_text = st.text_area(
    f"Enter {from_lang} text:",
    height=150,
    key='input'
)

if st.button("Translate", type="primary", key='translate_button'):
    if input_text:
        with st.spinner("Translating..."):
            translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang)
            
            if translation:
                # Show translation
                st.subheader(f"{to_lang} Translation")
                st.text_area(
                    "",
                    value=translation,
                    height=150,
                    key='output',
                    label_visibility="collapsed"
                )
                
                # Show analysis in expander
                with st.expander("See translation analysis and suggestions"):
                    st.markdown(analysis)
    else:
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
