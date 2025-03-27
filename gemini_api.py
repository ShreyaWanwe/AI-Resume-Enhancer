import google.generativeai as genai
import spacy

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Set up Google Gemini API key
genai.configure(api_key="YOUR_GEMINI_API_KEY")

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
    return missing_keywords

def improve_resume(resume_text, job_description):
    """Improves a resume based on job description using Google Gemini AI."""
    
    extracted_entities = extract_entities(resume_text)
    missing_keywords = find_missing_keywords(resume_text, job_description)
    missing_keywords_str = ", ".join(missing_keywords) if missing_keywords else "None"

    prompt = f"""
You are an expert resume reviewer and writer with deep knowledge of industry best practices. 
Your task is to refine and optimize the following resume based on the given job description. 
Ensure that the resume is **impactful, concise, and keyword-rich**, making it highly effective 
for recruiters and Applicant Tracking Systems (ATS).

### **Guidelines for Improvement:**
1. **Enhance clarity & structure**: Improve sentence structure while keeping it **concise**.
2. **Use strong action verbs**: Replace weak phrases with powerful, results-driven language.
3. **Quantify achievements**: Wherever possible, add numbers (e.g., "Increased efficiency by 30%").
4. **Keyword optimization**: Ensure relevant **skills & technologies** from the job description are naturally incorporated.
5. **Professional tone**: Keep it **formal yet engaging**, avoiding unnecessary fluff.
6. **Remove redundancy**: Ensure each section is **precise** and **adds value**.

---
### Extracted Resume Details:
- **Name**: {extracted_entities.get('PERSON', 'Not Found')}
- **Companies Worked At**: {extracted_entities.get('ORG', 'Not Found')}
- **Location**: {extracted_entities.get('GPE', 'Not Found')}
- **Missing Keywords from JD**: {missing_keywords_str}

### **Job Description:**
{job_description}

### **Original Resume:**
{resume_text}

---

### **Expected Output:**
#### **📌 Updated Resume (Refined & Optimized Version)**
[Provide the improved version of the resume with all necessary modifications.]

#### **💡 Key Improvements & Suggestions**
- List the **major changes** you made to improve the resume.
- Explain how these changes will make the resume more effective.

---
Keep the formatting **clean and readable**. Maintain a professional, ATS-friendly layout.
"""
    
    model = genai.GenerativeModel("gemini-1.5-pro-latest")  
    response = model.generate_content(prompt)  
    updated_resume = response.text  

    return updated_resume  

if __name__ == "__main__":
    sample_resume = "John Doe - Software Engineer with experience in Python and Java."
    sample_job = "Looking for a Software Engineer with experience in AI, ML, and cloud computing."
    print(improve_resume(sample_resume, sample_job))
