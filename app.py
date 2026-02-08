import streamlit as st
import os
import textwrap
from gtts import gTTS


from PyPDF2 import PdfReader
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from ai.brain import generate_learning_content

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="VedaAi", layout="centered")
st.title("📘 VEDA AI – AN AI Learning Assistant")
st.caption("Type text or upload files. Choose outputs. Press Generate.")

# ---------------- SESSION STATE ----------------
if "result" not in st.session_state:
    st.session_state.result = None

# ---------------- FILE TEXT EXTRACTOR ----------------
def extract_text_from_files(files):
    text = ""
    for f in files:
        if f.type == "application/pdf":
            reader = PdfReader(f)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"

        elif f.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(f)
            for p in doc.paragraphs:
                text += p.text + "\n"

        elif f.type == "text/plain":
            text += f.read().decode("utf-8") + "\n"

    return text

# ---------------- INPUT FORM ----------------
with st.form("study_form"):
    user_input = st.text_area(
        "📝 Enter topic / paragraph / question",
        height=200
    )

    uploaded_files = st.file_uploader(
        "📂 Drag & drop PDF / Word / Text files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )

    st.markdown("### ⚙️ Output Options")

    enable_audio = st.checkbox("🔊 Audio Explanation", value=True)

    diagram_type = st.selectbox(
        "📊 Diagram Type",
        ["None", "Flowchart", "Tree Diagram", "Process Diagram"]
    )

    enable_pdf = st.checkbox("📄 Download as PDF", value=True)

    submitted = st.form_submit_button("🚀 Generate")

# ---------------- GENERATION ----------------
if submitted:
    file_text = extract_text_from_files(uploaded_files)

    final_input = user_input.strip()
    if file_text:
        final_input += "\n\n" + file_text

    if not final_input.strip():
        st.warning("Please enter text or upload a file.")
        st.stop()

    with st.spinner("🧠 Generating learning content..."):
        st.session_state.result = generate_learning_content(final_input, diagram_type)

# ---------------- OUTPUT ----------------
if st.session_state.result:
    result = st.session_state.result

    # -------- TEXT --------
    st.header(result["topic"])
    st.write(result["explanation"])

    # -------- AUDIO --------
    if enable_audio:
        st.subheader("🎧 Audio Explanation")

        os.makedirs("media/audio", exist_ok=True)
        audio_path = "media/audio/explanation.mp3"

        gTTS(result["explanation"]).save(audio_path)
        st.audio(audio_path)

    # -------- VISUAL DIAGRAM (STEPS) --------
    diagram = result.get("diagram", {})

    if diagram_type != "None" and diagram.get("steps"):
        st.subheader("📊 Visual Concept Diagram")

        for i, step in enumerate(diagram["steps"], 1):
            st.markdown(
                f"""
                <div style="
                    padding:14px;
                    margin:10px 0;
                    border-left:6px solid #4CAF50;
                    background-color:#f4f9f4;
                    border-radius:8px;
                    font-size:16px;
                    color:black;
                ">
                <b>Step {i}:</b> {step}
                </div>
                """,
                unsafe_allow_html=True
            )

    # -------- RESOURCES --------
    st.subheader("🔗 Best Resources to Refer")

    resources = result.get("resources", {})
    topic_query = result["topic"].replace(" ", "+")

    col1, col2, col3 = st.columns(3)

    # ✅ YOUTUBE (SEARCH-BASED, ALWAYS WORKS)
    with col1:
        yt_search_url = f"https://www.youtube.com/results?search_query={topic_query}"
        st.markdown(
            f"▶️ **YouTube**  \n[Best videos on this topic]({yt_search_url})"
        )

    with col2:
        web = resources.get("website", {})
        if web.get("url"):
            st.markdown(f"🌐 **Website**  \n[{web['title']}]({web['url']})")

    with col3:
        art = resources.get("article", {})
        if art.get("url"):
            st.markdown(f"📄 **Article**  \n[{art['title']}]({art['url']})")

    # -------- PDF --------
    if enable_pdf:
        st.subheader("📄 Download Notes")

        os.makedirs("media", exist_ok=True)
        pdf_path = "media/StudyLM_Notes.pdf"

        c = canvas.Canvas(pdf_path, pagesize=A4)
        textobject = c.beginText(40, 800)

        # Title
        textobject.setFont("Helvetica-Bold", 16)
        textobject.textLine(result["topic"])
        textobject.textLine("")

        # Explanation
        textobject.setFont("Helvetica", 11)
        for line in result["explanation"].split("\n"):
            for wrapped in textwrap.wrap(line, 90):
                textobject.textLine(wrapped)

        # Resources
        textobject.textLine("")
        textobject.setFont("Helvetica-Bold", 12)
        textobject.textLine("Best Resources:")

        textobject.setFont("Helvetica", 11)
        textobject.textLine(f"- YouTube search: {yt_search_url}")

        for key in ["website", "article"]:
            item = resources.get(key, {})
            if item.get("title"):
                textobject.textLine(f"- {item['title']}")

        c.drawText(textobject)
        c.save()

        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇️ Download PDF",
                f,
                file_name="StudyLM_Notes.pdf"
            )
