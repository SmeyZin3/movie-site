import requests
import streamlit as st
from pathlib import Path
from urllib.parse import quote

# ពាក្យសម្ងាត់សម្រាប់ដាក់/លុបរឿង (បើចង់ប្តូរ កែតែបន្ទាត់នេះ)
PASSWORD = "smey1234"

st.set_page_config(page_title="រឿងរបស់ខ្ញុំ", page_icon="🎬")
st.title("🎬 រឿងរបស់ខ្ញុំ")

VIDEO_DIR = Path("videos")
VIDEO_DIR.mkdir(exist_ok=True)
EXT = (".mp4", ".mov", ".webm", ".mkv")

if "admin" not in st.session_state:
    st.session_state.admin = False

COLLECTIONS = {
    "ភាពយន្តវែង (Feature Films)": "feature_films",
    "ភាពយន្តចាស់ Prelinger": "prelinger",
    "ភាពយន្តបើកចំហ (Open Source)": "opensource_movies",
}


@st.cache_data(ttl=3600, show_spinner=False)
def search_archive(q, collection):
    query = q.strip() if q.strip() else "*"
    params = {
        "q": f"({query}) AND mediatype:movies AND collection:({collection})",
        "fl[]": ["identifier", "title"],
        "rows": 15,
        "output": "json",
        "sort[]": "downloads desc",
    }
    r = requests.get("https://archive.org/advancedsearch.php",
                     params=params, timeout=20)
    r.raise_for_status()
    return r.json()["response"]["docs"]


@st.cache_data(ttl=3600, show_spinner=False)
def get_video(identifier):
    r = requests.get(f"https://archive.org/metadata/{identifier}", timeout=20)
    r.raise_for_status()
    data = r.json()
    mp4s = [f for f in data.get("files", [])
            if f.get("name", "").lower().endswith(".mp4")]
    if not mp4s:
        return None, {}
    best = [f for f in mp4s if "h.264" in f.get("format", "").lower()] or mp4s
    return best[0]["name"], data.get("metadata", {})


tab_watch, tab_archive, tab_admin = st.tabs(
    ["📺 រឿងរបស់ខ្ញុំ", "🌐 រឿងឥតគិតថ្លៃ", "🔒 ម្ចាស់"]
)

# ---------- រឿងឥតគិតថ្លៃពី Internet Archive ----------
with tab_archive:
    st.write("ស្វែងរករឿង Public Domain / ឥតគិតថ្លៃពី Internet Archive "
             "(មើលផ្ទាល់ មិនបានរក្សាទុកក្នុងកម្មវិធីទេ)។")
    col_name = st.selectbox("ប្រភេទ", list(COLLECTIONS.keys()))
    kw = st.text_input("🔍 ស្វែងរក (ភាសាអង់គ្លេស ឧ. comedy, war, love)")
    try:
        docs = search_archive(kw, COLLECTIONS[col_name])
    except Exception:
        docs = []
        st.error("មិនអាចតភ្ជាប់ Internet Archive បានទេ សូមព្យាយាមម្តងទៀត។")

    if docs:
        titles = {d["identifier"]: d.get("title", d["identifier"]) for d in docs}
        pick = st.selectbox("ជ្រើសរើសរឿង", list(titles.keys()),
                            format_func=lambda i: str(titles[i]))
        try:
            fname, meta = get_video(pick)
        except Exception:
            fname, meta = None, {}
        if fname:
            url = f"https://archive.org/download/{pick}/{quote(fname)}"
            st.subheader(str(titles[pick]))
            st.video(url)
            st.link_button("⬇ ទាញយក", url)
            lic = meta.get("licenseurl")
            if lic:
                st.caption(f"អាជ្ញាប័ណ្ណ: {lic}")
            st.link_button("ℹ ពិនិត្យអាជ្ញាប័ណ្ណនៅ Internet Archive",
                           f"https://archive.org/details/{pick}")
        else:
            st.warning("រឿងនេះគ្មានឯកសារ MP4 សូមជ្រើសរឿងផ្សេង។")
    elif kw:
        st.info("រកមិនឃើញ សូមសាកពាក្យផ្សេង។")

# ---------- ម្ចាស់ (ត្រូវមានពាក្យសម្ងាត់) ----------
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
            st.success(f"បានរក្សាទុក {len(files)} វីដេអូ!")
        if st.button("ចាកចេញ"):
            st.session_state.admin = False
            st.rerun()

# ---------- រឿងរបស់ខ្ញុំ ----------
with tab_watch:
    q = st.text_input("🔍 ស្វែងរករឿងរបស់ខ្ញុំ")
    videos = sorted(p for p in VIDEO_DIR.iterdir() if p.suffix.lower() in EXT)
    videos = [v for v in videos if q.lower() in v.stem.lower()]

    if not videos:
        st.info("មិនទាន់មានរឿងទេ។ មើលរឿងឥតគិតថ្លៃនៅផ្ទាំង 🌐។")

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
        
