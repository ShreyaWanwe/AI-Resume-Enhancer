import os
import google.generativeai as genai
import spacy
import re
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"))

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

def extract_keywords(text):
    """Extract keywords from text using spaCy NLP"""
    if not nlp:
        # Fallback to simple keyword extraction if spaCy is not available
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return list(set(words))
    
    doc = nlp(text)
    keywords = []
    
    for token in doc:
        if (token.is_alpha and 
            not token.is_stop and 
            not token.is_punct and 
            len(token.text) > 2):
            keywords.append(token.lemma_.lower())
    
    return list(set(keywords))

def calculate_ats_score(resume_text, job_description):
    """Calculate ATS compatibility score based on keyword matching"""
    try:
        # Extract keywords from both texts
        resume_keywords = set(extract_keywords(resume_text))
        job_keywords = set(extract_keywords(job_description))
        
        if not job_keywords:
            return 0
        
        # Calculate overlap
        matching_keywords = resume_keywords.intersection(job_keywords)
        score = (len(matching_keywords) / len(job_keywords)) * 100
        
        return min(100, round(score))
        
    except Exception as e:
        print(f"Error calculating ATS score: {e}")
        return 0

def improve_resume(resume_text, job_description):
    """Use Gemini AI to provide resume improvement suggestions"""
    try:
        # Try different model names in order of preference
        model_names = [
            'gemini-1.5-flash',
            'gemini-1.5-pro', 
            'gemini-pro',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro'
        ]
        
        model = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except Exception as e:
                print(f"Failed to load model {model_name}: {e}")
                continue
        
        if not model:
            return "Error: Unable to load any Gemini model. Please check your API key and internet connection."
        
        prompt = f"""
        As an expert resume consultant and ATS optimization specialist, analyze the following resume against the job description and provide detailed, actionable improvement suggestions.

        **Job Description:**
        {job_description}

        **Current Resume:**
        {resume_text}

        Please provide a comprehensive analysis including:

        1. **ATS Optimization:**
           - Missing keywords that should be included
           - Formatting improvements for ATS readability
           - Section organization recommendations

        2. **Content Enhancement:**
           - Skills that should be highlighted or added
           - Experience descriptions that could be improved
           - Quantifiable achievements that could be emphasized

        3. **Keyword Integration:**
           - Specific keywords from the job description to incorporate
           - Natural ways to include these keywords
           - Technical skills alignment

        4. **Overall Structure:**
           - Resume section improvements
           - Professional summary enhancements
           - Action verb recommendations

        5. **Specific Recommendations:**
           - 3-5 concrete, actionable steps to improve the resume
           - Priority order for implementing changes

        Format your response in clear, organized sections with bullet points for easy reading.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error generating suggestions: {str(e)}. Please check your API configuration and internet connection."

def analyze_resume_sections(resume_text):
    """Analyze resume sections and provide structural feedback"""
    sections = {
        'contact_info': bool(re.search(r'(email|phone|@)', resume_text, re.IGNORECASE)),
        'summary': bool(re.search(r'(summary|objective|profile)', resume_text, re.IGNORECASE)),
        'experience': bool(re.search(r'(experience|work|employment)', resume_text, re.IGNORECASE)),
        'education': bool(re.search(r'(education|degree|university|college)', resume_text, re.IGNORECASE)),
        'skills': bool(re.search(r'(skills|technologies|proficient)', resume_text, re.IGNORECASE))
    }
    
    return sections

def list_available_models():
    """List available Gemini models for debugging"""
    try:
        models = genai.list_models()
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
        return available_models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def get_keyword_suggestions(resume_text, job_description):
    """Get specific keyword suggestions based on job description"""
    resume_keywords = set(extract_keywords(resume_text))
    job_keywords = set(extract_keywords(job_description))
    
    missing_keywords = job_keywords - resume_keywords
    
    # Filter out very common words
    common_words = {'work', 'experience', 'team', 'company', 'role', 'position', 'time', 'year'}
    missing_keywords = missing_keywords - common_words
    
    return list(missing_keywords)[:10] 
