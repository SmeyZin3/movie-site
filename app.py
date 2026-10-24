import streamlit as st
from pathlib import Path

st.set_page_config(page_title="រឿងរបស់ខ្ញុំ", page_icon="🎬")
st.title("🎬 រឿងរបស់ខ្ញុំ")

VIDEO_DIR = Path("videos")
VIDEO_DIR.mkdir(exist_ok=True)

tab_watch, tab_upload = st.tabs(["📺 មើលរឿង", "⬆ ដាក់រឿងថ្មី"])

# ---------- ដាក់រឿងថ្មី ----------
with tab_upload:
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

# ---------- មើលរឿង ----------
with tab_watch:
    q = st.text_input("🔍 ស្វែងរករឿង")
    videos = sorted(
        p for p in VIDEO_DIR.iterdir()
        if p.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv")
    )
    videos = [v for v in videos if q.lower() in v.stem.lower()]

    if not videos:
        st.info("មិនទាន់មានរឿងទេ។ ទៅផ្ទាំង «ដាក់រឿងថ្មី» ដើម្បីបន្ថែម។")

    for v in videos:
        st.subheader(v.stem)
        st.video(str(v))
        col1, col2 = st.columns(2)
        with col1:
            with open(v, "rb") as fh:
                st.download_button(
                    "⬇ ទាញយក",
                    fh,
                    file_name=v.name,
                    key=f"dl_{v.name}",
                )
        with col2:
            if st.button("🗑 លុប", key=f"rm_{v.name}"):
                v.unlink()
                st.rerun()
        st.divider()


