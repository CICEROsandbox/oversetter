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

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if isinstance(text, list):
        text = ' '.join([str(item) for item in text])
    elif not isinstance(text, str):
        text = str(text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_html_content(html_content: str) -> str:
    """Clean HTML content by removing duplicate content and unnecessary tags."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove duplicate sections
    seen_text = set()
    duplicates = []
    
    for element in soup.find_all(string=True):
        text = element.strip()
        if text and text in seen_text:
            parent = element.find_parent()
            if parent:
                duplicates.append(parent)
        seen_text.add(text)
    
    for duplicate in duplicates:
        duplicate.decompose()
    
    # Clean up empty elements
    for element in soup.find_all():
        if not element.get_text(strip=True) and not element.find_all('img'):
            element.decompose()
    
    return str(soup)

def extract_translatable_content(html_content: str) -> list:
    """Extract translatable content while preserving structure and order."""
    soup = BeautifulSoup(html_content, 'html.parser')
    content_elements = []
    
    # Define the order of elements we want to extract
    selectors = [
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        '.styles_lead',  # Lead paragraph
        'p',
        'figcaption',
        '.styles_textBlock___VSu1'
    ]
    
    # Extract elements in order
    for selector in selectors:
        elements = soup.select(selector)
        for element in elements:
            if element.get_text(strip=True):
                content_elements.append({
                    'tag': element.name,
                    'class': element.get('class', []),
                    'text': element.get_text(strip=True),
                    'original_html': str(element)
                })
    
    return content_elements

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str, preserve_html: bool = False):
    """Translate and analyze content."""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        if preserve_html:
            # Extract content in structured order
            content_elements = extract_translatable_content(input_text)
            
            # Create translation prompt with structured content
            translation_prompt = f"""Translate the following {from_lang} text to {to_lang}, maintaining the exact structure and order:

{'\n\n'.join([f'[{elem["tag"]}] {elem["text"]} [/{elem["tag"]}]' for elem in content_elements])}

Maintain the same order and structure in the translation."""
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=3000,
                temperature=0,
                system="You are a professional translator. Maintain the exact structure and order of the content in your translation.",
                messages=[{"role": "user", "content": translation_prompt}]
            )
            
            translated_text = response.content[0].text if isinstance(response.content, list) else response.content
            
            # Clean and structure both original and translated content
            output_html = f"""
            <div style="display: flex; gap: 2rem; margin: 1rem 0;">
                <div style="flex: 1;">
                    <h2 style="color: #2c3e50; margin-bottom: 1rem;">Original ({from_lang})</h2>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px;">
                        {' '.join([elem['original_html'] for elem in content_elements])}
                    </div>
                </div>
                <div style="flex: 1;">
                    <h2 style="color: #2c3e50; margin-bottom: 1rem;">Translation ({to_lang})</h2>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px;">
                        {clean_html_content(translated_text)}
                    </div>
                </div>
            </div>
            """

        else:
            # Simple text translation (rest of the code remains the same)
            translation_prompt = f"Translate this {from_lang} text to {to_lang}:\n\n{input_text}"
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=3000,
                temperature=0,
                system="You are a professional translator who provides accurate and natural-sounding translations.",
                messages=[{"role": "user", "content": translation_prompt}]
            )
            
            translated_text = response.content[0].text if isinstance(response.content, list) else response.content
            
            output_html = f"""
            <div style="display: flex; gap: 2rem; margin: 1rem 0;">
                <div style="flex: 1;">
                    <h2 style="color: #2c3e50; margin-bottom: 1rem;">Original ({from_lang})</h2>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px;">
                        <p>{input_text}</p>
                    </div>
                </div>
                <div style="flex: 1;">
                    <h2 style="color: #2c3e50; margin-bottom: 1rem;">Translation ({to_lang})</h2>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px;">
                        <p>{clean_text(translated_text)}</p>
                    </div>
                </div>
            </div>
            """

        # Analysis prompt remains the same
        analysis_prompt = f"""Analyze this translation focusing specifically on:

        1. Technical terms: How were specific technical or domain-specific terms handled?
        2. Idioms and expressions: How were idiomatic expressions translated?
        3. Uncertain translations: Note any terms or phrases where the translation choice is uncertain
        4. Cultural-specific elements: How were culture-specific references handled?

        Original ({from_lang}): {input_text}
        Translation ({to_lang}): {translated_text}

        Please be explicit about any uncertainties in word choices or translations. Do not speculate about meanings you're unsure of."""
        
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            system="You are a translation reviewer specializing in technical terminology and idiomatic expressions. Focus on specific terms and expressions rather than general translation quality.",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        
        analysis_text = analysis_response.content[0].text if isinstance(analysis_response.content, list) else analysis_response.content
        
        return output_html, clean_text(analysis_text)
    
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None, None
        
def main():
    st.set_page_config(page_title="CICERO Translator", layout="wide")

    # Initialize session state variables
    if 'input_text' not in st.session_state:
        st.session_state.input_text = None
    if 'translation' not in st.session_state:
        st.session_state.translation = None
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None

    st.title("CICERO Article Translator 🌍")
    
    # Translation direction selection
    direction = st.radio("Translation Direction:", ["Norwegian → English", "English → Norwegian"])
    
    # Input method selection
    input_method = st.radio("Input Method:", ["Paste URL", "Paste Content"])

    # Set languages based on direction
    from_lang = "Norwegian" if "Norwegian" in direction else "English"
    to_lang = "English" if "English" in direction else "Norwegian"
    
    # HTML structure preservation option
    preserve_html = st.checkbox("Preserve HTML structure", value=True)

    # Handle input
    if input_method == "Paste URL":
        url = st.text_input("Enter CICERO Article URL")
        if url:
            try:
                st.session_state.input_text = fetch_cicero_article(url)
            except ValueError as e:
                st.error(str(e))
    else:
        st.session_state.input_text = st.text_area(f"Paste {from_lang} content here:")

    # Translation button
    if st.button("Translate"):
        if st.session_state.input_text:
            with st.spinner("Translating..."):
                st.session_state.translation, st.session_state.analysis = get_translation_and_analysis(
                    st.session_state.input_text,
                    from_lang,
                    to_lang,
                    preserve_html
                )

    # Display results
    if st.session_state.translation:
        st.markdown(st.session_state.translation, unsafe_allow_html=True)
        
        # Download button
        st.download_button(
            label="Download Translation",
            data=st.session_state.translation,
            file_name="translation.html",
            mime="text/html"
        )
        
        if st.session_state.analysis:
            st.subheader("Translation Analysis")
            st.write(st.session_state.analysis)

if __name__ == "__main__":
    main()
