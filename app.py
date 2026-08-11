import os
import json
import streamlit as st
from pypdf import PdfReader
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄")
st.title("📄 AI Resume Analyzer")
st.caption("Day 2: now scores your resume and gives improvement suggestions")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])


def extract_text_from_pdf(file):
    reader = PdfReader(file)
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            all_text += page_text + "\n"
    return all_text


def analyze_resume(resume_text):
    """Ask the AI to act like an ATS and return a score + suggestions as JSON."""
    prompt = f"""You are an ATS (Applicant Tracking System) resume reviewer.
Analyze the resume text below and respond with ONLY valid JSON, no other text,
in exactly this shape:

{{
  "score": <a number from 0 to 100>,
  "strengths": ["short point", "short point"],
  "improvements": ["short actionable suggestion", "short actionable suggestion"]
}}

Resume text:
\"\"\"{resume_text}\"\"\"
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )
    raw_reply = response.choices[0].message.content

    # The model sometimes wraps JSON in ```json fences even when asked not to —
    # strip those out before parsing, just in case.
    cleaned = raw_reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    return json.loads(cleaned)


if uploaded_file is not None:
    with st.spinner("Reading your resume..."):
        resume_text = extract_text_from_pdf(uploaded_file)

    if not resume_text.strip():
        st.error("Couldn't extract any text — try a different PDF (not a scanned image).")
    else:
        with st.expander("📃 View extracted text"):
            st.text(resume_text)

        if st.button("🔍 Analyze Resume"):
            with st.spinner("Analyzing with AI..."):
                try:
                    result = analyze_resume(resume_text)
                except json.JSONDecodeError:
                    st.error("The AI's response wasn't valid JSON — try clicking Analyze again.")
                    result = None

            if result:
                st.metric("ATS Score", f"{result['score']}/100")

                st.subheader("✅ Strengths")
                for point in result["strengths"]:
                    st.write(f"- {point}")

                st.subheader("🛠️ Suggested improvements")
                for point in result["improvements"]:
                    st.write(f"- {point}")
else:
    st.info("Upload a PDF resume above to get started.")
