                import streamlit as st
                from anthropic import Anthropic
                import re

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

                def get_translation_and_analysis(input_text: str, from_lang: str, to_lang: str, preserve_html: bool = False):
                """Get translation and analysis with HTML support"""
                try:
                client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
                # Get translation
                translation_prompt = f"""Translate this from {from_lang} to {to_lang}."""
        if preserve_html:
                translation_prompt += """
                Important:
                - Preserve all HTML tags exactly as they appear
                - Only translate text content between tags
                - Keep HTML attributes unchanged
                - Maintain HTML structure exactly
                """
            else:
                translation_prompt += """
                Important:
                - Keep paragraph breaks as single line breaks
                - Maintain proper sentence spacing
                - Do not add extra spaces or newlines
                """
            
                translation_response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{
                "role": "user",
                "content": f"{translation_prompt}\n\n{input_text}"
                }]
                )
        
                translation = clean_text(translation_response.content, preserve_html)
        
                # Get analysis
                analysis_response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{
                "role": "user",
                "content": f"""Analyze this translation:

                Original: {input_text}
                Translation: {translation}

                Provide brief analysis focusing on:
                1. Key terminology translations
                2. Any challenging aspects
                3. Suggestions for improvement"""
                }]
                )
        
                analysis = clean_text(analysis_response.content)
                return translation, analysis
        
                except Exception as e:
                st.error(f"Translation error: {str(e)}")
                return None, None

                def main():
                st.set_page_config(page_title="Climate Science Translator", layout="wide")

                st.markdown('<h1 style="font-size: 2.5rem; font-weight: bold;">Climate Science Translator 🌍</h1>', unsafe_allow_html=True)

                direction = st.radio(
                "Select translation direction:",
                ["Norwegian → English", "English → Norwegian"],
                horizontal=True,
                label_visibility="collapsed"
                )

                from_lang = "Norwegian" if direction.startswith("Norwegian") else "English"
                to_lang = "English" if direction.startswith("Norwegian") else "Norwegian"

                # Add HTML toggle
                preserve_html = st.checkbox("Preserve HTML tags", help="Select this if your input includes HTML tags that should be preserved")

                st.subheader(f"{from_lang} Text")
                input_text = st.text_area(
                label="Input text",
                height=150,
                label_visibility="collapsed",
                key="input_area",
                placeholder=f"Enter {from_lang} text (with or without HTML)..."
                )

                if st.button("Translate", type="primary"):
                if input_text:
                with st.spinner("Translating..."):
                translation, analysis = get_translation_and_analysis(input_text, from_lang, to_lang, preserve_html)
                
                if translation:
                st.subheader(f"{to_lang} Translation")
                    
                # Show raw HTML or rendered version
                show_raw = st.checkbox("Show raw HTML") if preserve_html else False
        if preserve_html:
            if show_raw:
                st.text_area("Raw HTML Output", translation, key="output_raw")
            else:
                st.markdown(translation, unsafe_allow_html=True)
        else:
            st.write(translation)
                    
            if show_raw:
                st.text_area(
                label="Translation output",
                value=translation,
                height=150,
                label_visibility="collapsed",
                key="output_raw"
                )
            else:
                if preserve_html and '<' in translation and '>' in translation:
                st.markdown(translation, unsafe_allow_html=True)
            else:
                st.text_area(
                label="Translation output",
                value=translation,
                height=150,
                label_visibility="collapsed",
                key="output_area"
                )
                    
                if analysis:
                st.subheader("Translation Analysis")
                st.markdown(analysis)
            else:
                st.warning("Please enter text to translate")

                st.caption("Created by CICERO • Powered by Claude API")

                if __name__ == "__main__":
                main()
