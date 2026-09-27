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
st.caption("Upload a resume for an ATS-style score, or paste a job description too for a targeted match.")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
job_description = st.text_area(
    "Optional: paste a job description to score relevance against a specific role",
    height=150,
)


def extract_text_from_pdf(file):
    reader = PdfReader(file)
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            all_text += page_text + "\n"
    return all_text


def analyze_resume(resume_text, job_description=""):
    """Ask the AI to act like an ATS. If a job description is given, also
    score how well the resume matches that specific role."""

    if job_description.strip():
        task_instructions = f"""Also compare the resume against this job description
and include a "job_match_score" (0-100) for how well it fits this specific role,
plus a "missing_keywords" list of important terms from the job description that
are missing from the resume.

Job description:
\"\"\"{job_description}\"\"\"
"""
        extra_json_fields = ''',
  "job_match_score": <a number from 0 to 100>,
  "missing_keywords": ["keyword", "keyword"]'''
    else:
        task_instructions = ""
        extra_json_fields = ""

    prompt = f"""You are an ATS (Applicant Tracking System) resume reviewer.
Analyze the resume text below and respond with ONLY valid JSON, no other text,
in exactly this shape:

{{
  "score": <a number from 0 to 100>,
  "strengths": ["short point", "short point"],
  "improvements": ["short actionable suggestion", "short actionable suggestion"]{extra_json_fields}
}}

{task_instructions}

Resume text:
\"\"\"{resume_text}\"\"\"
"""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )
    raw_reply = response.choices[0].message.content
    cleaned = raw_reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def score_color(score):
    """Return a color word based on score range, for simple visual feedback."""
    if score >= 75:
        return "green"
    elif score >= 50:
        return "orange"
    else:
        return "red"


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
                    result = analyze_resume(resume_text, job_description)
                except json.JSONDecodeError:
                    st.error("The AI's response wasn't valid JSON — try clicking Analyze again.")
                    result = None

            if result:
                color = score_color(result["score"])
                st.markdown(f"### ATS Score: :{color}[{result['score']}/100]")
                st.progress(result["score"] / 100)

                if "job_match_score" in result:
                    match_color = score_color(result["job_match_score"])
                    st.markdown(
                        f"### Job Match Score: :{match_color}[{result['job_match_score']}/100]"
                    )
                    st.progress(result["job_match_score"] / 100)

                    if result.get("missing_keywords"):
                        st.subheader("🔑 Missing keywords from the job description")
                        st.write(", ".join(result["missing_keywords"]))

                st.subheader("✅ Strengths")
                for point in result["strengths"]:
                    st.write(f"- {point}")

                st.subheader("🛠️ Suggested improvements")
                for point in result["improvements"]:
                    st.write(f"- {point}")
else:
    st.info("Upload a PDF resume above to get started.")
