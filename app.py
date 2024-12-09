import streamlit as st
from anthropic import Anthropic
import re

def clean_text(text):
    """Clean text formatting"""
    # Convert to string if needed
    text = str(text)
    
    # Remove any "Here is the translation..." prefix
    text = re.sub(r'^.*?(?=In the|I f)', '', text, flags=re.DOTALL)
    
    # Remove [TextBlock] artifacts and type=text tags
    text = re.sub(r'\[TextBlock\(text=[\'"](.*)[\'"].*?\)\]', r'\1', text)
    text = re.sub(r', type=text\]', '', text)
    
    # Remove LaTeX-style formatting
    text = re.sub(r'\$.*?\$', '', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    
    # Fix ".n" artifacts
    text = re.sub(r'\.\s*n\s*(?=[A-Z-])', '. ', text)
    text = re.sub(r'\s*\.n\d+\s*', '. ', text)
    
    # Clean up extra spaces and periods
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.+', '.', text)
    
    return text.strip()

def display_analysis(analysis):
    """Format and display analysis in sections"""
    sections = [
        "Key Terminology:",
        "Translation Challenges:",
        "Suggested Improvements:",
        "Additional Notes:"
    ]
    
    # Split analysis into paragraphs
    paragraphs = [p.strip() for p in analysis.split('.') if p.strip()]
    
    # Display each paragraph with proper formatting
    for p in paragraphs:
        p = p.strip()
        if any(section in p for section in sections):
            st.write("---")
            st.write(f"**{p}**")
        else:
            st.write(p + ".")
            st.write("")

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
                "content": f"""Analyze this translation:

                Original: {input_text}
                Translation: {translation}

                Please provide a clear analysis with these sections:

                Key Terminology:
                • Point out important term translations
                • Note any terms that could be translated differently
                
                Translation Challenges:
                • Identify specific challenges in the text
                • Note any cultural or contextual considerations
                
                Suggested Improvements:
                • Offer specific suggestions for clearer translation
                • Note any structural improvements
                
                Additional Notes:
                • Comment on number formatting
                • Any other relevant observations

                Write in clear sentences without bullet points or special formatting."""
            }]
        )
        
        analysis = clean_text(analysis_response.content)
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
                    
                    # Show analysis with better formatting
                    st.subheader("Translation Analysis")
                    display_analysis(analysis)
        else:
            st.warning("Please enter text to translate")

    st.caption("Created by CICERO • Powered by Claude API")

if __name__ == "__main__":
    main()
