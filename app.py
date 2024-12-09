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

def format_analysis(analysis):
    """Format the analysis response"""
    # Remove TextBlock formatting
    analysis = re.sub(r'\[TextBlock\(text=["\'](.*)["\'].*?\)\]', r'\1', str(analysis))
    # Remove other artifacts
    analysis = analysis.replace("\\'", "'").replace('\\"', '"')
    analysis = re.sub(r',\s*type=\'text\'.*', '', analysis)
    
    # Split into sections and clean up
    sections = analysis.split('\n\n')
    formatted = ""
    
    for section in sections:
        if ':' in section:
            title, content = section.split(':', 1)
            formatted += f"### {title.strip()}\n"
            # Convert bullet points to proper markdown
            points = content.split('\n-')
            for point in points:
                if point.strip():
                    formatted += f"- {point.strip()}\n"
            formatted += "\n"
    
    return formatted

def get_translation_and_analysis(text, from_lang, to_lang):
    """Get both translation and analysis"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Get translation
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
        
        # Get analysis
        analysis_prompt = f"""Analyze this translation:

        Original: {text}
        Translation: {translation}

        Provide brief analysis in these categories:
        • Key Terms: Important terminology choices and climate science vocabulary
        • Challenges: Any tricky parts of the translation
        • Alternatives: Other possible ways to translate key terms
        • Suggestions: Ideas for improving the translation

        Keep each bullet point brief and focused."""
        
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        
        return translation, format_analysis(analysis_response.content)
        
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
                
                # Show analysis in expander with markdown formatting
                with st.expander("Translation Analysis"):
                    st.markdown(analysis)
    else:
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
