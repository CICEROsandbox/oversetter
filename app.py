import streamlit as st
from anthropic import Anthropic

def clean_output(text):
    """Clean any formatted text output"""
    return str(text).strip()

def get_translation_and_analysis(text, from_lang, to_lang):
    """Get translation and structured analysis"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Get translation
        translation_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": f"Translate this from {from_lang} to {to_lang}. Provide only the translation:\n\n{text}"}
            ]
        )
        
        # Get analysis
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": f"""Analyze this translation pair and provide brief bullet points about:

                Original: {text}
                Translation: {translation_response.content}
                
                Organize your analysis into these sections:
                1. Key Terms: Important terminology translations (2-3 key terms)
                2. Challenges: Main translation difficulties (1-2 points)
                3. Alternative Options: Other possible translations (1-2 suggestions)
                4. Brief Improvement Notes (if any)

                Keep each bullet point short and focused."""}
            ]
        )
        
        return clean_output(translation_response.content), clean_output(analysis_response.content)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, None

st.title("Climate Science Translator 🌍")

# Default to Norwegian->English
direction = st.radio(
    "Select translation direction:",
    ["Norwegian → English", "English → Norwegian"],
    horizontal=True,
    index=0  # This makes Norwegian->English the default
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
        with st.spinner("Translating..."):
            translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang)
            
            if translation:
                # Show translation
                st.subheader(f"{to_lang} Translation")
                st.text_area(
                    "",
                    value=translation,
                    height=150,
                    label_visibility="collapsed"
                )
                
                # Show analysis directly
                st.subheader("Translation Analysis")
                st.write(analysis)
    else:
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
