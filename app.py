import streamlit as st
from anthropic import Anthropic
import re
from bs4 import BeautifulSoup
import requests
from html import unescape

def fetch_cicero_article(url: str) -> str:
    """Fetch article content from CICERO website."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content
        article_content = []
        
        # Get the title
        title = soup.find('h1')
        if title:
            article_content.append(str(title))
        
        # Select content areas
        content_areas = [
            'div.styles_textBlock___VSu1',
            'div.styles_articleHeader__RYxA_',
            'p',
            'figcaption',
            'h2, h3, h4, h5, h6'
        ]
        
        for selector in content_areas:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    article_content.append(str(element))
        
        if not article_content:
            raise ValueError("No content found in the article.")
            
        return '\n'.join(article_content)
    except Exception as e:
        raise ValueError(f"Error fetching article: {str(e)}")

def extract_translatable_content(html_content: str) -> list:
    """Extract translatable content from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    translatable_elements = []
    seen_text = set()

    for element in soup.find_all(string=True):
        if element.strip() and element.parent.name not in ['script', 'style']:
            text = element.strip()
            if text not in seen_text:
                seen_text.add(text)
                translatable_elements.append({
                    'html': str(element.parent),
                    'text': text,
                    'element': element
                })
    return translatable_elements

def clean_text(text) -> str:
    """Clean and normalize text."""
    if isinstance(text, list):  # Handle list input
        text = ' '.join([str(item) for item in text])
    elif not isinstance(text, str):
        text = str(text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str, preserve_html: bool = False):
    """Translate and analyze content."""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        if preserve_html:
            soup = BeautifulSoup(input_text, 'html.parser')
            
            # Create the translation prompt with clear instructions
            translation_prompt = f"""You are a professional translator specializing in {from_lang} to {to_lang} translation. 
            Translate the following text accurately while preserving any names, technical terms, and proper nouns. 
            Provide only the translation without any additional comments or explanations.
            
            Text to translate:
            {clean_text(input_text)}"""
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                system="You are a professional translator who provides accurate and natural-sounding translations.",
                messages=[{"role": "user", "content": translation_prompt}]
            )
            
            translated_text = clean_text(response.content)
            
            # Create HTML structure with both original and translated text
            translated_html = f"""
            <div class="translation-content">
                <div class="original-text">
                    <strong>Original ({from_lang})</strong><br>
                    {input_text}
                </div>
                <div class="translated-text">
                    <strong>Translation ({to_lang})</strong><br>
                    {translated_text}
                </div>
            </div>
            """
        else:
            # Handle plain text translation
            translation_prompt = f"""Translate this {from_lang} text to {to_lang}. Preserve any names, technical terms, and proper nouns.
            
            Text to translate:
            {input_text}"""
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                system="You are a professional translator who provides accurate and natural-sounding translations.",
                messages=[{"role": "user", "content": translation_prompt}]
            )
            translated_html = clean_text(response.content)
        
        # Analysis
        analysis_prompt = f"""Analyze this translation for accuracy and quality:
        Original ({from_lang}): {input_text}
        Translation ({to_lang}): {translated_html}
        
        Provide a brief analysis of:
        1. Translation accuracy
        2. Preservation of meaning
        3. Natural flow in the target language
        4. Any notable challenges or special handling of technical terms"""
        
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            system="You are a professional translation reviewer who provides detailed analysis of translations.",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        analysis = clean_text(analysis_response.content)
        return translated_html, analysis
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None, None
        
def main():
    st.set_page_config(page_title="CICERO Translator", layout="wide")

    if 'input_text' not in st.session_state:
        st.session_state.input_text = None
    if 'translation' not in st.session_state:
        st.session_state.translation = None
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None

    st.title("CICERO Article Translator 🌍")
    direction = st.radio("Translation Direction:", ["Norwegian → English", "English → Norwegian"])
    input_method = st.radio("Input Method:", ["Paste URL", "Paste Content"])

    from_lang = "Norwegian" if "Norwegian" in direction else "English"
    to_lang = "English" if "English" in direction else "Norwegian"
    preserve_html = st.checkbox("Preserve HTML structure", value=True)

    if input_method == "Paste URL":
        url = st.text_input("Enter CICERO Article URL")
        if url:
            try:
                st.session_state.input_text = fetch_cicero_article(url)
            except ValueError as e:
                st.error(str(e))
    else:
        st.session_state.input_text = st.text_area(f"Paste {from_lang} content here:")

    if st.button("Translate"):
        if st.session_state.input_text:
            with st.spinner("Translating..."):
                translation, analysis = get_translation_and_analysis(
                    st.session_state.input_text, from_lang, to_lang, preserve_html
                )
                st.session_state.translation = translation
                st.session_state.analysis = analysis

    if st.session_state.translation:
        st.subheader(f"Original ({from_lang})")
        st.markdown(st.session_state.input_text, unsafe_allow_html=True)
        
        st.subheader(f"Translation ({to_lang})")
        st.markdown(st.session_state.translation, unsafe_allow_html=True)
        
        st.download_button(
            label="Download Translation",
            data=st.session_state.translation,
            file_name="translation.html",
            mime="text/html"
        )
        
        if st.session_state.analysis:
            st.subheader("Analysis")
            st.write(st.session_state.analysis)

if __name__ == "__main__":
    main()
