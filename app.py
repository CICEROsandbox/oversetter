import streamlit as st
from anthropic import Anthropic
import re

def clean_text(text: str) -> str:
    """Clean text with improved regex handling"""
    text = str(text)
    text = re.sub(r'TextBlock\(text=[\'"](.*?)[\'"]\)', r'\1', text)
    text = re.sub(r'\\n|\\r', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.(\s+)([a-z])', lambda m: f'.{m.group(1)}{m.group(2).upper()}', text)
    return text.strip()

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str):
    """Get translation and analysis with improved analysis prompt"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Get translation
        translation_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user", 
                "content": f"Translate this from {from_lang} to {to_lang}. Provide only the translation without any additional text:\n\n{input_text}"
            }]
        )
        
        translation = clean_text(translation_response.content)
        
        # Get analysis with more specific prompt
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Compare these texts and provide a brief analysis:

                Original: {input_text}
                Translation: {translation}

                Focus on:
                1. Important terminology translations (e.g., technical terms, key phrases)
                2. Any challenging aspects of the translation
                3. Suggestions for improvement if any

                Format your response in clear sections with bullet points."""
            }]
        )
        
        analysis = clean_text(analysis_response.content)
        
        if not analysis.strip():
            analysis = "Analysis unavailable. Please try again."
            
        return translation, analysis
        
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None, None

def main():
    st.set_page_config(page_title="Climate Science Translator", layout="wide")

    st.markdown('<h1 style="font-size: 2.5rem; font-weight: bold;">Climate Science Translator 🌍</h1>', unsafe_allow_html=True)

    direction = st.radio(
        "Select translation direction:",
        ["Norwegian → English", "English → Norwegian"],
        horizontal=True,
        label_visibility="collapsed"
    )

    from_lang = "Norwegian" if direction.startswith("Norwegian") else "English"
    to_lang = "English" if direction.startswith("Norwegian") else "Norwegian"

    st.subheader(f"{from_lang} Text")
    input_text = st.text_area(
        label="Input text",
        height=150,
        label_visibility="collapsed",
        key="input_area",
        placeholder=f"Enter {from_lang} text here..."
    )

    if st.button("Translate", type="primary"):
        if input_text:
            with st.spinner("Translating..."):
                translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang)
                
                if translation:
                    st.subheader(f"{to_lang} Translation")
                    st.text_area(
                        label="Translation output",
                        value=translation,
                        height=150,
                        label_visibility="collapsed",
                        key="output_area"
                    )
                    
                    st.subheader("Translation Analysis")
                    # Display analysis with markdown formatting
                    for line in analysis.split('\n'):
                        if line.strip():
                            # Check if it's a section header
                            if any(section in line.lower() for section in ['terminology', 'challenges', 'suggestions']):
                                st.markdown(f"**{line.strip()}**")
                            else:
                                st.markdown(f"{line.strip()}")

        else:
            st.warning("Please enter text to translate")

    st.caption("Created by CICERO • Powered by Claude API")

if __name__ == "__main__":
    main()
