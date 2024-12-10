import streamlit as st
from anthropic import Anthropic
import re
from bs4 import BeautifulSoup
import requests

# [Previous functions: fetch_cicero_article, clean_text remain the same]

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

def translate_element(client, element: dict, from_lang: str, to_lang: str) -> str:
    """Translate a single HTML element"""
    if not element['text'].strip():
        return element['html']
        
    translation_prompt = f"""Translate this content from {from_lang} to {to_lang}.
    Important:
    - Only translate the text content
    - Preserve any special terminology
    - Maintain the same tone and style
    - For headings, keep the headline style
    """
    
    try:
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
        return element['html'].replace(element['text'], translated_text)
    except Exception as e:
        st.error(f"Error translating element: {str(e)}")
        return element['html']

def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str, preserve_html: bool = False):
    """Get translation and analysis with enhanced HTML support for CICERO content"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        if preserve_html:
            # Extract all translatable elements
            translatable_elements = extract_translatable_content(input_text)
            
            # Show progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Translate elements one by one
            translated_pieces = []
            total_elements = len(translatable_elements)
            
            for idx, element in enumerate(translatable_elements):
                status_text.text(f"Translating element {idx + 1} of {total_elements}...")
                translated_html = translate_element(client, element, from_lang, to_lang)
                translated_pieces.append(translated_html)
                progress_bar.progress((idx + 1) / total_elements)
            
            # Clear progress indicators
            status_text.empty()
            progress_bar.empty()
            
            # Combine all translated pieces
            translated_html = '\n'.join(translated_pieces)
            
        else:
            # For plain text, split into smaller chunks
            chunks = [input_text[i:i+4000] for i in range(0, len(input_text), 4000)]
            translated_chunks = []
            
            # Show progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, chunk in enumerate(chunks):
                status_text.text(f"Translating chunk {idx + 1} of {len(chunks)}...")
                
                translation_response = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    temperature=0,
                    messages=[{
                        "role": "user",
                        "content": f"Translate this from {from_lang} to {to_lang}:\n\n{chunk}"
                    }]
                )
                
                translated_chunks.append(clean_text(translation_response.content))
                progress_bar.progress((idx + 1) / len(chunks))
            
            # Clear progress indicators
            status_text.empty()
            progress_bar.empty()
            
            translated_html = ' '.join(translated_chunks)
        
        # Get analysis on the complete translation
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Analyze this translation:

                Original length: {len(input_text)} characters
                Translated length: {len(translated_html)} characters

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

# [Rest of the main() function remains the same]
