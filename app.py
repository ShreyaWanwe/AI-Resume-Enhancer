import streamlit as st
import fitz  # PyMuPDF for PDF processing
from extract_text import extract_text  # Importing from extract_text.py
from pdf2image import convert_from_path  # Convert PDF to images for OCR
from gemini_api import improve_resume  # Function to improve resume
from io import BytesIO  # For PDF generation
import textwrap
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity(resume_text, job_desc):
    """Calculate the cosine similarity between resume and job description."""
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_text, job_desc])
    similarity_score = cosine_similarity(vectors)[0, 1] * 100  # Convert to percentage
    return round(similarity_score, 2)

# Function to generate a detailed PDF report
def generate_pdf(original_resume, suggestions):
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

    def process_markdown(text):
        """Detects markdown bold (**text**) and removes ** while keeping actual bold formatting."""
        matches = re.findall(r'\*\*(.*?)\*\*', text)  # Find all occurrences of **bold text**
        for match in matches:
            text = text.replace(f"**{match}**", f"<b>{match}</b>")  # Replace Markdown with a placeholder
        return text

    # Title
    y_offset = add_text(page, "Resume Review & Improvement Report", title_font_size, y_offset, bold=True)
    y_offset += 10

    # AI Suggestions Section
    y_offset = add_text(page, "AI Suggestions & Improvements:", section_font_size, y_offset, bold=True)
    y_offset += 5

    # Apply Fix to Remove ** and Use Proper Bold Font
    for line in suggestions.split("\n"):
        processed_line = process_markdown(line)  # Convert **bold** to <b>text</b>
        
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
st.title("📄 Resume Review AI")
st.write("Upload your resume and get AI-powered suggestions to improve it!")

# File Upload Section
uploaded_file = st.file_uploader("Upload your Resume (PDF or Text)", type=["pdf", "txt"])

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

# Job Description Input
st.subheader("📝 Job Description")
job_description = st.text_area("Enter the job description", height=150)
ai_suggestions = ""


# Button Click Logic (AI Suggestions only when button is clicked)
if st.button("✨ Get AI Suggestions"):
    if resume_text.strip() and job_description.strip():  # Ensure both fields are filled
        with st.spinner("Generating AI suggestions... 🤖"):
            try:
                ai_suggestions = improve_resume(resume_text, job_description)  # ✅ Pass both arguments
                st.subheader("💡 AI Suggestions & Improvements")
                st.text_area("Suggested Improvements", ai_suggestions, height=200)
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")  # Catch any errors
    else:
        st.error("⚠️ Please provide both a resume and a job description.")
# ✅ Only show download button if `ai_suggestions` is not empty
if ai_suggestions:
    pdf_report = generate_pdf(resume_text, ai_suggestions)  # Generate PDF
    st.download_button(
        label="📥 Download Report as PDF",
        data=pdf_report,
        file_name="resume_review.pdf",
        mime="application/pdf"
    )
# Resume Match Analysis
if resume_text and ai_suggestions:
    with st.spinner("Analyzing... 🔎"):
        match_score = calculate_similarity(resume_text, ai_suggestions)  # Directly use extracted text

        st.subheader("🔍 Resume Match Score:")
        st.metric(label="Match Percentage", value=f"{match_score}%", delta=None)

        # Feedback Based on Score
        if match_score > 80:
            st.success("✅ Great match! Your resume aligns well with the job description.")
        elif match_score > 60:
            st.warning("⚠️ Decent match, but consider adding more relevant keywords.")
        else:
            st.error("❌ Low match. Try optimizing your resume with job-specific keywords.")

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** Use clear, concise bullet points and quantifiable achievements in your resume!")
