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
            translatable_elements = extract_translatable_content(input_text)
            
            translations = {}
            for element in translatable_elements:
                prompt = f"Translate from {from_lang} to {to_lang}:\n\n{element['text']}"
                response = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                translations[element['text']] = clean_text(response.content)
            
            for element in translatable_elements:
                if element['text'] in translations:
                    element['element'].replace_with(soup.new_string(translations[element['text']]))
            
            translated_html = str(soup)
        else:
            # Handle plain text translation
            prompt = f"Translate from {from_lang} to {to_lang}:\n\n{input_text}"
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            translated_html = clean_text(response.content)
        
        # Analysis
        analysis_prompt = f"Analyze this translation:\nOriginal: {input_text}\nTranslation: {translated_html}"
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
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
