import streamlit as st
from anthropic import Anthropic

def clean_translation(text):
    """Clean the translation response"""
    return str(text).strip()

def format_analysis(raw_analysis):
    """Format analysis into clean markdown sections"""
    # Remove any TextBlock formatting and special characters
    text = str(raw_analysis)
    text = text.replace('\n\n', '\n').replace('\\n', '\n')
    text = text.replace('\t', ' ').replace('• ', '- ')
    
    # Remove any remaining special formatting
    import re
    text = re.sub(r'\[TextBlock.*?\]', '', text)
    text = re.sub(r'type=.*?text.*?\}', '', text)
    text = re.sub(r'\\+[a-z]', ' ', text)
    
    # Create clean markdown sections
    sections = []
    sections.append("### Translation Analysis\n")
    
    if "Key Terms:" in text:
        sections.append("**Key Terminology**")
        terms = text.split("Key Terms:")[1].split("Challenges:")[0]
        for term in terms.split("•"):
            if term.strip():
                sections.append(f"- {term.strip()}")
    
    if "Challenges:" in text:
        sections.append("\n**Translation Challenges**")
        challenges = text.split("Challenges:")[1].split("Alternatives:")[0]
        for challenge in challenges.split("•"):
            if challenge.strip():
                sections.append(f"- {challenge.strip()}")
    
    if "Alternatives:" in text:
        sections.append("\n**Alternative Options**")
        alts = text.split("Alternatives:")[1].split("Suggestions:")[0]
        for alt in alts.split("•"):
            if alt.strip():
                sections.append(f"- {alt.strip()}")
    
    if "Suggestions:" in text:
        sections.append("\n**Suggestions for Improvement**")
        suggestions = text.split("Suggestions:")[1]
        for suggestion in suggestions.split("•"):
            if suggestion.strip():
                sections.append(f"- {suggestion.strip()}")
    
    return "\n".join(sections)

def get_translation_and_analysis(text, from_lang, to_lang):
    """Get translation and analysis"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Get translation
        translation_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"Translate this from {from_lang} to {to_lang}. Provide only the translation:\n\n{text}"
            }]
        )
        
        translation = clean_translation(translation_response.content)
        
        # Get analysis
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Analyze this translation:
                Original: {text}
                Translation: {translation}
                
                Provide brief analysis in these categories:
                • Key Terms: Important terminology and vocabulary choices
                • Challenges: Any difficult aspects of the translation
                • Alternatives: Other possible translations for key terms
                • Suggestions: Brief ideas for improvement

                Keep each point concise."""
            }]
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
