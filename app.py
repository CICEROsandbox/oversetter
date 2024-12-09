import streamlit as st
from anthropic import Anthropic

st.title("Climate Science Translator 🌍")

# Set default to Norwegian->English
if 'direction' not in st.session_state:
    st.session_state.direction = "Norwegian → English"

direction = st.radio(
    "Select translation direction:",
    ["Norwegian → English", "English → Norwegian"],  # Changed order to make Norwegian->English first
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
                Provide only the translation with no additional text:

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
                    st.text_area(
                        f"{to_lang} Translation:",
                        value=response.content,
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
