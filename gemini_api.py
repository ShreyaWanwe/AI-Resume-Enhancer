import os
import google.generativeai as genai
import spacy
import re

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Set up Google Gemini API key securely
genai.configure(api_key="YOUR_GEMINI_API_KEY")


def preprocess_text(text):
    """Cleans and normalizes text by removing unnecessary formatting issues."""
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    text = re.sub(r'•|\*|- ', '• ', text)  # Standardize bullet points
    return text


def extract_entities(resume_text):
    """Extracts key entities like PERSON, ORG, and GPE from the resume."""
    doc = nlp(resume_text)
    entities = {ent.label_: ent.text for ent in doc.ents}
    return entities


def find_missing_keywords(resume_text, job_description):
    """Finds missing job-related keywords in the resume."""
    resume_doc = nlp(resume_text.lower())
    job_doc = nlp(job_description.lower())

    resume_keywords = {token.lemma_ for token in resume_doc if not token.is_stop and token.is_alpha}
    job_keywords = {token.lemma_ for token in job_doc if not token.is_stop and token.is_alpha}

    missing_keywords = job_keywords - resume_keywords
    return missing_keywords, job_keywords


def calculate_ats_score(resume_text, job_description):
    """Calculates an improved ATS Score considering multiple factors beyond keyword matching."""
    resume_text = preprocess_text(resume_text)  

    # Step 1: Extract missing keywords and existing job-related terms
    missing_keywords, job_keywords = find_missing_keywords(resume_text, job_description)
    matched_keywords = job_keywords - missing_keywords
    
    # **New Scoring System**
    keyword_match_score = (len(matched_keywords) / len(job_keywords)) * 30 if job_keywords else 0  # 30%
    
    # **Step 2: Experience Relevance (20%)**
    experience_relevance_score = 20 if "experience" in resume_text.lower() else 10  # Checks if 'Experience' section exists

    # **Step 3: Skill Density (20%)**
    skills_mentioned = len([word for word in resume_text.split() if word in job_keywords])
    skill_density_score = min((skills_mentioned / 10) * 20, 20)  # Caps at 20%

    # **Step 4: Action-Oriented Language (15%)**
    action_verbs = ["developed", "optimized", "designed", "implemented", "led", "achieved", "created", "engineered"]
    action_verb_count = sum(resume_text.lower().count(verb) for verb in action_verbs)
    action_language_score = min((action_verb_count / 5) * 15, 15)  # Caps at 15%

    # **Step 5: Formatting & Readability (15%)**
    formatting_issues = sum([
        1 if "table" in resume_text.lower() else 0,  # Avoiding tables (ATS struggles with them)
        1 if len(resume_text) > 2000 else 0  # Checking if resume is overly long
    ])
    formatting_score = 15 - (formatting_issues * 5)  # Deduct 5 points per formatting issue

    # **Final ATS Score Calculation**
    ats_score = round(
        keyword_match_score +
        experience_relevance_score +
        skill_density_score +
        action_language_score +
        formatting_score,
        2
    )

    return ats_score



def improve_resume(resume_text, job_description):
    """Generates detailed improvement suggestions along with project recommendations."""
    
    resume_text = preprocess_text(resume_text)  # Normalize formatting
    extracted_entities = extract_entities(resume_text)
    missing_keywords, _ = find_missing_keywords(resume_text, job_description)
    ats_score = calculate_ats_score(resume_text, job_description)

    missing_keywords_str = ", ".join(missing_keywords) if missing_keywords else "None"

    prompt = f"""
You are an expert in resume optimization and ATS compliance. Your job is to analyze the given resume and provide **detailed, structured suggestions for improvement** based on the job description.

### **Important Instruction:**
🚨 *Ignore formatting issues from text extraction.* Focus **only** on **content relevance**, **keyword optimization**, and **ATS alignment**.

### **ATS Score: {ats_score}%**
- Analyze missing keywords and recommend how to integrate them effectively.
- Provide **justifications** for all suggested changes.

---
### **Extracted Resume Details:**
- **Name**: {extracted_entities.get('PERSON', 'Not Found')}
- **Companies Worked At**: {extracted_entities.get('ORG', 'Not Found')}
- **Location**: {extracted_entities.get('GPE', 'Not Found')}
- **Missing Keywords from JD**: {missing_keywords_str}

### **Job Description:**
{job_description}

### **Original Resume (Preprocessed Text):**
{resume_text}

---
### **Expected Output:**
#### **📌 Improvement Suggestions**
- List clear **areas for enhancement** in skills, experience, and language.
- Explain **why** each change is necessary for better ATS optimization.
- Suggest **keyword placements** to improve ranking.
- Offer **industry-standard recommendations** to align with recruiter expectations.

#### **🛠️ Recommended Projects**
- **Suggest 2-3 project ideas** the candidate can work on **before applying** for this role.
- Each project should be **aligned with missing keywords** and the **job description**.
- Explain **how** each project enhances the resume and **helps land the job**.

#### **📊 ATS Score Analysis**
- Discuss how the current resume performs in keyword matching.
- Suggest **strategies to improve ATS score** based on missing keywords.
"""

    model = genai.GenerativeModel("gemini-1.5-pro-latest")  
    response = model.generate_content(prompt)  
    improvement_suggestions = response.text  

    return improvement_suggestions, ats_score


if __name__ == "__main__":
    sample_resume = "John Doe - Software Engineer with experience in Python and Java."
    sample_job = "Looking for a Software Engineer with experience in AI, ML, and cloud computing."
    suggestions, score = improve_resume(sample_resume, sample_job)

    print("Improvement Suggestions:\n", suggestions)
    print("\nATS Score:", score)
