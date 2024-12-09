import streamlit as st
from anthropic import Anthropic

# Page configuration
st.set_page_config(
    page_title="Climate Science Translator",
    page_icon="🌍",
    layout="centered"
)

@st.cache_data
def translate_text(text, from_lang, to_lang):
    """Translate text using Claude API with caching"""
    if not text:
        return None
        
    try:
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        prompt = f"""Translate the following {from_lang} climate science text to {to_lang}. 
        Maintain scientific accuracy and use appropriate climate science terminology:

        {text}
        """
        
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        # Extract the content as a string
        return str(message.content)
    except Exception as e:
        st.error(f"An error occurred during translation. Please try again.")
        return None

# Main UI
st.title("Climate Science Translator 🌍")

# Translation direction selector
direction = st.radio(
    "Select translation direction:",
    ["English → Norwegian", "Norwegian → English"],
    horizontal=True,
    key='direction'
)

# Set languages based on direction
from_lang = "English" if direction.startswith("English") else "Norwegian"
to_lang = "Norwegian" if direction.startswith("English") else "English"

# Input text area
st.subheader(f"{from_lang} Text")
input_text = st.text_area(
    "Enter text to translate:",
    height=150,
    key='input'
)

# Translation button
if st.button("Translate", type="primary"):
    if input_text:
        with st.spinner("Translating..."):
            translation = translate_text(input_text, from_lang, to_lang)
            if translation:
                st.subheader(f"{to_lang} Translation")
                st.text_area(
                    "Translation:",
                    value=translation,
                    height=150,
                    disabled=True,
                    key='output'
                )
                
                # Ensure translation is a string before encoding
                if isinstance(translation, str):
                    st.download_button(
                        label="Download Translation",
                        data=translation.encode('utf-8'),
                        file_name=f"translation_{to_lang.lower()}.txt",
                        mime="text/plain",
                        key='download'
                    )
                else:
                    st.error("Unable to prepare download. Please try translating again.")
    else:
        st.warning("Please enter some text to translate")

# Sidebar
with st.sidebar:
    st.header("About")
    st.write("Specialized translator for climate science content")
    
    # Example texts
    examples = {
        "English": """Climate change impacts are already more widespread and severe than expected. 
Future risks will increase with every increment of global warming.""",
        "Norwegian": """Klimaendringenes konsekvenser er allerede mer omfattende og alvorlige enn forventet. 
Fremtidige risikoer vil øke med hver økning i global oppvarming."""
    }
    
    if st.button("Load Example"):
        current_lang = "English" if direction.startswith("English") else "Norwegian"
        st.session_state['input'] = examples[current_lang]
        st.rerun()

st.markdown("---")
st.caption("Created by CICERO • Powered by Claude API")
