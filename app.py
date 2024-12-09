import streamlit as st
from anthropic import Anthropic
import re

def clean_text(text: str) -> str:
    """Clean text with improved regex handling"""
    # Convert to string and clean TextBlock artifacts
    text = str(text)
    text = re.sub(r'TextBlock\(text=[\'"](.*?)[\'"]\)', r'\1', text)
    
    # Remove escape characters and extra spaces
    text = re.sub(r'\\n|\\r', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Ensure proper capitalization after periods
    text = re.sub(r'\.(\s+)([a-z])', lambda m: f'.{m.group(1)}{m.group(2).upper()}', text)
    
    return text.strip()

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str):
    """Get translation and analysis with improved error handling"""
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
        
        # Get analysis
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Analyze this translation. Provide only brief bullet points for each section:

                Original: {input_text}
                Translation: {translation}

                Key Terms:
                - List main terms and their translations
                
                Challenges:
                - List specific translation challenges
                
                Suggestions:
                - List concrete improvement ideas"""
            }]
        )
        
        analysis = clean_text(analysis_response.content)
        return translation, analysis
        
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None, None

def main():
    # Page config
    st.set_page_config(
        page_title="Climate Science Translator",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .stRadio [role=radiogroup] {
            gap: 0;
        }
        .stRadio [role=radio] {
            background-color: #f0f2f6;
            padding: 10px 20px;
            border-radius: 5px;
            margin-right: 10px;
        }
        .stRadio [aria-checked=true] {
            background-color: #00acee;
            color: white;
        }
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
        .section-header {
            font-size: 1.5rem;
            font-weight: bold;
            margin: 1rem 0;
        }
        .analysis-section {
            background-color: white;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title with emoji
    st.markdown('<h1 class="main-header">Climate Science Translator 🌍</h1>', unsafe_allow_html=True)

    # Translation direction with custom radio styling
    direction = st.radio(
        "Select translation direction:",
        ["Norwegian → English", "English → Norwegian"],
        horizontal=True,
        label_visibility="collapsed"
    )

    from_lang = "Norwegian" if direction.startswith("Norwegian") else "English"
    to_lang = "English" if direction.startswith("Norwegian") else "Norwegian"

    # Input section
    st.markdown(f'<h2 class="section-header">{from_lang} Text</h2>', unsafe_allow_html=True)
    
    input_text = st.text_area(
        label="Input text",
        height=150,
        label_visibility="collapsed",
        key="input_area",
        placeholder=f"Enter {from_lang} text here..."
    )

    # Translate button with custom styling
    if st.button("Translate", type="primary", key="translate_button"):
        if input_text:
            with st.spinner("Translating..."):
                translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang)
                
                if translation:
                    # Translation output
                    st.markdown(f'<h2 class="section-header">{to_lang} Translation</h2>', unsafe_allow_html=True)
                    st.text_area(
                        label="Translation output",
                        value=translation,
                        height=150,
                        label_visibility="collapsed",
                        key="output_area"
                    )
                    
                    # Analysis with better formatting
                    st.markdown('<h2 class="section-header">Translation Analysis</h2>', unsafe_allow_html=True)
                    
                    # Split analysis into sections and display with proper formatting
                    sections = analysis.split('\n')
                    current_section = None
                    
                    for section in sections:
                        if section.strip():
                            if section.startswith('Key Terms:'):
                                current_section = 'Key Terms'
                                st.markdown('**Key Terms:**')
                            elif section.startswith('Challenges:'):
                                current_section = 'Challenges'
                                st.markdown('**Challenges:**')
                            elif section.startswith('Suggestions:'):
                                current_section = 'Suggestions'
                                st.markdown('**Suggestions:**')
                            elif current_section and section.strip().startswith('-'):
                                st.markdown(section)
        else:
            st.warning("Please enter text to translate")

    st.caption("Created by CICERO • Powered by Claude API")

if __name__ == "__main__":
    main()
