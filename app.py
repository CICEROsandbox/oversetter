import streamlit as st
from anthropic import Anthropic

st.title("Climate Science Translator 🌍")

direction = st.radio(
    "Select translation direction:",
    ["English → Norwegian", "Norwegian → English"],
    horizontal=True
)

from_lang = "English" if direction.startswith("English") else "Norwegian"
to_lang = "Norwegian" if direction.startswith("English") else "English"

input_text = st.text_area(f"Enter {from_lang} text:", height=150)

if st.button("Translate"):
    if input_text:
        try:
            client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"Translate this from {from_lang} to {to_lang}: {input_text}"
                    }
                ]
            )
            
            st.text_area(f"{to_lang} Translation:", response.content, height=150)
        except Exception as e:
            st.error(f"Translation error: {str(e)}")
    else:
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
