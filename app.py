import streamlit as st
from anthropic import Anthropic
from bs4 import BeautifulSoup
import requests
from html import unescape
import re
from typing import Dict, List, Tuple, Optional

# Constants and Configuration
CLIMATE_TERMS = {
    "klimaendringer": "climate change",
    "utslipp": "emissions",
    "klimagasser": "greenhouse gases",
    "havnivåstigning": "sea level rise",
    "klimatiltak": "climate measures",
    "klimatilpasning": "climate adaptation",
    "karbonfangst": "carbon capture",
    "fornybar energi": "renewable energy",
    # Add more CICERO-specific terms as needed
}

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

def chunk_content(html_content: str, max_chunk_size: int = 1000) -> List[str]:
    """Split content into logical chunks while preserving structure."""
    soup = BeautifulSoup(html_content, 'html.parser')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'figcaption']):
        element_text = element.get_text(strip=True)
        if not element_text:
            continue
            
        # Start new chunk on headers or when chunk gets too large
        if (element.name.startswith('h') and current_chunk) or current_size > max_chunk_size:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
            
        current_chunk.append(str(element))
        current_size += len(element_text)
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def validate_translation_quality(original: str, translated: str) -> Dict[str, bool]:
    """Check translation quality metrics."""
    def check_numbers_match(orig: str, trans: str) -> bool:
        orig_numbers = re.findall(r'\d+(?:\.\d+)?', orig)
        trans_numbers = re.findall(r'\d+(?:\.\d+)?', trans)
        return len(orig_numbers) == len(trans_numbers)
    
    def check_terminology(trans: str, terms: Dict[str, str]) -> bool:
        for eng_term in terms.values():
            if eng_term.lower() in trans.lower():
                return True
        return True  # Return True if no terms found (might be chunk without terms)
    
    def check_units_preserved(orig: str, trans: str) -> bool:
        unit_pattern = r'\d+\s*(?:km|m|cm|kg|°C|%)'
        orig_units = re.findall(unit_pattern, orig)
        trans_units = re.findall(unit_pattern, trans)
        return len(orig_units) == len(trans_units)
    
    return {
        'numbers_preserved': check_numbers_match(original, translated),
        'terms_consistent': check_terminology(translated, CLIMATE_TERMS),
        'scientific_units': check_units_preserved(original, translated),
        'length_reasonable': 0.8 <= len(translated)/len(original) <= 1.2
    }

def create_translation_prompt(chunk: str, from_lang: str, to_lang: str, 
                            previous_chunk: Optional[str] = None, 
                            next_chunk: Optional[str] = None) -> str:
    """Create enhanced translation prompt with context."""
    context = f"""You are an experienced climate science translator working with CICERO content.
    
    Context:
    Previous content: {previous_chunk if previous_chunk else 'Start of article'}
    Following content: {next_chunk if next_chunk else 'End of article'}
    
    Required terminology translations:
    {CLIMATE_TERMS}
    
    Translation guidelines:
    - Maintain precise scientific language and technical terms
    - Use active voice where appropriate
    - Preserve uncertainty qualifiers exactly (likely, very likely, etc.)
    - Keep measurements and units consistent
    - Ensure technical terms are translated consistently
    - Adapt Norwegian expressions to natural {to_lang}
    - Preserve citations and references exactly
    
    Please translate the following {from_lang} text to {to_lang}:
    
    {chunk}
    """
    return context

def translate_chunk(chunk: str, from_lang: str, to_lang: str, 
                   previous_chunk: Optional[str] = None, 
                   next_chunk: Optional[str] = None) -> str:
    """Translate a single chunk while maintaining context."""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        prompt = create_translation_prompt(chunk, from_lang, to_lang, 
                                        previous_chunk, next_chunk)
        
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=3000,
            temperature=0,
            system=f"You are a professional translator specializing in climate science and academic content. Your goal is to produce translations that read naturally in {to_lang} while preserving precise scientific meaning.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        translated_text = response.content[0].text
        
        # Validate translation quality
        quality = validate_translation_quality(chunk, translated_text)
        if not all(quality.values()):
            st.warning(f"Quality check issues detected: {quality}")
        
        return translated_text
    
    except Exception as e:
        st.error(f"Translation error in chunk: {str(e)}")
        return chunk  # Return original chunk if translation fails

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str) -> Tuple[str, str]:
    """Translate and analyze content in chunks."""
    try:
        # Split content into chunks
        chunks = chunk_content(input_text)
        translated_chunks = []
        
        # Progress bar
        progress_bar = st.progress(0)
        
        # Translate each chunk
        for i, chunk in enumerate(chunks):
            prev_chunk = chunks[i-1] if i > 0 else None
            next_chunk = chunks[i+1] if i < len(chunks)-1 else None
            
            translated_chunk = translate_chunk(chunk, from_lang, to_lang, 
                                            prev_chunk, next_chunk)
            translated_chunks.append(translated_chunk)
            
            # Update progress
            progress_bar.progress((i + 1) / len(chunks))
        
        # Combine translated chunks
        complete_translation = '\n'.join(translated_chunks)
        
        # Create the HTML output
        output_html = f"""
        <div style="display: flex; gap: 2rem; margin: 1rem 0;">
            <div style="flex: 1;">
                <h2 style="color: #2c3e50; margin-bottom: 1rem;">Original ({from_lang})</h2>
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px;">
                    {input_text}
                </div>
            </div>
            <div style="flex: 1;">
                <h2 style="color: #2c3e50; margin-bottom: 1rem;">Translation ({to_lang})</h2>
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px;">
                    {complete_translation}
                </div>
            </div>
        </div>
        """
        
        # Generate analysis
        analysis_response = get_translation_analysis(input_text, complete_translation, 
                                                  from_lang, to_lang)
        
        analysis_html = f"""
        <div style="background: #f8f9fa; padding: 2rem; border-radius: 4px; margin-top: 2rem;">
            <h2 style="color: #2c3e50; margin-bottom: 1.5rem;">Translation Analysis</h2>
            <div style="margin-left: 1rem;">
                {analysis_response}
            </div>
        </div>
        """
        
        return output_html, analysis_html
    
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None, None

def get_translation_analysis(original: str, translation: str, 
                           from_lang: str, to_lang: str) -> str:
    """Generate analysis of the translation."""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        analysis_prompt = f"""Analyze this climate science translation and provide a structured report:

        # Translation Analysis

        ## Technical Accuracy
        - Evaluate preservation of scientific terms and concepts
        - Check consistency of measurements and units
        - Assess handling of uncertainty language

        ## Language Adaptation
        - Identify how Norwegian expressions were adapted to English
        - Note any areas where phrasing could be more natural
        - Evaluate active vs passive voice usage

        ## Suggestions for Improvement
        Provide specific, actionable suggestions for improving the translation.

        Original ({from_lang}):
        {original}

        Translation ({to_lang}):
        {translation}
        """
        
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            system="You are a translation reviewer specializing in climate science communication.",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        
        return response.content[0].text
    
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return "Analysis unavailable"

def main():
    st.set_page_config(page_title="CICERO Translator", layout="wide")

    # Initialize session state
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
                    to_lang
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
            st.markdown(st.session_state.analysis, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
