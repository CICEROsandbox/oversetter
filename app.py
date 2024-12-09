import streamlit as st
from anthropic import Anthropic
import re

def clean_text(text):
    """Clean text formatting"""
    # Remove [TextBlock] artifacts
    text = re.sub(r'\[TextBlock\(text=[\'"](.*)[\'"].*?\)\]', r'\1', str(text))
    
    # Remove quotes and backslashes
    text = re.sub(r'[\'"\\]', '', text)
    
    # Fix n- artifacts in analysis sections
    text = re.sub(r'(?:^|\n)(\w+):n-\s*', r'\n\1:\n', text)
    
    # Standardize newlines and clean up spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Restore paragraph breaks for sections
    text = text.replace(' Key Terms:', '\nKey Terms:')
    text = text.replace(' Challenges:', '\nChallenges:')
    text = text.replace(' Suggestions:', '\nSuggestions:')
    
    return text.strip()

def get_translation_and_analysis(input_text, from_lang, to_lang):
    """Get translation and analysis"""
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Get translation with instruction about numbers and alternatives
        translation_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user", 
                "content": f"""Translate this from {from_lang} to {to_lang}. 
                Important instructions:
                - Keep numbers in their original format
                - Just translate 'milliarder' to 'billion' when going from Norwegian to English
                - For key terms or phrases that could have multiple valid translations, include alternatives in parentheses
                
                {input_text}"""
            }]
        )
        
        translation = clean_text(translation_response.content)
        
        # Get analysis with improved formatting instructions
        analysis_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Analyze this translation:

                Original: {input_text}
                Translation: {translation}

                Provide analysis in these sections:
                
                Key Terms:
                • List 2-3 important terminology translations
                • Include alternative translations in parentheses where relevant
                • Example format: "utslippskutt" → "emission cuts (emission reductions)"
                
                Challenges:
                • Note 1-2 main translation challenges
                • Be specific about structural or cultural differences
                
                Suggestions:
                • Provide 1-2 concrete improvement ideas
                • Focus on clarity and accuracy"""
            }]
        )
        
        analysis = clean_text(analysis_response.content)
        return translation, analysis
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, None

# [Rest of the Streamlit UI code remains the same]
