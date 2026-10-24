import json
import re
import uuid
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st

# ពាក្យសម្ងាត់សម្រាប់ដាក់/លុបរឿង (បើចង់ប្តូរ កែតែបន្ទាត់នេះ)
PASSWORD = "smey1234"

st.set_page_config(page_title="រឿងរបស់ខ្ញុំ", page_icon="🎬", layout="centered")

st.markdown("""
<style>
div[data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:12px!important}
div[data-testid="stColumn"],div[data-testid="column"]{
  min-width:0!important;flex:1 1 0!important;width:calc(50% - 6px)!important}
div[data-testid="stImage"] img{border-radius:12px}
</style>
""", unsafe_allow_html=True)

DATA = Path("data")
MEDIA = DATA / "media"
MEDIA.mkdir(parents=True, exist_ok=True)
DB = DATA / "series.json"

CATS = ["រឿងពិត (Real Drama)", "រឿង AI (AI Drama)", "គំនូរជីវចល", "ផ្សេងៗ"]

for k, v in {"admin": False, "view": None, "up": 0}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def load():
    if DB.exists():
        return json.loads(DB.read_text("utf-8"))
    return []


def save(items):
    DB.write_text(json.dumps(items, ensure_ascii=False, indent=1), "utf-8")


def nat(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def parse_links(txt):
    return [l.strip() for l in txt.splitlines()
            if l.strip().lower().startswith("http")]


def save_eps(sid, files, start=1):
    names = []
    for i, f in enumerate(sorted(files, key=lambda x: nat(x.name)), start):
        ext = Path(f.name).suffix.lower() or ".mp4"
        name = f"{sid}_ep{i:03d}{ext}"
        (MEDIA / name).write_bytes(f.getbuffer())
        names.append(name)
    return names


# ---------- Internet Archive (រឿងឥតគិតថ្លៃ) ----------
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


st.title("🎬 រឿងរបស់ខ្ញុំ")
tab_home, tab_free, tab_admin = st.tabs(["🏠 ទំព័រដើម", "🌐 ឥតគិតថ្លៃ", "🔒 ម្ចាស់"])

# ================= ទំព័រដើម =================
with tab_home:
    items = load()
    cur = next((s for s in items if s["id"] == st.session_state.view), None)

    if cur:  # ----- ទំព័រមើលរឿង -----
        if st.button("← ត្រឡប់ក្រោយ"):
            st.session_state.view = None
            st.rerun()
        st.subheader(cur["title"])
        eps = [e for e in cur["episodes"]
               if e.startswith("http") or (MEDIA / e).exists()]
        if not eps:
            st.info("រឿងនេះមិនទាន់មានភាគទេ។")
        else:
            n = st.selectbox("ជ្រើសរើសភាគ", range(len(eps)),
                             format_func=lambda i: f"ភាគទី {i + 1}")
            ep = eps[n]
            if ep.startswith("http"):
                st.video(ep)
                st.link_button("⬇ បើក/ទាញយកភាគនេះ", ep)
            else:
                path = MEDIA / ep
                st.video(str(path))
                with open(path, "rb") as fh:
                    st.download_button("⬇ ទាញយកភាគនេះ", fh,
                                       file_name=path.name,
                                       key=f"dl_{path.name}")
    else:  # ----- បញ្ជីរឿង -----
        q = st.text_input("ស្វែងរកចំណងជើងរឿង", placeholder="🔍 ស្វែងរកចំណងជើងរឿង...",
                          label_visibility="collapsed")
        cat = st.radio("ប្រភេទ", ["ទាំងអស់"] + CATS, horizontal=True,
                       label_visibility="collapsed")
        shown = [s for s in items
                 if q.lower() in s["title"].lower()
                 and (cat == "ទាំងអស់" or s["category"] == cat)]
        if not shown:
            st.info("មិនទាន់មានរឿងទេ។ ចូលផ្ទាំង 🔒 ម្ចាស់ ដើម្បីបន្ថែមរឿង។")
        for i in range(0, len(shown), 2):
            cols = st.columns(2)
            for col, s in zip(cols, shown[i:i + 2]):
                with col:
                    p = MEDIA / s["poster"] if s.get("poster") else None
                    if p and p.exists():
                        st.image(str(p), use_container_width=True)
                    else:
                        st.markdown("🎬")
                    st.markdown(f"**{s['title']}**")
                    st.caption(f"🎞 {len(s['episodes'])} ភាគ")
                    if st.button("▶ មើល", key=f"open_{s['id']}",
                                 use_container_width=True):
                        st.session_state.view = s["id"]
                        st.rerun()

# ================= ឥតគិតថ្លៃ (Internet Archive) =================
with tab_free:
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
            if meta.get("licenseurl"):
                st.caption(f"អាជ្ញាប័ណ្ណ: {meta['licenseurl']}")
            st.link_button("ℹ ពិនិត្យអាជ្ញាប័ណ្ណ",
                           f"https://archive.org/details/{pick}")
        else:
            st.warning("រឿងនេះគ្មានឯកសារ MP4 សូមជ្រើសរឿងផ្សេង។")
    elif kw:
        st.info("រកមិនឃើញ សូមសាកពាក្យផ្សេង។")

# ================= ម្ចាស់ =================
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
        st.write("ដាក់តែរឿងដែលអ្នកធ្វើខ្លួនឯង ឬមានសិទ្ធិប្រើប្រាស់ប៉ុណ្ណោះ។")
        u = st.session_state.up

        st.subheader("➕ បន្ថែមរឿងថ្មី")
        title = st.text_input("ឈ្មោះរឿង", key=f"t_{u}")
        category = st.radio("ប្រភេទ", CATS, key=f"c_{u}")
        poster = st.file_uploader("រូបភាពក្របរឿង (Poster)",
                                  type=["jpg", "jpeg", "png", "webp"],
                                  key=f"p_{u}")
        eps_up = st.file_uploader(
            "វីដេអូតាមលំដាប់ភាគ (ដាក់ឈ្មោះ 1.mp4, 2.mp4, ...)",
            type=["mp4", "mov", "webm", "mkv"],
            accept_multiple_files=True, key=f"e_{u}")
        links_txt = st.text_area(
            "ឬដាក់លីងវីដេអូ (មួយបន្ទាត់ = មួយភាគ)",
            placeholder="https://.../1.mp4\nhttps://youtube.com/watch?v=...",
            key=f"l_{u}")
        if st.button("💾 រក្សាទុករឿង"):
            if not title.strip():
                st.error("សូមដាក់ឈ្មោះរឿង")
            else:
                sid = uuid.uuid4().hex[:8]
                pname = ""
                if poster:
                    pname = f"{sid}_poster{Path(poster.name).suffix.lower()}"
                    (MEDIA / pname).write_bytes(poster.getbuffer())
                names = save_eps(sid, eps_up) if eps_up else []
                names += parse_links(links_txt)
                items = load()
                items.append({"id": sid, "title": title.strip(),
                              "category": category, "poster": pname,
                              "episodes": names})
                save(items)
                st.session_state.up += 1
                st.success("បានរក្សាទុក! ចូលផ្ទាំង 🏠 ទំព័រដើម។")
                st.rerun()

        items = load()
        if items:
            st.divider()
            st.subheader("➕ បន្ថែមភាគទៅរឿងដែលមានស្រាប់")
            ids = [s["id"] for s in items]
            names_map = {s["id"]: s["title"] for s in items}
            sel = st.radio("ជ្រើសរឿង", ids, format_func=lambda i: names_map[i],
                           key=f"sel_{u}")
            more = st.file_uploader("វីដេអូភាគថ្មី",
                                    type=["mp4", "mov", "webm", "mkv"],
                                    accept_multiple_files=True, key=f"m_{u}")
            more_links = st.text_area(
                "ឬដាក់លីងវីដេអូភាគថ្មី (មួយបន្ទាត់ = មួយភាគ)",
                key=f"ml_{u}")
            if st.button("💾 បន្ថែមភាគ") and (more or more_links.strip()):
                s = next(x for x in items if x["id"] == sel)
                start = len(s["episodes"]) + 1
                if more:
                    s["episodes"] += save_eps(sel, more, start)
                s["episodes"] += parse_links(more_links)
                save(items)
                st.session_state.up += 1
                st.rerun()
            if st.button("🗑 លុបរឿងនេះ"):
                s = next(x for x in items if x["id"] == sel)
                for fn in s["episodes"] + [s.get("poster", "")]:
                    if fn and not fn.startswith("http") and (MEDIA / fn).exists():
                        (MEDIA / fn).unlink()
                save([x for x in items if x["id"] != sel])
                st.session_state.view = None
                st.rerun()

        st.divider()
        if st.button("ចាកចេញ"):
            st.session_state.admin = False
            st.rerun()
