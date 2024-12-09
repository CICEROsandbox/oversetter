import streamlit as st
from anthropic import Anthropic
import re

def clean_text(text):
    """Clean text formatting"""
    # Convert to string if needed
    text = str(text)
    
    # Remove any prefixes
    text = re.sub(r'^.*?(?=\w)', '', text, flags=re.DOTALL)
    
    # Fix capitalization after periods
    text = re.sub(r'\.(\s+)([a-z])', lambda m: f'.{m.group(1)}{m.group(2).upper()}', text)
    
    # Clean up extra spaces and periods
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.+', '.', text)
    
    return text.strip()

def format_analysis(analysis):
    """Structure the analysis output in markdown format"""
    sections = {
        "Key Terminology": [],
        "Challenges": [],
        "Suggestions": []
    }
    
    current_section = None
    current_points = []
    
    # Parse the analysis text
    for line in analysis.split('\n'):
        line = line.strip()
        if line.lower().startswith('key terminology'):
            current_section = "Key Terminology"
        elif line.lower().startswith('challenges'):
            current_section = "Challenges"
        elif line.lower().startswith('suggestions'):
            current_section = "Suggestions"
        elif line and current_section:
            current_points.append(line)
    
    # Format into markdown
    formatted = []
    for section, points in sections.items():
        if current_points:  # Only add sections that have content
            formatted.append(f"### {section}")
            formatted.extend([f"- {point}" for point in current_points])
            formatted.append("")  # Add spacing between sections
    
    return "\n".join(formatted)

def get_translation_and_analysis(input_text, from_lang, to_lang):
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
                "content": f"""Translate this from {from_lang} to {to_lang}. 
                Important:
                - Keep numbers in their original format
                - Ensure proper capitalization after periods
                - Just translate 'milliarder' to 'billion' when going from Norwegian to English
                - Provide a direct translation without any introduction or meta-text
                
                {input_text}"""
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
                "content": f"""Analyze this translation and provide structured feedback:

                Original: {input_text}
                Translation: {translation}

                Structure your response in these exact sections:

                Key Terminology:
                - List key terms with their translations in parentheses
                - Note any alternative translations where relevant
                
                Challenges:
                - Note specific translation challenges
                - Include examples with original and translated terms
                
                Suggestions:
                - Provide concrete improvements
                - Include specific examples"""
            }]
        )
        
        analysis = clean_text(analysis_response.content)
        analysis = format_analysis(analysis)
        
        return translation, analysis
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, None

def main():
    st.set_page_config(page_title="Climate Science Translator", layout="wide")

    st.title("Climate Science Translator 🌍")

    # Translation direction
    direction = st.radio(
        "Select translation direction:",
        ["Norwegian → English", "English → Norwegian"],
        horizontal=True,
        index=0
    )

    from_lang = "Norwegian" if direction.startswith("Norwegian") else "English"
    to_lang = "English" if direction.startswith("Norwegian") else "Norwegian"

    # Input text area
    st.subheader(f"{from_lang} Text")
    input_text = st.text_area(
        label="Input text",
        height=150,
        label_visibility="collapsed",
        key="input_area",
        placeholder=f"Enter {from_lang} text here..."
    )

    # Translation
    if st.button("Translate", type="primary"):
        if input_text:
            with st.spinner("Translating..."):
                translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang)
                
                if translation:
                    # Show translation
                    st.subheader(f"{to_lang} Translation")
                    st.text_area(
                        label="Translation output",
                        value=translation,
                        height=150,
                        label_visibility="collapsed",
                        key="output_area"
                    )
                    
                    # Show analysis with markdown formatting
                    st.subheader("Translation Analysis")
                    st.markdown(analysis)
        else:
            st.warning("Please enter text to translate")

    st.caption("Created by CICERO • Powered by Claude API")

if __name__ == "__main__":
    main()
