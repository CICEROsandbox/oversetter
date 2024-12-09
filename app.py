import streamlit as st
import pandas as pd
from anthropic import Anthropic
import os

# Page configuration
st.set_page_config(
    page_title="Climate Science Translator",
    page_icon="🌍",
    layout="wide"
)

# Function to load parallel text database
def load_parallel_text():
    """Load the parallel text dataset"""
    try:
        # Replace this path with your CSV file path
        df = pd.read_csv('data/ipcc_parallel_text.csv')
        return df
    except Exception as e:
        st.error(f"Error loading parallel text: {e}")
        return None

# Translation function using Claude API
def translate_text(text, parallel_df):
    """Translate text using Claude API with context from parallel text"""
    # Initialize Anthropic client with API key
    anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    
    # Create context from parallel text examples
    context = parallel_df.head(3)[['english', 'norwegian']].to_string()
    
    # Construct the prompt
    prompt = f"""You are a specialized translator for climate science content from English to Norwegian. 
    Here are some examples of high-quality translations to match the style:
    
    {context}
    
    Please translate the following English text to Norwegian, maintaining scientific accuracy 
    and matching the style of the example translations:
    
    {text}
    """
    
    try:
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.0,
            system="You are a specialized translator for climate science content, translating from English to Norwegian.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content
    except Exception as e:
        st.error(f"Translation error: {e}")
        return None

# Main UI
st.title("Climate Science Translator 🌍")
st.write("Translate climate science content from English to Norwegian")

# Load parallel text
parallel_df = load_parallel_text()
if parallel_df is not None:
    st.success("Loaded parallel text database for context")

# Create two columns for input and output
col1, col2 = st.columns(2)

with col1:
    st.subheader("English Text")
    input_text = st.text_area("Enter text to translate:", height=300)

with col2:
    st.subheader("Norwegian Translation")
    # Add translation button
    if st.button("Translate"):
        if input_text:
            with st.spinner("Translating..."):
                translation = translate_text(input_text, parallel_df)
                if translation:
                    st.text_area("Translation:", value=translation, height=300, disabled=True)
                    
                    # Download button for translation
                    st.download_button(
                        label="Download Translation",
                        data=translation,
                        file_name="translation.txt",
                        mime="text/plain"
                    )
        else:
            st.warning("Please enter some text to translate")

# Sidebar with information
with st.sidebar:
    st.header("About")
    st.write("""
    This translator is specialized for climate science content, 
    using context from IPCC reports to ensure accurate technical translations.
    """)
    
    # Example text button
    if st.button("Load Example Text"):
        example_text = """
        Climate change impacts are already more widespread and severe than expected. 
        Future risks will increase with every increment of global warming.
        """
        st.session_state['input_text'] = example_text

# Footer
st.markdown("---")
st.markdown("Created by CICERO • Powered by Claude API")
