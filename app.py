import streamlit as st
from pypdf import PdfReader

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄")
st.title("📄 AI Resume Analyzer")
st.caption("Day 1: upload a resume and see the extracted text — AI scoring comes on Day 2")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])


def extract_text_from_pdf(file):
    """Read every page of the uploaded PDF and join their text together."""
    reader = PdfReader(file)
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:  # some pages (e.g. pure images) may return None
            all_text += page_text + "\n"
    return all_text


if uploaded_file is not None:
    with st.spinner("Reading your resume..."):
        resume_text = extract_text_from_pdf(uploaded_file)

    if resume_text.strip():
        st.success(f"Extracted {len(resume_text)} characters from your resume.")
        with st.expander("📃 View extracted text"):
            st.text(resume_text)
    else:
        st.error(
            "Couldn't extract any text. This usually means the PDF is a scanned "
            "image rather than real text — try a different file."
        )
else:
    st.info("Upload a PDF resume above to get started.")
