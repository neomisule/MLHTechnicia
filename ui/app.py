import streamlit as st
import asyncio
import sys
import os
from pathlib import Path
from PIL import Image
import tempfile

# Add parent directory to path to import runner
sys.path.append(str(Path(__file__).parent.parent))
from runner import runner

# Page configuration
st.set_page_config(
    page_title="ENSEMBLE",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
def load_css():
    st.markdown("""
        <style>
        /* Main app styling */
        .stApp {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        
        /* Hide streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Title styling */
        .main-title {
            color: #4dd5d5;
            font-size: 4rem;
            font-weight: 300;
            text-align: center;
            margin-top: 3rem;
            margin-bottom: 3rem;
            letter-spacing: 0.3rem;
            writing-mode: vertical-rl;
            text-orientation: mixed;
            position: absolute;
            left: 5%;
            top: 30%;
            transform: translateY(-50%);
        }
        
        /* Container for main content */
        .main-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            margin-left: 15%;
        }
        
        /* Input container styling */
        .input-section {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid #4dd5d5;
            border-radius: 20px;
            padding: 3rem;
            margin-top: 10rem;
            backdrop-filter: blur(10px);
        }
        
        /* Custom input styling */
        .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid #4dd5d5;
            border-radius: 15px;
            color: #ffffff;
            padding: 1.5rem;
            font-size: 1.1rem;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #4dd5d5;
            box-shadow: 0 0 20px rgba(77, 213, 213, 0.3);
        }
        
        /* File uploader styling */
        .uploadedFile {
            background: rgba(77, 213, 213, 0.1);
            border-radius: 10px;
            padding: 0.5rem;
            margin: 0.5rem 0;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #4dd5d5 0%, #3ba8a8 100%);
            color: #1a1a2e;
            border: none;
            border-radius: 15px;
            padding: 1rem 3rem;
            font-size: 1.1rem;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(77, 213, 213, 0.3);
        }
        
        /* Image preview styling */
        .image-preview {
            border: 2px solid #4dd5d5;
            border-radius: 15px;
            padding: 1rem;
            margin: 1rem 0;
            background: rgba(255, 255, 255, 0.05);
        }
        
        /* Result styling */
        .result-container {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid #4dd5d5;
            border-radius: 20px;
            padding: 2rem;
            margin-top: 2rem;
            color: #ffffff;
            backdrop-filter: blur(10px);
        }
        
        /* Loading spinner color */
        .stSpinner > div {
            border-top-color: #4dd5d5 !important;
        }
        
        /* Upload button styling */
        .upload-icon {
            text-align: center;
            font-size: 3rem;
            color: #4dd5d5;
            cursor: pointer;
            margin: 1rem 0;
        }
        
        /* Labels styling */
        .stMarkdown, label {
            color: #4dd5d5 !important;
            font-size: 1.1rem;
        }
        
        /* Success/info messages */
        .stSuccess, .stInfo {
            background: rgba(77, 213, 213, 0.1);
            border-left: 4px solid #4dd5d5;
            color: #ffffff;
        }
        </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []

def main():
    load_css()
    
    # Title (styled like in the image)
    st.markdown('<div class="main-title">ENSEMBLE</div>', unsafe_allow_html=True)
    
    # Main container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Input section
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    
    # Image upload section
    st.markdown("### 📎 Attach Images")
    uploaded_files = st.file_uploader(
        "Click to upload images or drag and drop",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        key="image_uploader",
        help="Upload one or multiple images for analysis"
    )
    
    # Display uploaded images
    if uploaded_files:
        cols = st.columns(len(uploaded_files))
        for idx, (col, uploaded_file) in enumerate(zip(cols, uploaded_files)):
            with col:
                image = Image.open(uploaded_file)
                st.image(image, caption=uploaded_file.name, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Question input
    st.markdown("### 🔍 Your Question")
    question = st.text_input(
        "Enter your question here...",
        placeholder="What would you like to know?",
        label_visibility="collapsed",
        key="question_input"
    )
    
    # Submit button
    submit = st.button("🚀 Analyze", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process the query
    if submit:
        if not question:
            st.warning("⚠️ Please enter a question.")
        elif not uploaded_files:
            st.warning("⚠️ Please upload at least one image.")
        else:
            with st.spinner("🔄 Processing your query..."):
                try:
                    # Save uploaded images to temporary files
                    temp_image_paths = []
                    for uploaded_file in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_image_paths.append(tmp_file.name)
                    
                    # Run the analysis
                    # If multiple images, pass the list; if single, pass as string
                    image_input = temp_image_paths if len(temp_image_paths) > 1 else temp_image_paths[0]
                    result = asyncio.run(runner(question, image_input))
                    st.session_state.result = result
                    
                    # Clean up temporary files
                    for path in temp_image_paths:
                        try:
                            os.unlink(path)
                        except:
                            pass
                    
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    st.exception(e)
    
    # Display result
    if st.session_state.result:
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.markdown("### 📊 Result")
        st.markdown(st.session_state.result)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

