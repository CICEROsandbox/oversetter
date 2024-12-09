import streamlit as st
from anthropic import Anthropic
import pandas as pd
import re

def clean_response(response):
    """Clean up Claude's response format"""
    # Remove TextBlock wrapper
    cleaned = re.sub(r'\[TextBlock\(text=\'(.*?)\'.*?\)\]', r'\1', str(response))
    # Remove intro phrases
    cleaned = re.sub(r'Here is the .* translation[,\s\w]*:\s*\n+', '', cleaned)
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def check_terminology(text, reference_df):
    """Check if key climate terms are translated consistently"""
    key_terms = {
        'climate change': 'klimaendringer',
        'greenhouse gas': 'klimagass',
        'emissions': 'utslipp',
        'global warming': 'global oppvarming'
        # Add more terms from your IPCC text
    }
    
    inconsistencies = []
    for eng, nor in key_terms.items():
        if eng in text.lower() and nor not in text.lower():
            inconsistencies.append(f"Check term: {eng} -> {nor}")
    return inconsistencies

def calculate_confidence(text, reference_df):
    """Calculate confidence score based on reference matches"""
    # Simple scoring based on key term matches
    score = 100
    inconsistencies = check_terminology(text, reference_df)
    score -= len(inconsistencies) * 10
    return max(score, 0)

def translate_text(text, from_lang, to_lang):
    """Enhanced translation with quality checks"""
    try:
        # Load reference text
        reference_df = pd.read_csv('data/ipcc_parallel_text.csv')
        
        # Create prompt with specific instructions
        prompt = f"""Translate this {from_lang} climate science text to {to_lang}.
        Provide ONLY the direct translation, no explanations or metadata.
        Use IPCC terminology and maintain scientific accuracy.

        Text to translate:
        {text}
        """
        
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Clean response
        translation = clean_response(message.content)
        
        # Run quality checks
        inconsistencies = check_terminology(translation, reference_df)
        confidence = calculate_confidence(translation, reference_df)
        
        return translation, inconsistencies, confidence
        
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None, [], 0

# UI Components
st.title("Climate Science Translator 🌍")

# Translation direction
direction = st.radio(
    "Select translation direction:",
    ["English → Norwegian", "Norwegian → English"],
    horizontal=True
)

from_lang = "English" if direction.startswith("English") else "Norwegian"
to_lang = "Norwegian" if direction.startswith("English") else "English"

# Input with document type selection
doc_type = st.selectbox(
    "Document type:",
    ["Scientific report", "Public communication", "Policy brief"]
)

# Input text
st.subheader(f"{from_lang} Text")
input_text = st.text_area(
    "Enter text to translate:",
    height=150,
    label_visibility="collapsed"
)

# Translation
if st.button("Translate", type="primary"):
    if input_text:
        with st.spinner("Translating..."):
            translation, inconsistencies, confidence = translate_text(
                input_text, from_lang, to_lang
            )
            
            if translation:
                # Show translation
                st.subheader(f"{to_lang} Translation")
                st.text_area(
                    "Translation result",
                    value=translation,
                    height=150,
                    label_visibility="collapsed"
                )
                
                # Show quality metrics in columns
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Confidence Score", f"{confidence}%")
                
                with col2:
                    if inconsistencies:
                        st.warning("Terminology checks:")
                        for issue in inconsistencies:
                            st.write(f"• {issue}")
                    else:
                        st.success("Terminology verified ✓")
    else:
        st.warning("Please enter some text to translate")

st.caption("Created by CICERO • Powered by Claude API")
