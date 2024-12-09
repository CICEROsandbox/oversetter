import streamlit as st
from anthropic import Anthropic
import re

def clean_text(text):
    """Clean text formatting"""
    # Convert to string if needed
    text = str(text)
    
    # Remove any "Here is the translation..." prefix
    text = re.sub(r'^.*?(?=In the|I f)', '', text, flags=re.DOTALL)
    
    # Remove [TextBlock] artifacts
    text = re.sub(r'\[TextBlock\(text=[\'"](.*)[\'"].*?\)\]', r'\1', text)
    
    # Remove quotes and backslashes
    text = re.sub(r'[\'"\\]', '', text)
    
    # Replace 'nn' between sentences with proper spacing
    text = re.sub(r'(?<!\.)\s*\.\s*n+\s*(?=[A-Z])', '. ', text)
    
    # Clean up extra spaces and periods
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.+', '.', text)
    text = text.strip()
    
    return text

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

                Provide brief analysis in these sections:
                
                Key Terms:
                • List 2-3 key translation pairs
                
                Challenges:
                • Note 1-2 specific translation challenges
                
                Suggestions:
                • Provide 1-2 concrete improvement ideas"""
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
                    
                    # Show analysis directly
                    st.subheader("Translation Analysis")
                    st.text_area(
                        label="Translation analysis",
                        value=analysis,
                        height=200,
                        label_visibility="collapsed",
                        key="analysis_area"
                    )
        else:
            st.warning("Please enter text to translate")

    st.caption("Created by CICERO • Powered by Claude API")

if __name__ == "__main__":
    main()
