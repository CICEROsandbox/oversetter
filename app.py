import streamlit as st
from anthropic import Anthropic

# Page configuration
st.set_page_config(
    page_title="Climate Science Translator",
    page_icon="🌍",
    layout="wide"
)

def translate_text(text, from_lang, to_lang):
    """Translate text using Claude API"""
    try:
        anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        prompt = f"""You are a specialized translator for climate science content from {from_lang} to {to_lang}. 
        Please translate the following {from_lang} text to {to_lang}, maintaining scientific accuracy 
        and using appropriate climate science terminology:
        
        {text}
        """
        
        message = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.0,
            system=f"You are a specialized translator for climate science content, translating from {from_lang} to {to_lang}.",
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
st.write("Translate climate science content between English and Norwegian")

# Translation direction selector
direction = st.radio(
    "Select translation direction:",
    ["English → Norwegian", "Norwegian → English"],
    horizontal=True
)

# Set languages based on direction
if direction == "English → Norwegian":
    from_lang = "English"
    to_lang = "Norwegian"
    example_text = """
    Climate change impacts are already more widespread and severe than expected. 
    Future risks will increase with every increment of global warming.
    """
else:
    from_lang = "Norwegian"
    to_lang = "English"
    example_text = """
    Klimaendringenes konsekvenser er allerede mer omfattende og alvorlige enn forventet. 
    Fremtidige risikoer vil øke med hver økning i global oppvarming.
    """

# Create two columns for input and output
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"{from_lang} Text")
    input_text = st.text_area("Enter text to translate:", height=300)

with col2:
    st.subheader(f"{to_lang} Translation")
    if st.button("Translate"):
        if input_text:
            with st.spinner("Translating..."):
                translation = translate_text(input_text, from_lang, to_lang)
                if translation:
                    st.text_area("Translation:", value=translation, height=300, disabled=True)
                    
                    # Download button
                    st.download_button(
                        label="Download Translation",
                        data=translation,
                        file_name=f"translation_{to_lang.lower()}.txt",
                        mime="text/plain"
                    )
        else:
            st.warning("Please enter some text to translate")

# Sidebar with information and examples
with st.sidebar:
    st.header("About")
    st.write("""
    This translator is specialized for climate science content, 
    with expertise in IPCC terminology and climate research.
    """)
    
    # Add example button
    if st.button("Load Example"):
        st.session_state['input_text'] = example_text

# Footer
st.markdown("---")
st.markdown("Created by CICERO • Powered by Claude API")
