import streamlit as st
from anthropic import Anthropic
import re

def clean_response(text):
    """Clean the translation response"""
    # Convert to string and remove outer formatting
    text = str(text)
    text = re.sub(r'\[TextBlock\(text=["\'](.*)["\'].*?\)\]', r'\1', text)
    
    # Remove escaped quotes
    text = text.replace("\\'", "'").replace('\\"', '"')
    
    # Remove type='text and other artifacts
    text = re.sub(r',\s*type=\'text\'.*', '', text)
    
    # Clean up newlines and spaces
    text = text.replace('\\n', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

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
            try:
                client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                
                prompt = f"""Translate this {from_lang} text to {to_lang}. 
                Provide only the plain translation text without any formatting or metadata:

                {input_text}"""
                
                response = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    temperature=0,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                if response and response.content:
                    # Clean the response before displaying
                    clean_translation = clean_response(response.content)
                    st.text_area(
                        f"{to_lang} Translation:",
                        value=clean_translation,
                        height=150,
                        key='output'
                    )
                else:
                    st.error("No translation received")
            except Exception as e:
                st.error(f"Translation error: {str(e)}")
    else:
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
