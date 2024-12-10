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

def clean_text(text, preserve_html: bool = False) -> str:
    """Clean text while preserving HTML if needed"""
    if isinstance(text, list):
        text = ' '.join(str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text)
    
    # Remove TextBlock artifacts
    text = re.sub(r'TextBlock\(text=[\'"](.*?)[\'"]\)', r'\1', text)
    
    if preserve_html:
        # Clean up newlines and spaces while preserving HTML tags
        text = re.sub(r'\\n\\n|\\n|\n\n|\n', ' ', text)
        text = re.sub(r'\s+', ' ', text)
    else:
        # Clean up all formatting
        text = re.sub(r'\\n\\n|\\n|\n\n|\n', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\. ([A-Z])', '.\n\n\\1', text)
    
    return text.strip()

def extract_translatable_content(html_content: str) -> dict:
    """Extract only the translatable content from CICERO HTML while preserving structure"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    translatable_elements = []
    
    # Get text from specific content areas
    content_selectors = [
        'div.styles_textBlock___VSu1',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p:not(.styles_caption__qsbpi)',
        'figcaption'
    ]
    
    for selector in content_selectors:
        elements = soup.select(selector)
        for elem in elements:
            translatable_elements.append({
                'html': str(elem),
                'text': elem.get_text(strip=True),
                'tag': elem.name
            })
    
    return translatable_elements

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str, preserve_html: bool = False):
    """Get translation and analysis with enhanced HTML support for CICERO content"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        if preserve_html:
            translatable_elements = extract_translatable_content(input_text)
            
            translation_prompt = f"""Translate this content from {from_lang} to {to_lang}.
            Important:
            - Only translate the text content between HTML tags
            - Preserve all HTML tags and attributes exactly
            - Maintain all links, references, and internal structure
            - Keep image references and captions in their original structure
            - Skip any structural content (menus, navigation, metadata)
            - For headings, maintain the appropriate tone and style for headlines
            """
            
            translated_html = input_text
            for element in translatable_elements:
                if element['text'].strip():
                    translation_response = client.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=1000,
                        temperature=0,
                        messages=[{
                            "role": "user",
                            "content": f"{translation_prompt}\n\nText to translate: {element['text']}"
                        }]
                    )
                    
                    translated_text = clean_text(translation_response.content)
                    translated_html = translated_html.replace(element['text'], translated_text)
        
        else:
            translation_response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"Translate this from {from_lang} to {to_lang}:\n\n{input_text}"
                }]
            )
            translated_html = clean_text(translation_response.content)
        
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Analyze this translation:

                Original: {input_text}
                Translation: {translated_html}

                Provide brief analysis focusing on:
                1. Key terminology translations for climate science
                2. Any challenging aspects specific to CICERO content
                3. Suggestions for improvement"""
            }]
        )
        
        analysis = clean_text(analysis_response.content)
        return translated_html, analysis
        
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None, None

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
