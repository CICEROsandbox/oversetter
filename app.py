import streamlit as st
from anthropic import Anthropic
import re

def clean_output(text):
    """Clean any formatted text output"""
    # Remove TextBlock and type='text' formatting
    text = re.sub(r'\[TextBlock\(text=[\'"]?(.*?)[\'"]?,\s*type=\'text\'\)\]', r'\1', str(text))
    # Remove escaped characters and extra whitespace
    text = text.replace('\\n', ' ').replace('\n\n', '\n')
    text = text.replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text)
    # Remove any remaining formatting artifacts
    text = re.sub(r',\s*type=\'text\'\)?$', '', text)
    return text.strip()

def format_analysis(analysis):
    """Format analysis into clean sections"""
    sections = {
        "Key Terminology": [],
        "Translation Challenges": [],
        "Alternative Options": [],
        "Suggestions for Improvement": []
    }
    
    # Clean and parse the content
    content = clean_output(analysis)
    
    # Extract points for each section
    for section in content.split('\n'):
        section = section.strip()
        if section:
            if "Fattige land" in section or "developing countries" in section:
                sections["Key Terminology"].append(section)
            elif "challenge" in section.lower() or "difficult" in section.lower():
                sections["Translation Challenges"].append(section)
            elif "could also be" in section or "alternative" in section.lower():
                sections["Alternative Options"].append(section)
            elif "suggest" in section.lower() or "consider" in section.lower():
                sections["Suggestions for Improvement"].append(section)
    
    # Format into markdown
    formatted = "## Translation Analysis\n\n"
    for title, points in sections.items():
        if points:
            formatted += f"### {title}\n"
            for point in points:
                formatted += f"- {point}\n"
            formatted += "\n"
    
    return formatted

def get_translation_and_analysis(text, from_lang, to_lang):
    """Get translation and analysis"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Get translation
        translation_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": f"Translate this from {from_lang} to {to_lang}. Provide only the translation with no additional text:\n\n{text}"}
            ]
        )
        translation = clean_output(translation_response.content)
        
        # Get analysis
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": f"""Analyze this translation:
                Original: {text}
                Translation: {translation}
                
                Provide brief analysis in these sections:
                • Key Terminology: Important term translations
                • Translation Challenges: Difficult aspects
                • Alternative Options: Other possible translations
                • Suggestions for Improvement: Brief improvement ideas

                Keep each point concise and focus on terminology and clarity."""}
            ]
        )
        analysis = format_analysis(analysis_response.content)
        
        return translation, analysis
        
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
    key='input',
    label_visibility="collapsed"
)

if st.button("Translate", type="primary", key='translate_button'):
    if input_text:
        with st.spinner("Translating..."):
            translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang)
            
            if translation:
                st.subheader(f"{to_lang} Translation")
                st.text_area(
                    "",
                    value=translation,
                    height=150,
                    key='output',
                    label_visibility="collapsed"
                )
                
                with st.expander("View Translation Analysis"):
                    st.markdown(analysis)
    else:
        st.warning("Please enter text to translate")

st.caption("Created by CICERO • Powered by Claude API")
