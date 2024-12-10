import streamlit as st
from anthropic import Anthropic
import re
from bs4 import BeautifulSoup
import requests

def fetch_cicero_article(url: str) -> str:
    """Fetch article content from CICERO website"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main article content
        article_content = []
        
        # Get article title
        title = soup.find('h1')
        if title:
            article_content.append(str(title))
        
        # Get only the main article content (avoiding duplicate intro)
        main_content = soup.find_all('div', class_='styles_textBlock___VSu1')
        if main_content:
            # Skip the first occurrence if it's duplicate intro text
            seen_text = set()
            for content in main_content:
                text = content.get_text(strip=True)
                if text not in seen_text:
                    article_content.append(str(content))
                    seen_text.add(text)
            
        return '\n'.join(article_content)
    except Exception as e:
        raise Exception(f"Error fetching article: {str(e)}")

# [Previous functions remain the same: clean_text, extract_translatable_content, get_translation_and_analysis]

def download_html(translated_html):
    """Create a download link for the raw HTML"""
    return f'<a href="data:text/html;charset=utf-8,{translated_html}" download="translation.html">Download Raw HTML</a>'

def main():
    st.set_page_config(page_title="CICERO Article Translator", layout="wide")

    st.markdown('<h1 style="font-size: 2.5rem; font-weight: bold;">CICERO Article Translator 🌍</h1>', unsafe_allow_html=True)

    col_controls1, col_controls2 = st.columns([1, 2])
    
    with col_controls1:
        direction = st.radio(
            "Select translation direction:",
            ["Norwegian → English", "English → Norwegian"],
            horizontal=True,
            label_visibility="collapsed"
        )

    with col_controls2:
        input_method = st.radio(
            "Choose input method:",
            ["Paste URL", "Paste Content"],
            horizontal=True
        )

    from_lang = "Norwegian" if direction.startswith("Norwegian") else "English"
    to_lang = "English" if direction.startswith("Norwegian") else "Norwegian"

    preserve_html = st.checkbox(
        "Preserve HTML structure", 
        value=True,
        help="Keep HTML tags and structure from CICERO articles (recommended for website content)"
    )

    if input_method == "Paste URL":
        url = st.text_input(
            "Enter CICERO article URL",
            placeholder="https://cicero.oslo.no/no/artikler/..."
        )
        if url:
            try:
                with st.spinner("Fetching article content..."):
                    input_text = fetch_cicero_article(url)
            except Exception as e:
                st.error(f"Error fetching article: {str(e)}")
                input_text = ""
        else:
            input_text = ""
    else:
        input_text = st.text_area(
            label="Input text",
            height=300,
            label_visibility="collapsed",
            key="input_area",
            placeholder=f"Paste {from_lang} article content here..."
        )

    if st.button("Translate", type="primary"):
        if input_text:
            with st.spinner("Translating..."):
                translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang, preserve_html)
                
                if translation:
                    # Store in session state
                    st.session_state['translation'] = translation
                    st.session_state['input_text'] = input_text
                    
                    # Create two columns for side-by-side display
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(f"Original ({from_lang})")
                        if preserve_html:
                            st.markdown(input_text, unsafe_allow_html=True)
                        else:
                            st.markdown(input_text)
                    
                    with col2:
                        st.subheader(f"Translation ({to_lang})")
                        if preserve_html:
                            st.markdown(translation, unsafe_allow_html=True)
                        else:
                            st.markdown(translation)
                    
                    # Download HTML button
                    st.download_button(
                        label="Download Raw HTML",
                        data=translation,
                        file_name="translation.html",
                        mime="text/html"
                    )
                    
                    if analysis:
                        st.subheader("Translation Analysis")
                        st.markdown(analysis)
        else:
            st.warning("Please enter a URL or paste content to translate")

    st.caption("Created by CICERO • Powered by Claude API")

if __name__ == "__main__":
    main()
