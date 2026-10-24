import streamlit as st
from pathlib import Path

# ពាក្យសម្ងាត់សម្រាប់ដាក់/លុបរឿង (បើចង់ប្តូរ កែតែបន្ទាត់នេះ)
PASSWORD = "smey1234"

st.set_page_config(page_title="រឿងរបស់ខ្ញុំ", page_icon="🎬")
st.title("🎬 រឿងរបស់ខ្ញុំ")

VIDEO_DIR = Path("videos")
VIDEO_DIR.mkdir(exist_ok=True)
EXT = (".mp4", ".mov", ".webm", ".mkv")

if "admin" not in st.session_state:
    st.session_state.admin = False

tab_watch, tab_admin = st.tabs(["📺 មើលរឿង", "🔒 ម្ចាស់គេហទំព័រ"])

# ---------- ម្ចាស់គេហទំព័រ (ត្រូវមានពាក្យសម្ងាត់) ----------
with tab_admin:
    if not st.session_state.admin:
        pw = st.text_input("ពាក្យសម្ងាត់", type="password")
        if st.button("ចូល"):
            if pw == PASSWORD:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("ពាក្យសម្ងាត់មិនត្រឹមត្រូវ")
    else:
        st.write("ដាក់តែវីដេអូដែលអ្នកធ្វើខ្លួនឯង ឬមានសិទ្ធិប្រើប្រាស់ប៉ុណ្ណោះ។")
        files = st.file_uploader(
            "ជ្រើសរើសវីដេអូ",
            type=["mp4", "mov", "webm", "mkv"],
            accept_multiple_files=True,
        )
        if files:
            for f in files:
                (VIDEO_DIR / f.name).write_bytes(f.getbuffer())
            st.success(f"បានរក្សាទុក {len(files)} វីដេអូ! ចូលទៅផ្ទាំង «មើលរឿង»។")
        if st.button("ចាកចេញ"):
            st.session_state.admin = False
            st.rerun()

# ---------- មើលរឿង (អ្នកណាក៏មើលបាន) ----------
with tab_watch:
    q = st.text_input("🔍 ស្វែងរករឿង")
    videos = sorted(p for p in VIDEO_DIR.iterdir() if p.suffix.lower() in EXT)
    videos = [v for v in videos if q.lower() in v.stem.lower()]

    if not videos:
        st.info("មិនទាន់មានរឿងទេ។")

    for v in videos:
        st.subheader(v.stem)
        st.video(str(v))
        col1, col2 = st.columns(2)
        with col1:
            with open(v, "rb") as fh:
                st.download_button("⬇ ទាញយក", fh, file_name=v.name,
                                   key=f"dl_{v.name}")
        with col2:
            if st.session_state.admin:
                if st.button("🗑 លុប", key=f"rm_{v.name}"):
                    v.unlink()
                    st.rerun()
        st.divider()
