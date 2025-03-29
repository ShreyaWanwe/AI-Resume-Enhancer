import streamlit as st
import fitz  # PyMuPDF for PDF processing
from extract_text import extract_text  # Importing from extract_text.py
from pdf2image import convert_from_path  # Convert PDF to images for OCR
from gemini_api import improve_resume, calculate_ats_score  # Function to improve resume
from io import BytesIO  # For PDF generation
import textwrap
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Function to generate a detailed PDF report
def generate_pdf(original_resume, suggestions):
    if isinstance(suggestions, tuple):
        suggestions = " ".join(map(str, suggestions))  # Convert tuple to string
    
    pdf_bytes = BytesIO()
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 page

    # Define styling
    title_font_size = 18
    section_font_size = 14
    body_font_size = 11
    wrap_width = 80  # Characters per line before wrapping
    y_offset = 50  # Starting Y position

    def wrap_text(text, width=wrap_width):
        """Wraps text to prevent cutoff issues."""
        return textwrap.fill(text, width)

    def add_text(page, text, fontsize, y_offset, bold=False):
        """Adds text to the PDF with correct formatting."""
        font = "helvetica-bold" if bold else "helvetica"
        wrapped_text = wrap_text(text)
        for line in wrapped_text.split("\n"):
            page.insert_text((50, y_offset), line, fontsize=fontsize, fontname=font, color=(0, 0, 0))
            y_offset += fontsize + 2  # Line spacing
        return y_offset



    # Title
    y_offset = add_text(page, "Resume Review & Improvement Report", title_font_size, y_offset, bold=True)
    y_offset += 10

    # AI Suggestions Section
    y_offset = add_text(page, "AI Suggestions & Improvements:", section_font_size, y_offset, bold=True)
    y_offset += 5

    # Apply Fix to Remove ** and Use Proper Bold Font
    for line in suggestions.split("\n"):

        processed_line = line.strip()        
        # Detect if line contains <b> (meaning it was bold in Markdown)
        if "<b>" in processed_line:
            clean_text = processed_line.replace("<b>", "").replace("</b>", "")  # Remove HTML tags
            y_offset = add_text(page, "• " + clean_text.strip("- "), body_font_size, y_offset, bold=True)
        else:
            y_offset = add_text(page, "• " + processed_line.strip("- "), body_font_size, y_offset)

        if y_offset > 800:  # New page if needed
            page = doc.new_page()
            y_offset = 50

    doc.save(pdf_bytes)
    doc.close()
    pdf_bytes.seek(0)
    return pdf_bytes

# Streamlit UI
# Page Configuration
st.set_page_config(page_title="Resume Review AI", layout="wide")

# Custom Styling
st.markdown(
    """
    <style>
    .main { background-color: #f5f7fa; }
    .stTextArea textarea { font-size: 16px !important; }
    .stButton button { background-color: #4CAF50; color: white; }
    .stDownloadButton button { background-color: #007BFF; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("AI Resume Enhancer")
st.write("Upload your resume and get AI-powered suggestions to improve it!")

uploaded_file = st.file_uploader("Upload your Resume (PDF, TXT, JPG, PNG)", type=["pdf", "txt", "jpg", "png"])
resume_text = ""

if uploaded_file:
    with st.spinner("Extracting text..."):
        if uploaded_file.type == "application/pdf":
            pdf_bytes = uploaded_file.getvalue()
            doc = fitz.open(stream=BytesIO(pdf_bytes))  
            resume_text = "\n".join([page.get_text("text") for page in doc])
        elif uploaded_file.type == "text/plain":
            resume_text = uploaded_file.getvalue().decode("utf-8")

    st.subheader("📜 Extracted Resume Content")
    st.text_area("Preview", resume_text, height=200)

st.subheader("📝 Job Description")
job_description = st.text_area("Enter the job description", height=150)
ai_suggestions = ""

if st.button("✨ Get AI Suggestions"):
    if resume_text.strip() and job_description.strip():
        with st.spinner("Generating AI suggestions... 🤖"):
            try:
                ai_suggestions = improve_resume(resume_text, job_description)
                st.subheader("💡 AI Suggestions & Improvements")
                st.text_area("Suggested Improvements", ai_suggestions, height=200)
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
    else:
        st.error("⚠️ Please provide both a resume and a job description.")

if ai_suggestions:
    pdf_report = generate_pdf(resume_text, ai_suggestions)
    st.download_button(
        label="📥 Download Report as PDF",
        data=pdf_report,
        file_name="resume_review.pdf",
        mime="application/pdf"
    )

if resume_text and job_description:
    with st.spinner("Analyzing ATS Score... 🔎"):
        ats_score = calculate_ats_score(resume_text, job_description)
        st.subheader("📊 ATS Score")
        st.metric(label="Applicant Tracking System Score", value=f"{ats_score}%", delta=None)

        if ats_score > 80:
            st.success("✅ Strong resume! Well-optimized for ATS.")
        elif ats_score > 60:
            st.warning("⚠️ Decent match, but consider refining keywords.")
        else:
            st.error("❌ Low ATS score. Optimize your resume with job-specific keywords.")

st.markdown("---")
st.markdown("💡 **Tip:** Use clear, concise bullet points and quantifiable achievements in your resume!")
