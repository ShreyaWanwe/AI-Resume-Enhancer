import os
import streamlit as st
import fitz  # PyMuPDF for PDF processing
from io import BytesIO  # Added missing import
from dotenv import load_dotenv

# Import functions from other modules
from extract_text import extract_text_from_uploaded_file
from gemini_api import improve_resume, calculate_ats_score

# Load environment variables
load_dotenv()

# Streamlit UI
st.set_page_config(page_title="AI Resume Enhancer", layout="wide", page_icon="📄")

# Custom Styling
st.markdown(
    """
    <style>
    .main { 
        background-color: #f8f9fa; 
        padding: 2rem;
    }
    .stTextArea textarea { 
        font-size: 14px !important; 
        font-family: 'Consolas', monospace;
    }
    .stButton button { 
        background-color: #28a745; 
        color: white; 
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #218838;
    }
    .stDownloadButton button { 
        background-color: #007bff; 
        color: white; 
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stDownloadButton button:hover {
        background-color: #0056b3;
    }
    .metric-container {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.title("AI Resume Enhancer")
st.markdown("Upload your resume and get AI-powered suggestions to improve it!")


# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Upload Resume")
    uploaded_file = st.file_uploader(
        "Choose your resume file", 
        type=["pdf", "txt", "jpg", "jpeg", "png"],
        help="Supported formats: PDF, TXT, JPG, PNG"
    )
    
    resume_text = ""
    if uploaded_file:
        with st.spinner("🔍 Extracting text..."):
            try:
                if uploaded_file.type == "application/pdf":
                    # Use BytesIO for PDF processing
                    pdf_bytes = BytesIO(uploaded_file.getvalue())
                    doc = fitz.open(stream=pdf_bytes)
                    resume_text = "\n".join([page.get_text("text") for page in doc])
                    doc.close()
                elif uploaded_file.type == "text/plain":
                    resume_text = uploaded_file.getvalue().decode("utf-8")
                else:
                    # Use the extract_text module for images
                    resume_text = extract_text_from_uploaded_file(uploaded_file)
                
                if resume_text.strip():
                    st.success("✅ Text extracted successfully!")
                else:
                    st.warning("⚠️ No text found in the uploaded file.")
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                resume_text = ""

    if resume_text:
        with st.expander("📜 Preview Extracted Text", expanded=False):
            st.text_area("Resume Content", resume_text, height=200, disabled=True)

with col2:
    st.subheader("Job Description")
    job_description = st.text_area(
        "Paste the job description here", 
        height=300,
        placeholder="Enter the complete job description including requirements, responsibilities, and qualifications..."
    )

# Analysis Section
if resume_text and job_description:
    st.markdown("---")
    
    # ATS Score Analysis
    with st.spinner("🔍 Calculating ATS Score..."):
        try:
            ats_score = calculate_ats_score(resume_text, job_description)
            
            col1, col2, col3 = st.columns(3)
            
            with col2:
                st.metric(
                    label="ATS Compatibility Score", 
                    value=f"{ats_score}%"
                )
                
                # Score interpretation
                if ats_score >= 80:
                    st.success("🎉 Excellent! Your resume is well-optimized for ATS systems.")
                elif ats_score >= 60:
                    st.warning("⚠️ Good match, but there's room for improvement.")
                elif ats_score >= 40:
                    st.warning("🔄 Moderate match. Consider optimizing with more relevant keywords.")
                else:
                    st.error("❌ Low ATS score. Your resume needs significant optimization.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error calculating ATS score: {str(e)}")

# AI Suggestions
if st.button("Get AI-Powered Suggestions", type="primary"):
    if resume_text.strip() and job_description.strip():
        with st.spinner("Generating personalized suggestions..."):
            try:
                result = improve_resume(resume_text, job_description)
                # Handle both tuple and string returns
                if isinstance(result, tuple):
                    ai_suggestions, _ = result
                else:
                    ai_suggestions = result
                
                # Display AI suggestions in a nicely formatted container
                st.markdown("---")
                st.subheader("AI-Powered Resume Enhancement Report")
                
                # Create a container with custom styling for the suggestions
                with st.container():
                    
                    # Display the suggestions with proper markdown formatting
                    st.markdown(ai_suggestions)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Add a success message
                st.success("✅ Analysis complete! Review the suggestions above to optimize your resume.")
                
            except Exception as e:
                st.error(f"⚠️ Error generating suggestions: {str(e)}")
                st.info("Please check your internet connection and API configuration.")
    else:
        st.error("⚠️ Please provide both a resume and a job description.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Your data is processed securely.</p>
    </div>
    """, 
    unsafe_allow_html=True
)
