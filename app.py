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
        
        # Get main article content more comprehensively
        content_areas = [
            'div.styles_textBlock___VSu1',  # Main text blocks
            'div.styles_articleHeader__RYxA_',  # Article header
            'p',  # All paragraphs
            'div.styles_contentWithLabel__tHzjJ',  # Content with labels
            'figcaption',  # Image captions
            'h2, h3, h4, h5, h6'  # All subheadings
        ]
        
        for selector in content_areas:
            elements = soup.select(selector)
            for element in elements:
                # Skip elements that are part of navigation or metadata
                if any(skip in str(element.get('class', [])) for skip in ['breadcrumbs', 'menu', 'footer', 'caption']):
                    continue
                    
                # Get text content
                text = element.get_text(strip=True)
                if text and not any(text in existing for existing in article_content):
                    article_content.append(str(element))
        
        if not article_content:
            raise Exception("No article content found")
            
        return '\n'.join(article_content)
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing article: {str(e)}")

def extract_translatable_content(html_content: str) -> list:
    """Extract only the translatable content from CICERO HTML while preserving structure"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    translatable_elements = []
    
    # More comprehensive content selection
    content_selectors = [
        'div.styles_textBlock___VSu1',
        'h1, h2, h3, h4, h5, h6',
        'p:not(.styles_caption__qsbpi)',
        'figcaption',
        'div.styles_articleHeader__RYxA_ p',
        'div.styles_contentWithLabel__tHzjJ div',
        'li',  # List items
        'blockquote'  # Quoted content
    ]
    
    seen_text = set()  # To avoid duplicates
    
    for selector in content_selectors:
        elements = soup.select(selector)
        for elem in elements:
            # Skip elements that are part of navigation or metadata
            if any(skip in str(elem.get('class', [])) for skip in ['breadcrumbs', 'menu', 'footer', 'caption']):
                continue
                
            text = elem.get_text(strip=True)
            if text and text not in seen_text:
                seen_text.add(text)
                translatable_elements.append({
                    'html': str(elem),
                    'text': text,
                    'tag': elem.name
                })
    
    return translatable_elements

def clean_text(text, preserve_html: bool = False) -> str:
    """Clean text while preserving HTML if needed"""
    if isinstance(text, list):
        text = ' '.join(str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text)
    
    # First, remove all technical artifacts and formatting
    text = re.sub(r'<userStyle>.*?</userStyle>', '', text)  # Remove userStyle tags
    text = re.sub(r'TextBlock\(text=[\'"](.*?)[\'"]\)', r'\1', text)  # Remove TextBlock wrapper
    text = re.sub(r"['\"]?,?\s*type=['\"]text['\"]", '', text)  # Remove type='text'
    text = re.sub(r'Here is the translation.*?:\n\n', '', text)  # Remove translation prefix
    text = re.sub(r'\*\*\s*(.*?)\s*\*\*', r'\1', text)  # Remove markdown bold
    text = re.sub(r'\(\s*\)', '', text)  # Remove empty parentheses
    text = re.sub(r',\s*$', '', text)  # Remove trailing commas
    text = re.sub(r"^'|'$", '', text)  # Remove single quotes at start/end
    text = re.sub(r'\\n', '\n', text)  # Convert escaped newlines to actual newlines
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()
    
    return text

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str, preserve_html: bool = False):
    """Get translation and analysis with improved handling"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        if preserve_html:
            translatable_elements = extract_translatable_content(input_text)
            
            translation_prompt = f"""Translate this content from {from_lang} to {to_lang}.
            Important rules:
            1. Translate ALL text content - don't skip anything
            2. Keep HTML tags exactly as they are
            3. Don't add any formatting marks or technical annotations
            4. Don't add any metadata like 'type=text'
            5. Remove any "Here is the translation..." prefixes
            6. Don't add any extra quotes or asterisks
            7. Keep the same paragraph structure
            8. If you see text in quotes, translate the text but keep the quotes
            
            For example:
            Input: <p>"Dette er en test"</p>
            Correct: <p>"This is a test"</p>
            Wrong: <p>type='text' "This is a test"</p>
            """
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            translated_html = input_text
            total_elements = len(translatable_elements)
            
            for idx, element in enumerate(translatable_elements):
                if element['text'].strip():
                    status_text.text(f"Translating element {idx + 1} of {total_elements}...")
                    
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
                    
                progress_bar.progress((idx + 1) / total_elements)
            
            status_text.empty()
            progress_bar.empty()
            
            # Final cleanup
            translated_html = clean_text(translated_html, preserve_html=True)
            
        else:
            translation_response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"""Translate this from {from_lang} to {to_lang}.
                    Important: Translate ALL text and keep any quotation marks around quoted text.
                    Do not add any metadata or formatting.
                    
                    Text to translate: {input_text}"""
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
