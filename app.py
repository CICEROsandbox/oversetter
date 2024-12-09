import streamlit as st
from anthropic import Anthropic
import re
from bs4 import BeautifulSoup
import html

def extract_html_content(html_text: str):
    """Extract text while preserving HTML structure"""
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Create a map of text pieces to their original HTML context
    text_map = {}
    
    for element in soup.find_all(text=True):
        if element.strip():
            # Store the text with its parent tag and attributes
            parent = element.parent
            tag_name = parent.name if parent and parent.name else None
            attrs = parent.attrs if parent and parent.attrs else {}
            text_map[element] = (tag_name, attrs)
    
    # Return both the plain text for translation and the mapping
    return ' '.join(text_map.keys()), text_map

def reconstruct_html(translated_text: str, text_map):
    """Reconstruct HTML with translated text"""
    soup = BeautifulSoup('', 'html.parser')
    
    # Split translated text back into pieces
    translated_pieces = translated_text.split('\n')
    original_pieces = list(text_map.keys())
    
    # Rebuild HTML structure
    for orig, trans in zip(original_pieces, translated_pieces):
        tag_name, attrs = text_map[orig]
        if tag_name:
            new_tag = soup.new_tag(tag_name, **attrs)
            new_tag.string = trans.strip()
            soup.append(new_tag)
        else:
            soup.append(trans.strip())
    
    return str(soup)

def clean_text(text: str) -> str:
    """Clean text while preserving HTML"""
    # Remove TextBlock artifacts
    text = re.sub(r'TextBlock\(text=[\'"](.*?)[\'"]\)', r'\1', text)
    # Clean up spaces while preserving HTML
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str, is_html: bool = False):
    """Get translation and analysis with HTML support"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        if is_html:
            # Extract text while preserving HTML structure
            text_for_translation, html_map = extract_html_content(input_text)
        else:
            text_for_translation = input_text
        
        # Get translation
        translation_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user", 
                "content": f"""Translate this from {from_lang} to {to_lang}. 
                Keep the same structure and formatting as the original.
                Translate only the text content, not any HTML tags.
                
                {text_for_translation}"""
            }]
        )
        
        translated_text = clean_text(translation_response.content)
        
        if is_html:
            # Reconstruct HTML with translated text
            final_translation = reconstruct_html(translated_text, html_map)
        else:
            final_translation = translated_text
        
        # Get analysis
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Analyze this translation:

                Original: {text_for_translation}
                Translation: {translated_text}

                Provide brief analysis focusing on:
                1. Key terminology translations
                2. Any challenging aspects
                3. Suggestions for improvement"""
            }]
        )
        
        analysis = clean_text(analysis_response.content)
        return final_translation, analysis
        
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

    # Add HTML toggle
    is_html = st.checkbox("Input contains HTML formatting", help="Select this if your input includes HTML tags")

    st.subheader(f"{from_lang} Text")
    input_text = st.text_area(
        label="Input text",
        height=150,
        label_visibility="collapsed",
        key="input_area",
        placeholder=f"Enter {from_lang} text (with or without HTML)..."
    )

    if st.button("Translate", type="primary"):
        if input_text:
            with st.spinner("Translating..."):
                translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang, is_html)
                
                if translation:
                    st.subheader(f"{to_lang} Translation")
                    
                    # Show raw HTML option
                    show_raw = st.checkbox("Show raw HTML")
                    
                    if show_raw or not is_html:
                        st.text_area(
                            label="Translation output",
                            value=translation,
                            height=150,
                            label_visibility="collapsed",
                            key="output_area"
                        )
                    else:
                        # Display rendered HTML
                        st.markdown(translation, unsafe_allow_html=True)
                    
                    st.subheader("Translation Analysis")
                    st.markdown(analysis)
        else:
            st.warning("Please enter text to translate")

    st.caption("Created by CICERO • Powered by Claude API")

if __name__ == "__main__":
    main()
