import os
import json
import re
import streamlit as st
from collections import defaultdict
from docx import Document
from PyPDF2 import PdfReader


def read_lines(uploaded_file):
    name = uploaded_file.name.lower()

    if name.endswith(".txt"):
        return [line.strip() for line in uploaded_file.read().decode("utf-8").splitlines() if line.strip()]

    elif name.endswith(".json"):
        data = json.load(uploaded_file)
        lines = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    lines.append(item.strip())
                elif isinstance(item, dict):
                    for v in item.values():
                        if isinstance(v, str) and v.strip():
                            lines.append(v.strip())
                            break
        elif isinstance(data, dict):
            for v in data.values():
                if isinstance(v, str) and v.strip():
                    lines.append(v.strip())
        return lines

    elif name.endswith(".docx"):
        doc = Document(uploaded_file)
        return [para.text.strip() for para in doc.paragraphs if para.text.strip()]

    elif name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        lines = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                lines.extend([line.strip() for line in text.split("\n") if line.strip()])
        return lines

    else:
        raise ValueError(f"Unsupported file format: {name}")


def exact_line_matches(lines1, lines2):
    set2 = set(lines2)
    matches = []
    for i, line1 in enumerate(lines1):
        if line1 in set2:
            j = lines2.index(line1)
            matches.append((i + 1, line1, j + 1, lines2[j]))
    return matches


def extract_keywords(lines):
    keyword_map = defaultdict(list)
    for i, line in enumerate(lines):
        keywords = re.findall(r'\b\w+\b', line.lower())
        for word in keywords:
            keyword_map[word].append((i + 1, line))
    return keyword_map


def keyword_search(keyword, kw1, kw2):
    keyword = keyword.lower()
    return kw1.get(keyword, []), kw2.get(keyword, [])


# Streamlit App
st.title("🔍 File Matching & Keyword Analyzer")
st.markdown("Compare two text-based files for **exact matching lines** and overlapping keywords.")

file1 = st.file_uploader("Upload File 1", type=["txt", "json", "docx", "pdf"])
file2 = st.file_uploader("Upload File 2", type=["txt", "json", "docx", "pdf"])

if file1 and file2:
    try:
        lines1 = read_lines(file1)[:5000]
        lines2 = read_lines(file2)[:5000]

        with st.spinner("Finding exact matching lines..."):
            matches = exact_line_matches(lines1, lines2)

        st.subheader(f"🔗 Exact Matching Lines ({len(matches)})")
        for f1_ln, f1_txt, f2_ln, f2_txt in matches:
            st.markdown(f"**File 1 [Line {f1_ln}]**: {f1_txt}")
            st.markdown(f"**File 2 [Line {f2_ln}]**: {f2_txt}")
            st.markdown("---")

        # Keyword overlap and search
        keywords1 = extract_keywords(lines1)
        keywords2 = extract_keywords(lines2)
        common_keywords = sorted(set(keywords1) & set(keywords2))

        st.subheader(f"🧠 Overlapping Keywords ({len(common_keywords)})")
        st.text(", ".join(common_keywords[:100]))

        search_kw = st.text_input("🔎 Search for a specific keyword in both files:")
        if search_kw:
            f1_hits, f2_hits = keyword_search(search_kw, keywords1, keywords2)

            st.markdown(f"### Results for keyword: `{search_kw}`")
            if f1_hits:
                st.markdown("**In File 1:**")
                for ln, txt in f1_hits:
                    st.text(f"Line {ln}: {txt}")
            if f2_hits:
                st.markdown("**In File 2:**")
                for ln, txt in f2_hits:
                    st.text(f"Line {ln}: {txt}")
            if not (f1_hits or f2_hits):
                st.info("Keyword not found in either file.")

    except Exception as e:
        st.error(f"Error: {e}")