import streamlit as st
from anthropic import Anthropic
import re
from bs4 import BeautifulSoup
import requests

# [Previous helper functions remain the same]

def main():
    st.set_page_config(page_title="CICERO Article Translator", layout="wide")

    # Initialize session state
    if 'input_text' not in st.session_state:
        st.session_state.input_text = None
    if 'translation' not in st.session_state:
        st.session_state.translation = None
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None

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

    # Input section
    if input_method == "Paste URL":
        url = st.text_input(
            "Enter CICERO article URL",
            placeholder="https://cicero.oslo.no/no/artikler/..."
        )
        if url and url != st.session_state.get('last_url', ''):
            try:
                with st.spinner("Fetching article content..."):
                    st.session_state.input_text = fetch_cicero_article(url)
                    st.session_state.last_url = url
            except Exception as e:
                st.error(f"Error fetching article: {str(e)}")
    else:
        input_text = st.text_area(
            label="Input text",
            height=300,
            label_visibility="collapsed",
            key="input_area",
            placeholder=f"Paste {from_lang} article content here..."
        )
        if input_text:
            st.session_state.input_text = input_text

    # Translation button and display
    if st.button("Translate", type="primary"):
        if st.session_state.input_text:
            with st.spinner("Translating..."):
                translation, analysis = get_translation_and_analysis(
                    st.session_state.input_text, 
                    from_lang, 
                    to_lang, 
                    preserve_html
                )
                if translation:
                    st.session_state.translation = translation
                    st.session_state.analysis = analysis

    # Always show content if available
    if st.session_state.input_text and st.session_state.translation:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Original ({from_lang})")
            if preserve_html:
                st.markdown(st.session_state.input_text, unsafe_allow_html=True)
            else:
                st.markdown(st.session_state.input_text)
        
        with col2:
            st.subheader(f"Translation ({to_lang})")
            if preserve_html:
                st.markdown(st.session_state.translation, unsafe_allow_html=True)
            else:
                st.markdown(st.session_state.translation)

        # Download button outside columns
        st.download_button(
            label="Download Raw HTML",
            data=st.session_state.translation,
            file_name="translation.html",
            mime="text/html"
        )
        
        if st.session_state.analysis:
            st.subheader("Translation Analysis")
            st.markdown(st.session_state.analysis)
    
    st.caption("Created by CICERO • Powered by Claude API")

if __name__ == "__main__":
    main()
