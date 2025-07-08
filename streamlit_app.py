import os
import json
import re
import streamlit as st
from collections import defaultdict
from docx import Document
from PyPDF2 import PdfReader

# --- File Reading Function ---
def read_lines(uploaded_file):
    name = uploaded_file.name.lower()

    if name.endswith(".txt"):
        return [
            line.strip()
            for line in uploaded_file.read().decode("utf-8").splitlines()
            if line.strip()
        ]

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
                lines.extend(
                    [line.strip() for line in text.split("\n") if line.strip()]
                )
        return lines

    else:
        raise ValueError(f"Unsupported file format: {name}")


# --- Matching & Keyword Functions ---
def exact_line_matches(lines1, lines2):
    index_map = {line: idx for idx, line in enumerate(lines2)}
    matches = []
    for i, line1 in enumerate(lines1):
        if line1 in index_map:
            j = index_map[line1]
            matches.append((i + 1, line1, j + 1, lines2[j]))
    return matches


def extract_keywords(lines):
    keyword_map = defaultdict(list)
    for i, line in enumerate(lines):
        keywords = re.findall(r"\b\w+\b", line.lower())
        for word in keywords:
            keyword_map[word].append((i + 1, line))
    return keyword_map


def keyword_search(keyword, kw1, kw2):
    keyword = keyword.lower()
    return kw1.get(keyword, []), kw2.get(keyword, [])


# --- Initialize Session State ---
for key in ["matches", "keywords1", "keywords2"]:
    if key not in st.session_state:
        st.session_state[key] = None


# --- UI ---
st.set_page_config(page_title="📁 File Comparator", layout="wide")
st.title("📁 File Comparison & Keyword Analyzer")
st.markdown(
    "Upload two files to find **exact matching lines** and **shared keywords**. "
    "Supports `.txt`, `.json`, `.docx`, and `.pdf` files."
)

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("📄 Upload File 1", type=["txt", "json", "docx", "pdf"])
with col2:
    file2 = st.file_uploader("📄 Upload File 2", type=["txt", "json", "docx", "pdf"])

if file1 and file2:
    lines1 = read_lines(file1)
    lines2 = read_lines(file2)

    if st.button("🔍 Compare Files"):
        with st.spinner("Comparing lines and extracting keywords..."):
            st.session_state.matches = exact_line_matches(lines1, lines2)
            st.session_state.keywords1 = extract_keywords(lines1)
            st.session_state.keywords2 = extract_keywords(lines2)
        st.success(f"✅ Comparison complete! {len(st.session_state.matches)} exact matches found.")

# --- Display Matching Lines ---
if st.session_state.matches is not None:
    with st.expander(f"📌 View Exact Matching Lines ({len(st.session_state.matches)})", expanded=False):
        for f1_ln, f1_txt, f2_ln, f2_txt in st.session_state.matches:
            st.markdown(f"🔹 **File 1 [Line {f1_ln}]**: `{f1_txt}`")
            st.markdown(f"🔸 **File 2 [Line {f2_ln}]**: `{f2_txt}`")
            st.markdown("---")

# --- Display Overlapping Keywords ---
# --- Keyword Search (non-nested) ---
if st.session_state.keywords1 and st.session_state.keywords2:
    if st.button("🧠 Show Overlapping Keywords"):
        common_keywords = sorted(set(st.session_state.keywords1) & set(st.session_state.keywords2))
        st.subheader(f"🧠 Overlapping Keywords ({len(common_keywords)})")
        if common_keywords:
            st.code(", ".join(common_keywords[:100]), language="text")
        else:
            st.info("No overlapping keywords found.")

    st.subheader("🔎 Search for a Specific Keyword in Both Files")
    search_kw = st.text_input("Enter keyword")
    if search_kw:
        f1_hits, f2_hits = keyword_search(search_kw, st.session_state.keywords1, st.session_state.keywords2)

        st.markdown(f"### Results for: `{search_kw}`")
        if f1_hits:
            st.markdown(f"📘 **In File 1 ({len(f1_hits)} matches)**")
            for ln, txt in f1_hits:
                st.text(f"Line {ln}: {txt}")
        if f2_hits:
            st.markdown(f"📗 **In File 2 ({len(f2_hits)} matches)**")
            for ln, txt in f2_hits:
                st.text(f"Line {ln}: {txt}")
        if not (f1_hits or f2_hits):
            st.warning("No matches found for that keyword.")
