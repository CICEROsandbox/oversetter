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
        
        # Get main article content
        main_content = soup.find_all('div', class_='styles_textBlock___VSu1')
        if main_content:
            seen_text = set()
            for content in main_content:
                text = content.get_text(strip=True)
                if text not in seen_text:
                    article_content.append(str(content))
                    seen_text.add(text)
        
        if not article_content:
            raise Exception("No article content found")
            
        return '\n'.join(article_content)
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing article: {str(e)}")

def clean_text(text, preserve_html: bool = False) -> str:
    """Clean text while preserving HTML if needed"""
    if isinstance(text, list):
        text = ' '.join(str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text)
    
    # Remove TextBlock artifacts
    text = re.sub(r'TextBlock\(text=[\'"](.*?)[\'"]\)', r'\1', text)  # Remove TextBlock wrapper
    text = re.sub(r'\*\*\s*([^*]+?)\s*\*\*', r'\1', text)  # Remove markdown bold
    text = re.sub(r'<userStyle>.*?</userStyle>', '', text)  # Remove userStyle tags
    text = re.sub(r'\(\s*\)', '', text)  # Remove empty parentheses
    
    # Fix spacing issues
    text = re.sub(r'\n{3,}', '\n\n', text)  # Reduce multiple newlines to double
    text = re.sub(r'^\s+', '', text)  # Remove leading whitespace
    text = re.sub(r'\s+$', '', text)  # Remove trailing whitespace
    text = re.sub(r'\s*\n\s*', '\n', text)  # Clean up spaces around newlines
    
    if preserve_html:
        # Clean up whitespace while preserving HTML structure
        text = re.sub(r'>\s+<', '><', text)
        text = re.sub(r'>\s+([^<])', r'>\1', text)
        text = re.sub(r'([^>])\s+<', r'\1<', text)
    else:
        # For plain text, ensure proper sentence spacing
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\. ([A-Z])', '.\n\n\\1', text)
    
    # Final cleanup
    text = text.strip()
    text = re.sub(r'\n{3,}', '\n\n', text)  # Final check for multiple newlines
    
    return text

def extract_translatable_content(html_content: str) -> list:
    """Extract only the translatable content from CICERO HTML while preserving structure"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    translatable_elements = []
    
    content_selectors = [
        'div.styles_textBlock___VSu1',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p:not(.styles_caption__qsbpi)',
        'figcaption'
    ]
    
    for selector in content_selectors:
        elements = soup.select(selector)
        for elem in elements:
            # Clean the text before adding to translatable elements
            clean_content = clean_text(elem.get_text(strip=True))
            if clean_content:  # Only add if there's actual content after cleaning
                translatable_elements.append({
                    'html': str(elem),
                    'text': clean_content,
                    'tag': elem.name
                })
    
    return translatable_elements
    
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
    """Get translation and analysis with improved artifact handling"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        if preserve_html:
            translatable_elements = extract_translatable_content(input_text)
            
            translation_prompt = f"""Translate this content from {from_lang} to {to_lang}.
            Important:
            - Translate only the actual content
            - Preserve HTML structure exactly
            - Do not add any technical annotations or metadata
            - Do not add phrases like 'type=text' or similar
            - Keep heading formats but translate the text
            - Maintain the same paragraph structure
            For the title/heading, translate directly without adding any metadata or quotes.
            """
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            translated_html = input_text
            total_elements = len(translatable_elements)
            
            for idx, element in enumerate(translatable_elements):
                if element['text'].strip():
                    status_text.text(f"Translating element {idx + 1} of {total_elements}...")
                    
                    # Special handling for titles to prevent artifacts
                    if element['tag'] in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        prompt = f"{translation_prompt}\nThis is a title/heading - translate only the text without adding any metadata:"
                    else:
                        prompt = translation_prompt
                    
                    translation_response = client.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=1000,
                        temperature=0,
                        messages=[{
                            "role": "user",
                            "content": f"{prompt}\n\nText to translate: {element['text']}"
                        }]
                    )
                    
                    translated_text = clean_text(translation_response.content)
                    translated_html = translated_html.replace(element['text'], translated_text)
                    
                progress_bar.progress((idx + 1) / total_elements)
            
            status_text.empty()
            progress_bar.empty()
            
            # Final cleanup pass
            translated_html = re.sub(r"['\"]?,?\s*type=['\"]text['\"]", '', translated_html)
            translated_html = re.sub(r"',\s*$", '', translated_html)
            translated_html = re.sub(r"^'", '', translated_html)
            translated_html = re.sub(r',\s*$', '', translated_html)
            translated_html = re.sub(r'>\s+<', '><', translated_html)
            
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
        
        # Get analysis
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Analyze this translation:
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

    # Initialize session state
    if 'input_text' not in st.session_state:
        st.session_state.input_text = None
    if 'translation' not in st.session_state:
        st.session_state.translation = None
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None
    if 'last_url' not in st.session_state:
        st.session_state.last_url = None

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
        if url and url != st.session_state.last_url:
            try:
                with st.spinner("Fetching article content..."):
                    st.session_state.input_text = fetch_cicero_article(url)
                    st.session_state.last_url = url
            except Exception as e:
                st.error(f"Error fetching article: {str(e)}")
                st.session_state.input_text = None
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

        # Download button for raw HTML
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
