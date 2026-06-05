import base64
import io
import json
import re
import html
import hashlib
import zipfile
from datetime import date
from typing import Any, Dict, List, Tuple

import streamlit as st
import streamlit.components.v1 as components

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

APP_VERSION = "V17.7"

LANGS = {
    "ES": {"name": "Español", "market": "Amazon.es", "native": "español"},
    "FR": {"name": "Français", "market": "Amazon.fr", "native": "français"},
    "DE": {"name": "Deutsch", "market": "Amazon.de", "native": "Deutsch"},
    "IT": {"name": "Italiano", "market": "Amazon.it", "native": "italiano"},
    "NL": {"name": "Nederlands", "market": "Amazon.nl", "native": "Nederlands"},
    "PL": {"name": "Polski", "market": "Amazon.pl", "native": "polski"},
    "PT": {"name": "Português", "market": "Amazon.pt", "native": "português"},
    "SE": {"name": "Svenska", "market": "Amazon.se", "native": "svenska"},
    "EN": {"name": "English", "market": "Amazon.co.uk", "native": "English"},
}
TARGET_LANGS = ["FR", "DE", "IT", "NL", "PL", "PT", "SE", "EN"]
ALL_LANGS = ["ES"] + TARGET_LANGS

PRICE = {
    "gpt-5.5": {"input": 5.00, "output": 30.00},
    "gpt-5.4": {"input": 2.50, "output": 15.00},
    "gpt-5.4-mini": {"input": 0.75, "output": 4.50},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
}

TITLE_BAD_PHRASES = [
    "ideal para", "perfecto para", "bombilla no incluida", "sin bombilla", "no incluye bombilla",
    "incluye accesorios", "instalación sencilla", "fácil instalación", "compatible con bombillas led",
]

FACT_KEYS = [
    "product_type", "series_name", "key_structure", "materials", "colors", "dimensions", "socket_or_led",
    "bulb_included", "power", "cct_or_dimming", "adjustability", "installation", "indoor_outdoor",
    "style", "spaces", "core_selling_points", "must_keep_in_titles", "do_not_claim", "notes_for_copy",
]

FACT_LABELS = {
    "product_type": "产品类型",
    "series_name": "系列名",
    "key_structure": "核心结构",
    "materials": "材质",
    "colors": "颜色",
    "dimensions": "尺寸",
    "socket_or_led": "灯头 / 光源",
    "bulb_included": "是否含灯泡",
    "power": "功率",
    "cct_or_dimming": "色温 / 调光",
    "adjustability": "可调节能力",
    "installation": "安装方式",
    "indoor_outdoor": "室内 / 室外",
    "style": "风格",
    "spaces": "适用空间",
    "core_selling_points": "核心卖点",
    "must_keep_in_titles": "标题必须保留",
    "do_not_claim": "禁止宣称 / 不要写",
    "notes_for_copy": "文案注意事项",
}

st.set_page_config(page_title=f"Alpinaluz Listing Generator {APP_VERSION}", layout="wide")

st.markdown(
    """
<style>
:root { --bg:#071014; --panel:#0f172a; --panel2:#111827; --panel3:#1f2937; --text:#f8fafc; --muted:#cbd5e1; --line:#334155; --accent:#60a5fa; --green:#063b22; --red:#451a1a; }
html, body, .stApp, [data-testid="stAppViewContainer"] { background:var(--bg)!important; color:var(--text)!important; }
[data-testid="stHeader"], [data-testid="stToolbar"] { background:rgba(7,16,20,.92)!important; }
[data-testid="stSidebar"] { background:#0b1220!important; }
.block-container { padding-top:2.0rem; max-width:1500px; }
h1,h2,h3,h4,h5,h6,p,span,label,div[data-testid="stMarkdownContainer"] { color:var(--text)!important; }
.stTextInput input,.stTextArea textarea,.stNumberInput input,.stSelectbox div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div { background:#0f172a!important; color:#f8fafc!important; -webkit-text-fill-color:#f8fafc!important; border:1px solid #475569!important; border-radius:8px!important; }
.stTextArea textarea { font-family: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace!important; }
.stTextArea textarea:focus,.stTextInput input:focus { border-color:#60a5fa!important; box-shadow:0 0 0 1px #60a5fa!important; }
.stButton button,.stDownloadButton button { background:#1f2937!important; color:#f8fafc!important; border:1px solid #475569!important; border-radius:8px!important; font-weight:700!important; }
.stButton button:hover,.stDownloadButton button:hover { background:#334155!important; border-color:#93c5fd!important; }
section[data-testid="stExpander"] { background:#0f172a!important; border:1px solid #334155!important; border-radius:10px!important; }
[data-testid="stAlert"] { background:#0f172a!important; border:1px solid #334155!important; color:#f8fafc!important; }
[data-testid="stFileUploader"], [data-testid="stFileUploaderDropzone"] { background:#0f172a!important; color:#f8fafc!important; border:1px dashed #475569!important; border-radius:10px!important; }
[data-baseweb="tag"] { background:#ef4444!important; color:#fff!important; }
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] { background:#111827!important; color:#f8fafc!important; }
[role="option"]:hover { background:#334155!important; }
.card { background:#0f172a; border:1px solid #334155; border-radius:12px; padding:14px 16px; margin:8px 0; }
.info-card { background:#082f49; border:1px solid #0369a1; border-radius:10px; padding:10px 14px; margin:8px 0; }
.ok { background:#052e16; color:#dcfce7; border:1px solid #166534; border-radius:9px; padding:8px 10px; margin:4px 0; }
.warn { background:#3f2f05; color:#fef3c7; border:1px solid #a16207; border-radius:9px; padding:8px 10px; margin:4px 0; }
.bad { background:#3f1212; color:#fee2e2; border:1px solid #991b1b; border-radius:9px; padding:8px 10px; margin:4px 0; }
.small-muted { color:#cbd5e1!important; font-size:13px; }
.titlebox { background:#071827; border:1px solid #2563eb; border-radius:10px; padding:10px 12px; margin:8px 0; }
.candidate-card { background:#0b1b2c; border:1px solid #334155; border-radius:12px; padding:12px 14px; margin:8px 0; line-height:1.45; white-space:normal; word-break:break-word; }
.candidate-title { color:#f8fafc!important; font-size:15px; font-weight:700; }
.candidate-zh { color:#bbf7d0!important; font-size:13px; margin-top:6px; }
.zhbox { background:#102a1d; border:1px solid #166534; border-radius:10px; padding:8px 10px; margin:6px 0; color:#dcfce7!important; }
.status-pill { display:inline-block; padding:3px 8px; border-radius:999px; font-size:12px; font-weight:700; margin-right:6px; }
.s-ok { background:#065f46; color:#d1fae5; } .s-warn { background:#92400e; color:#fef3c7; } .s-bad { background:#991b1b; color:#fee2e2; }
.recommended { border-color:#22c55e!important; box-shadow:0 0 0 1px rgba(34,197,94,.35); }
.status-table { width:100%; border-collapse:collapse; margin:8px 0 12px 0; }
.status-table td,.status-table th { border-bottom:1px solid #334155; padding:7px 8px; color:#f8fafc; vertical-align:top; }
.status-table th { color:#cbd5e1; font-weight:700; }
hr { border-color:#334155!important; }
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------- session helpers -------------------------
def init_state() -> None:
    defaults = {
        "api_usage_log": [],
        "fact_card": {},
        "es_title_candidates": [],
        "selected_es_title": "",
        "selected_es_title_zh": "",
        "confirmed_titles": {},
        "confirmed_title_zh": {},
        "title_candidates": {},
        "title_history": {},
        "listings": {},
        "target_langs": TARGET_LANGS.copy(),
        "listing_mode": "标准包：标题+五点+描述+Search Terms",
        "es_cand_version": 0,
        "lang_cand_version": {},
        "newbie_auto_title": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def product_signature_from_inputs() -> str:
    # Stable identity for the current product. When it changes, generated titles/listings from the previous product must not leak.
    raw = "||".join([
        clean_text(st.session_state.get("sku", "")),
        clean_text(st.session_state.get("manual_title", ""))[:500],
        clean_text(st.session_state.get("old_content", ""))[:800],
        clean_text(st.session_state.get("tech_notes", ""))[:500],
        clean_text(st.session_state.get("brand", "")),
    ])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def reset_generated_state_if_product_changed() -> None:
    sig = product_signature_from_inputs()
    prev = st.session_state.get("product_signature")
    if prev is None:
        st.session_state["product_signature"] = sig
        return
    if sig != prev:
        # Keep user input and API settings, clear generated artifacts that could contain old sockets/concepts.
        for key in [
            "fact_card", "es_title_candidates", "selected_es_title", "selected_es_title_zh",
            "confirmed_titles", "confirmed_title_zh", "title_candidates", "title_history", "listings",
            "selected_es_title_zh_source", "lang_cand_version", "es_cand_version",
        ]:
            if key in st.session_state:
                if key in ["confirmed_titles", "confirmed_title_zh", "title_candidates", "title_history", "listings", "fact_card", "lang_cand_version"]:
                    st.session_state[key] = {}
                elif key == "es_title_candidates":
                    st.session_state[key] = []
                elif key == "es_cand_version":
                    st.session_state[key] = 0
                else:
                    st.session_state[key] = ""
        # Clear language current titles and edit versions.
        for k in list(st.session_state.keys()):
            if k.startswith(("current_title::", "current_title_zh::", "current_title_zh_source::", "title_edit_version::", "selected_candidate_idx::", "title_edit::")):
                del st.session_state[k]
        st.session_state["product_signature"] = sig

# ------------------------- cost and API -------------------------
def estimate_text_tokens(text: str) -> int:
    return max(1, int(len(text or "") / 3.2)) if text else 0


def _usage_tokens(resp: Any) -> Tuple[int, int]:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return 0, 0
    def pick(obj, *names):
        for n in names:
            if hasattr(obj, n):
                return getattr(obj, n) or 0
        return 0
    return int(pick(usage, "input_tokens", "prompt_tokens") or 0), int(pick(usage, "output_tokens", "completion_tokens") or 0)


def record_usage(label: str, model: str, resp: Any = None, input_hint: str = "", output_hint: str = "", image_count: int = 0):
    inp, out = _usage_tokens(resp) if resp is not None else (0, 0)
    estimated = False
    if not inp and not out:
        inp = estimate_text_tokens(input_hint) + image_count * 1200
        out = estimate_text_tokens(output_hint)
        estimated = True
    price = PRICE.get(model, PRICE.get("gpt-5.4"))
    cost = inp / 1_000_000 * price["input"] + out / 1_000_000 * price["output"]
    st.session_state.setdefault("api_usage_log", []).append({
        "label": label, "model": model, "input_tokens": inp, "output_tokens": out,
        "cost": cost, "estimated": estimated, "image_count": image_count,
    })


def usage_totals():
    logs = st.session_state.get("api_usage_log", [])
    return {
        "calls": len(logs),
        "input": sum(x.get("input_tokens", 0) for x in logs),
        "output": sum(x.get("output_tokens", 0) for x in logs),
        "cost": sum(x.get("cost", 0.0) for x in logs),
    }


def get_client():
    key = st.session_state.get("openai_api_key", "").strip()
    if not key:
        return None
    if OpenAI is None:
        raise RuntimeError("缺少 openai 依赖，请先安装 requirements.txt")
    return OpenAI(api_key=key)


def response_text(resp: Any) -> str:
    if hasattr(resp, "output_text") and resp.output_text:
        return str(resp.output_text).strip()
    try:
        chunks = []
        for item in getattr(resp, "output", []) or []:
            for c in getattr(item, "content", []) or []:
                txt = getattr(c, "text", None)
                if txt:
                    chunks.append(txt)
        if chunks:
            return "\n".join(chunks).strip()
    except Exception:
        pass
    return str(resp).strip()


def llm(prompt: str, system: str, model: str = None, effort: str = None, label: str = "文本生成") -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("请先在左侧输入 OpenAI API Key")
    model = model or st.session_state.get("model", "gpt-5.4")
    effort = effort or st.session_state.get("reasoning_effort", "medium")
    if str(model).startswith("gpt-5"):
        kwargs = {
            "model": model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
            ],
        }
        if effort:
            kwargs["reasoning"] = {"effort": effort}
        try:
            resp = client.responses.create(**kwargs)
        except TypeError:
            kwargs.pop("reasoning", None)
            resp = client.responses.create(**kwargs)
        out = response_text(resp)
        record_usage(label, model, resp, system + "\n" + prompt, out)
        return out
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0.25,
    )
    out = resp.choices[0].message.content.strip()
    record_usage(label, model, resp, system + "\n" + prompt, out)
    return out


def llm_multimodal(prompt: str, files: List[Any], system: str, label: str = "图片/事实识别") -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("请先在左侧输入 OpenAI API Key")
    model = st.session_state.get("model", "gpt-5.4")
    files = files[: int(st.session_state.get("image_limit", 3))]
    content = [{"type": "input_text", "text": prompt}]
    for f in files:
        try:
            data = f.getvalue()
            mime = f.type or "image/jpeg"
            content.append({"type": "input_image", "image_url": f"data:{mime};base64,{base64.b64encode(data).decode()}"})
        except Exception:
            pass
    kwargs = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system}]},
            {"role": "user", "content": content},
        ],
        "reasoning": {"effort": st.session_state.get("reasoning_effort", "medium")},
    }
    try:
        resp = client.responses.create(**kwargs)
    except TypeError:
        kwargs.pop("reasoning", None)
        resp = client.responses.create(**kwargs)
    out = response_text(resp)
    record_usage(label, model, resp, system + "\n" + prompt, out, image_count=len(files))
    return out

# ------------------------- parsing and formatting -------------------------
def safe_json(raw: str, fallback: Any):
    text = str(raw or "").strip()
    text = re.sub(r"^```json|^```|```$", "", text, flags=re.M).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            return fallback
    return fallback


def clean_text(s: str) -> str:
    s = str(s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    return s.strip(" \n\t")


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", str(s or "")))


ES_STOPWORDS = {"de", "del", "la", "las", "el", "los", "un", "una", "unos", "unas", "y", "o", "u", "para", "por", "con", "en", "a", "al", "sin", "sobre", "entre", "hasta", "desde"}
PROTECTED_UPPER = {"LED", "USB", "CCT", "RGB", "IP20", "IP44", "IP54", "IP65", "E27", "E14", "G9", "GU10", "G45", "CRI"}


def spanish_amazon_case(title: str) -> str:
    """Amazon.es display style: important words capitalized, short connectors lower-case."""
    def fix_word(w: str, is_first: bool = False) -> str:
        if not w:
            return w
        # Preserve technical tokens and dimensions
        plain = w.strip(" ,;:()[]{}")
        up = plain.upper()
        if up in PROTECTED_UPPER:
            return w.replace(plain, up)
        if re.fullmatch(r"Ø?\d+(?:[.,]\d+)?", plain) or plain.lower() in {"cm", "mm", "w", "x"}:
            return w
        low = plain.lower()
        if (not is_first) and low in ES_STOPWORDS:
            return w.replace(plain, low)
        # Do not destroy words with apostrophes/hyphens too aggressively
        if re.search(r"[A-Z]{2,}|\d", plain):
            return w
        return w.replace(plain, plain[:1].upper() + plain[1:].lower())

    parts = re.split(r"(,|–|-|:)\s*", title)
    out = []
    new_segment = True
    for part in parts:
        if part in {",", "–", "-", ":"}:
            out.append(part + " ")
            new_segment = True
            continue
        words = part.split(" ")
        fixed = []
        for i, w in enumerate(words):
            fixed.append(fix_word(w, is_first=(new_segment and i == 0)))
        out.append(" ".join(fixed))
        new_segment = False
    return clean_text("".join(out)).strip(" ,;-–—")



ROMANCE_STOPWORDS = {
    "FR": {"de", "du", "des", "la", "le", "les", "un", "une", "et", "ou", "pour", "avec", "en", "à", "a", "au", "aux", "sur", "sans"},
    "IT": {"di", "del", "della", "delle", "dei", "da", "con", "e", "o", "per", "a", "al", "alla", "in", "su", "senza"},
    "PT": {"de", "do", "da", "dos", "das", "com", "e", "ou", "para", "em", "no", "na", "ao", "à", "a", "sem"},
}


def light_amazon_case(title: str, lang: str) -> str:
    if lang == "ES":
        return spanish_amazon_case(title)
    stops = ROMANCE_STOPWORDS.get(lang)
    if not stops:
        return title
    def fix_word(w: str, is_first: bool = False) -> str:
        plain = w.strip(" ,;:()[]{}")
        if not plain:
            return w
        up = plain.upper()
        if up in PROTECTED_UPPER:
            return w.replace(plain, up)
        if re.fullmatch(r"Ø?\d+(?:[.,]\d+)?", plain) or plain.lower() in {"cm", "mm", "w", "x"}:
            return w
        low = plain.lower()
        if (not is_first) and low in stops:
            return w.replace(plain, low)
        if re.search(r"[A-Z]{2,}|\d", plain):
            return w
        return w.replace(plain, plain[:1].upper() + plain[1:].lower())
    parts = re.split(r"(,|–|-|:)\s*", title)
    out = []
    new_segment = True
    for part in parts:
        if part in {",", "–", "-", ":"}:
            out.append(part + " ")
            new_segment = True
            continue
        words = part.split(" ")
        out.append(" ".join(fix_word(w, is_first=(new_segment and i == 0)) for i, w in enumerate(words)))
        new_segment = False
    return clean_text("".join(out)).strip(" ,;-–—")

def normalize_title(title: str, lang: str = "") -> str:
    t = clean_text(title)
    t = t.replace("Ø12 Cm", "Ø12 cm").replace("Ø20 Cm", "Ø20 cm")
    t = re.sub(r"(\d+)\s*Cm\b", r"\1 cm", t)
    t = re.sub(r"(\d+)\s*Mm\b", r"\1 mm", t)
    t = re.sub(r"\bLed\b", "LED", t, flags=re.I)
    t = re.sub(r"\bUsb\b", "USB", t, flags=re.I)
    t = re.sub(r"\bG9\b", "G9", t, flags=re.I)
    t = re.sub(r"\bE27\b", "E27", t, flags=re.I)
    t = re.sub(r"\bGu10\b", "GU10", t, flags=re.I)
    t = re.sub(r"\bIp(\d{2})\b", lambda m: "IP" + m.group(1), t, flags=re.I)
    t = t.strip(" ,;-–—")
    if lang in {"ES", "FR", "IT", "PT"}:
        t = light_amazon_case(t, lang)
    return t.strip(" ,;-–—")

def zh_translate_title(title: str, lang: str = "ES") -> str:
    title = normalize_title(title, lang)
    if not title:
        return ""
    prompt = f"""请把下面 {LANGS.get(lang, {}).get('name', lang)} Amazon 标题快速翻译成中文，给不会外语的中国运营同事确认。
要求：
- 只说明标题写了哪些产品事实；
- 不新增内容；
- 一句话，尽量短；
- 如果标题有明显残缺或不自然，请在最后用“风险：...”提醒。

标题：{title}
"""
    return llm(prompt, "你是电商标题内部审核翻译助手，只做准确、简短的中文解释。", model=st.session_state.get("translation_model", "gpt-5.4-mini"), effort="medium", label="标题中文快译")


def translate_listing_title_cheap(title: str, lang: str) -> str:
    return zh_translate_title(title, lang)


def notify_done(msg: str = "生成完成"):
    try:
        st.toast(msg)
    except Exception:
        pass
    if not st.session_state.get("sound_notify", True):
        return
    components.html("""
<script>
try{const A=window.AudioContext||window.webkitAudioContext;const c=new A();const o=c.createOscillator();const g=c.createGain();o.frequency.value=880;o.connect(g);g.connect(c.destination);g.gain.setValueAtTime(0.001,c.currentTime);g.gain.exponentialRampToValueAtTime(0.12,c.currentTime+0.02);g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+0.28);o.start();o.stop(c.currentTime+0.3);}catch(e){}
</script>
""", height=0)


def uploaded_image_key(f: Any, idx: int) -> str:
    return f"exclude_img::{idx}::{getattr(f, 'name', 'img')}::{getattr(f, 'size', 0)}"

# ------------------------- prompt builders -------------------------
def source_brief() -> str:
    return f"""
SKU: {st.session_state.get('sku','')}
EAN: {st.session_state.get('ean','')}
品牌: {st.session_state.get('brand','Alpinaluz')}
系列名: {st.session_state.get('series','')}
原始标题: {st.session_state.get('manual_title','')}
旧Amazon/网站内容: {st.session_state.get('old_content','')}
技术备注: {st.session_state.get('tech_notes','')}
SEO关键词: {st.session_state.get('seo_keywords','')}
手动长描述: {st.session_state.get('manual_description','')}
""".strip()


def fact_card_text() -> str:
    fc = st.session_state.get("fact_card", {}) or {}
    if not fc:
        return ""
    lines = []
    for k in FACT_KEYS:
        v = fc.get(k, "")
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v if str(x).strip())
        if v:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def confirmed_title_block() -> str:
    lines = []
    for lang in ALL_LANGS:
        title = st.session_state.get("confirmed_titles", {}).get(lang, "")
        if title:
            lines.append(f"{lang}: {title}")
    return "\n".join(lines)


def generate_fact_prompt() -> str:
    return f"""你是 Alpinaluz 灯具产品事实识别助手。请只识别事实，不写营销文案。

根据以下资料和图片，生成产品事实卡。资料可能来自旧 Amazon 标题、旧五点、长描述、图片文件名和技术备注。
优先级：技术备注/人工字段 > 原始标题五点描述 > 图片识别。不要发明不存在功能。

输出 JSON，字段必须包含：
{json.dumps(FACT_KEYS, ensure_ascii=False)}

字段说明：
- product_type: 产品类型，西班牙语为主，也可附中文；
- series_name: 系列名/型号名，不一定进标题；
- key_structure: 产品核心结构，比如“三头吊灯/壁灯玻璃球/可调头”等；
- materials/colors/dimensions/socket_or_led: 核心事实；
- bulb_included: 是否含灯泡，写清楚；
- core_selling_points: 5-8个关键卖点；
- must_keep_in_titles: 标题必须尽量保留的信息，不要太多，但要保留SEO和成交关键；
- do_not_claim: 不能声称的功能，比如不是LED集成、不可调光、不是户外等；
- notes_for_copy: 后续写文案要注意什么。

资料：
{source_brief()}
"""


def title_rules(lang: str) -> str:
    common = f"""
标题规则：
- 品牌 Alpinaluz 必须第一位。
- 标题要像 {LANGS[lang]['market']} 上可成交的专业标题，不要碎词拼接。
- 保留高价值事实：产品类型、核心结构、核心材质/颜色、关键尺寸、灯头/LED、风格、核心使用场景。
- 不要把低价值售后/说明塞进标题：bombilla no incluida / bulbs not included / compatible / easy installation / incluye accesorios / cable细节，除非是非常核心卖点。
- 不允许中文，不允许 SKU，不允许无具体数字的裸 cm；但 75 cm、Ø20 cm、43 x 5,1 x 2,7 cm 这类前面有数字的写法是允许的。
- 单灯/单头产品：标题不要突出 1 foco / 1 luz / 1 spot / 1 light / 1-flammig / 1 luce 等数量词，除非用户明确要求；直接写 wall light / aplique / Wandleuchte + 灯头即可。
- 多灯/多头产品：2灯以上必须保留数量，例如 3 luces / 3 lights / 3-flammig / 3x E27。
- 如果 ES 最终标题中已经人工删除某个低价值词，多国语言不要把它重新加回来。
- 宁可略短自然，也不要为了凑字数堆词。
- 标题长度建议 140-200 字符，特殊语言可自然略短，但不能缺失A级核心信息。
- 如果信息太多，按 A/B/C 三级取舍：A级必须进标题；B级保留1-2个最重要；C级放到五点/描述，不要塞标题。
"""
    local = {
        "ES": "西班牙语标题可用 Amazon 西班牙风格：重要名词首字母可大写，介词自然小写。",
        "FR": "法语标题要自然，不要逐词翻译；可用 applique murale / suspension 等本地常用词。",
        "DE": "德语标题要符合德语语法，名词大写，复合词自然；不要出现 für -Leuchtmittel 这种残缺。",
        "IT": "意大利语标题要自然，注意 stile moderno，不要写 stile moderna。",
        "NL": "荷兰语标题要自然，注意 moderne stijl，不要写 modern stijl。",
        "PL": "波兰语标题要自然，不要夹杂英语或西班牙语。",
        "PT": "葡萄牙语标题面向葡萄牙站，使用 candeeiro/aplique/casquilho 等自然表达。",
        "SE": "瑞典语标题要自然，不要夹杂英语；日落要写 solnedgång，不要写 sunset。",
        "EN": "英语标题用 Amazon UK 自然 Title Case，不要机械堆词。",
    }
    return common + "\n" + local.get(lang, "")


def es_title_prompt(instruction: str = "") -> str:
    return f"""请为 Amazon.es 生成 3 个西班牙语标题候选。

{title_rules('ES')}

重点：你要像聊天窗口那样处理，少读无关长描述，标题只围绕高价值 SEO 和成交信息。不要负优化已有好标题。

用户本轮中文修改要求：{instruction or '首次生成，请根据资料给出高质量候选'}

产品事实卡：
{fact_card_text()}

原始资料：
{source_brief()}

输出 JSON 数组，每个元素：
{{"title":"西班牙标题", "zh":"标题中文快译", "why":"简短说明保留了哪些核心信息", "risk":"标题风险/缺点/注意点；若无明显风险写无明显风险"}}
只输出 JSON。
"""


def lang_title_prompt(lang: str, instruction: str = "") -> str:
    es_title = st.session_state.get("confirmed_titles", {}).get("ES", "") or st.session_state.get("selected_es_title", "")
    return f"""请为 {LANGS[lang]['market']} 生成 3 个本地语言标题候选，语言必须是 {LANGS[lang]['native']}。

这是逐国语言标题确认，不是机器翻译，也不是碎词拼接。请参考最终 ES 标题的含义，但要按该国 Amazon 搜索习惯重写。

{title_rules(lang)}

非常重要：必须尊重 ES 标题核心信息，但不能机械照搬导致超长。请按照下面的标题信息预算和 A/B/C 取舍生成：
{title_budget_text()}
{must_inherit_text_for_prompt()}

用户本轮中文修改要求：{instruction or '首次生成，请给出3个高质量本地标题'}

最终 ES 标题：
{es_title}

产品事实卡：
{fact_card_text()}

原始资料补充：
{source_brief()}

输出 JSON 数组，每个元素：
{{"title":"{LANGS[lang]['native']}标题", "zh":"标题中文快译", "kept":"简短说明保留了哪些ES核心信息", "risk":"标题风险/缺点/注意点；若无明显风险写无明显风险"}}
只输出 JSON。
"""



def batch_lang_title_prompt(langs: List[str]) -> str:
    es_title = st.session_state.get("confirmed_titles", {}).get("ES", "") or st.session_state.get("selected_es_title", "")
    lang_rules = "\n".join([f"{l}: {LANGS[l]['market']}，必须使用 {LANGS[l]['native']}。{title_rules(l)}" for l in langs])
    schema = {l: [{"title": f"{LANGS[l]['native']}标题1", "zh": "中文快译", "kept": "保留的核心信息", "risk": "风险或无"}] for l in langs}
    return f"""请为多个 Amazon 国家站一次性生成首轮标题候选。每个国家生成 3 个标题候选。

这是给新手节省等待时间的“首轮批量候选”，不是最终正文。请保证每个国家标题独立本地化，不能碎词拼接，不能简单机器翻译。

通用要求：
- Alpinaluz 必须第一位。
- 每个国家必须使用对应本地语言。
- 标题必须尽量保留 ES 标题的核心成交信息，但不能机械照搬导致超长。
- 标题信息预算：{title_budget_text()}
- A/B/C取舍：{must_inherit_text_for_prompt()}
- 不要写中文，不要写 SKU，不要无具体数字的裸 cm；但 75 cm、Ø20 cm、43 x 5,1 x 2,7 cm 这类前面有数字的写法是允许的。
- 不要把“灯泡不含/安装简单/配件包含”等低价值说明塞进标题。
- 每个标题都给一个短中文快译，方便不会外语的同事判断。

各国规则：
{lang_rules}

最终 ES 标题：
{es_title}

产品事实卡：
{fact_card_text()}

原始资料补充：
{source_brief()}

输出严格 JSON 对象，key 必须是语言代码。示例结构：
{json.dumps(schema, ensure_ascii=False)}

只输出 JSON。"""

def listing_prompt(lang: str, include_aplus: bool) -> str:
    title = st.session_state.get("confirmed_titles", {}).get(lang, "")
    es_listing = st.session_state.get("listings", {}).get("ES", {})
    es_bullets = es_listing.get("bullets", []) if isinstance(es_listing, dict) else []
    es_description = es_listing.get("description", "") if isinstance(es_listing, dict) else ""
    es_search = es_listing.get("search_terms", "") if isinstance(es_listing, dict) else ""
    return f"""请生成 {LANGS[lang]['market']} Listing 正文，语言必须是 {LANGS[lang]['native']}。

关键规则：
- Title 必须完全使用我提供的“已确认标题”，不得修改、不得缩短、不得重写。
- 只生成五点、长描述、Search Terms 和中文解释；A+ 按开关生成。
- 如果已有 ES 五点/描述，请逐条保留同样卖点方向，避免负优化。
- 不要新增不存在功能。灯头/是否含灯泡/尺寸/功率必须准确。
- 五点格式要像 Amazon 最常见的自然格式："自然卖点短标题: 具体说明"，短标题可 3-8 个词，不要硬凑两个词。
- 标题短语不能碎裂，语法要像本地人写的电商文案。

已确认标题（必须原样输出）：
{title}

产品事实卡：
{fact_card_text()}

ES 参考五点：
{json.dumps(es_bullets, ensure_ascii=False)}

ES 参考长描述：
{es_description}

ES Search Terms：
{es_search}

原始资料：
{source_brief()}

输出 JSON：
{{
  "title": "必须原样等于已确认标题",
  "title_zh": "中文快译",
  "bullets": ["5条"],
  "bullets_zh": ["5条中文解释"],
  "description": "长描述",
  "description_zh": "中文解释",
  "search_terms": "250字符以内，不重复品牌，不加标点堆砌",
  "search_terms_zh": "中文解释",
  "aplus": [{{"module":1,"title":"","body":"","image_prompt_zh":""}}]
}}
A+开关：{'生成5个模块' if include_aplus else '不生成，aplus输出空数组'}。
只输出 JSON。
"""

# ------------------------- candidates and listings -------------------------
def parse_candidate_payload(data: Any, lang: str = "") -> List[Dict[str, str]]:
    if isinstance(data, dict):
        data = data.get("candidates") or data.get("titles") or data.get("items") or []
    out = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, str):
            out.append({"title": normalize_title(item, lang), "zh": "", "why": "", "risk": ""})
        elif isinstance(item, dict):
            title = normalize_title(item.get("title", ""), lang)
            if title:
                out.append({
                    "title": title,
                    "zh": clean_text(item.get("zh", "") or item.get("title_zh", "")),
                    "why": clean_text(item.get("why", "") or item.get("kept", "")),
                    "risk": clean_text(item.get("risk", "")),
                })
    return out[:3]


def parse_candidates(raw: Any, lang: str = "") -> List[Dict[str, str]]:
    data = safe_json(raw, []) if isinstance(raw, str) else raw
    return parse_candidate_payload(data, lang)


def parse_batch_candidates(raw: str, langs: List[str]) -> Dict[str, List[Dict[str, str]]]:
    data = safe_json(raw, {})
    result: Dict[str, List[Dict[str, str]]] = {}
    if not isinstance(data, dict):
        return result
    for lang in langs:
        block = data.get(lang) or data.get(lang.lower()) or data.get(LANGS[lang]["name"]) or []
        cands = parse_candidate_payload(block, lang)
        if cands:
            result[lang] = cands
    return result


def bump_lang_version(lang: str) -> None:
    d = st.session_state.setdefault("lang_cand_version", {})
    d[lang] = int(d.get(lang, 0)) + 1

def candidates_need_compression(cands: List[Dict[str, str]], lang: str) -> bool:
    if not cands:
        return False
    # Compress only when all candidates are unusable or outside the safe budget.
    if all(len(clean_text(c.get("title", ""))) > 200 for c in cands):
        return True
    if all((title_blocking_issues(c.get("title", ""), lang) or len(clean_text(c.get("title", ""))) > target_title_max()) for c in cands):
        return True
    return False


def compress_candidates_prompt(lang: str, cands: List[Dict[str, str]]) -> str:
    es_title = current_es_title()
    current_titles = "\n".join([f"{i+1}. {c.get('title','')}" for i, c in enumerate(cands)])
    return f"""下面是 {LANGS[lang]['market']} 的标题候选，但它们过长或风险偏高。请重新生成 3 个更短、更自然的标题候选。语言必须是 {LANGS[lang]['native']}。

{title_rules(lang)}

标题预算：{title_budget_text()}
A/B/C取舍：{must_inherit_text_for_prompt()}

压缩规则：
- 必须保留A级信息。
- B级只保留最重要的 1-2 个，不要堆满所有场景。
- C级全部移到五点/描述，不要放标题。
- 目标长度：140-{target_title_max()} 字符；绝对不能超过200。
- 如果 ES 标题已经很长，不要逐字翻译；要本地化压缩。

最终 ES 标题：
{es_title}

当前过长/风险候选：
{current_titles}

产品事实卡：
{fact_card_text()}

输出 JSON 数组，每个元素：
{{"title":"{LANGS[lang]['native']}标题", "zh":"标题中文快译", "kept":"保留的核心信息", "risk":"风险或无明显风险"}}
只输出 JSON。"""


def maybe_auto_compress_candidates(lang: str, cands: List[Dict[str, str]], label_prefix: str) -> List[Dict[str, str]]:
    """If all candidates are over budget, ask the model once for compressed versions.
    This costs a little extra only for problematic languages, but saves manual repair time.
    """
    if not candidates_need_compression(cands, lang):
        return cands
    try:
        raw = llm(compress_candidates_prompt(lang, cands), f"你是 {LANGS[lang]['market']} Amazon 标题压缩专家。输出严格 JSON。", label=f"{label_prefix}-{lang}标题自动压缩")
        fixed = parse_candidates(raw, lang)
        return fixed or cands
    except Exception:
        return cands


def sync_zh_for_title(lang: str, title: str, zh: str) -> None:
    if lang == "ES":
        st.session_state["selected_es_title_zh"] = zh
        st.session_state["selected_es_title_zh_source"] = title
    else:
        st.session_state[f"current_title_zh::{lang}"] = zh
        st.session_state[f"current_title_zh_source::{lang}"] = title


def bump_title_edit_version(lang: str) -> None:
    key = f"title_edit_version::{lang}"
    st.session_state[key] = int(st.session_state.get(key, 0)) + 1


def current_title_state_key(lang: str) -> str:
    return "selected_es_title" if lang == "ES" else f"current_title::{lang}"


def current_title_widget_key(lang: str) -> str:
    version = int(st.session_state.get(f"title_edit_version::{lang}", 0))
    return f"title_edit::{lang}::{version}"


def get_effective_current_title(lang: str) -> str:
    # Prefer what the user has typed in the current visible title box, then the stored title.
    wkey = current_title_widget_key(lang)
    return st.session_state.get(wkey) or st.session_state.get(current_title_state_key(lang), "")


def set_current_title(lang: str, title: str, zh: str = "") -> None:
    title = normalize_title(title, lang)
    if lang == "ES":
        st.session_state["selected_es_title"] = title
        st.session_state["selected_es_title_zh"] = zh or ""
        st.session_state["selected_es_title_zh_source"] = title if zh else ""
    else:
        current_key = f"current_title::{lang}"
        zh_key = f"current_title_zh::{lang}"
        st.session_state[current_key] = title
        st.session_state[zh_key] = zh or ""
        st.session_state[f"current_title_zh_source::{lang}"] = title if zh else ""
    # Force the editable title widget to remount with the new generated/selected title.
    bump_title_edit_version(lang)


def has_naked_cm(title: str) -> bool:
    """Return True only when cm appears without a nearby numeric value.
    Allowed examples: 75 cm, 75cm, Ø20 cm, 43 x 5,1 x 2,7 cm.
    """
    t = clean_text(title)
    for m in re.finditer(r"\bcm\b", t, flags=re.I):
        prefix = t[:m.start()].rstrip()
        # Accept number immediately before cm, allowing space, decimal comma/dot and Ø.
        if re.search(r"(?:Ø\s*)?\d+(?:[.,]\d+)?\s*$", prefix):
            continue
        # Accept dimension chains like 43 x 5,1 x 2,7 cm.
        if re.search(r"\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?\s*(?:[x×]\s*\d+(?:[.,]\d+)?\s*)?$", prefix):
            continue
        return True
    return False



def _facts_blob() -> str:
    fc = st.session_state.get("fact_card", {}) or {}
    parts = [st.session_state.get("selected_es_title", ""), st.session_state.get("manual_title", ""), st.session_state.get("tech_notes", ""), st.session_state.get("old_content", "")]
    for v in fc.values():
        parts.append(" ".join(map(str, v)) if isinstance(v, list) else str(v or ""))
    return " ".join(parts)


def is_multi_light_product() -> bool:
    blob = _facts_blob().lower()
    patterns = [
        r"\b(?:2|3|4|5|6|8|10)\s*[x×]\s*(?:e27|e14|g9|gu10)",
        r"\b(?:2|3|4|5|6|8|10)\s*(?:luces|lights|luci|luzes|flammig|flammes|lichtpunten|ljuspunkter|punktowa|puntos)",
        r"\b(?:doble|triple|cuádruple|3h|2h|4h)\b",
        r"\b(?:dos|tres|quattro|three|zwei|drei|trois)\b.*\b(?:luces|lights|luci|luzes|spots|pantallas|shades|schirm|abat-jour)",
        r"三头|三灯|双头|双灯|多头|3灯|2灯|4灯",
    ]
    return any(re.search(p, blob, re.I) for p in patterns)


def is_single_light_product() -> bool:
    if is_multi_light_product():
        return False
    blob = _facts_blob().lower()
    patterns = [
        r"\b1\s*[x×]\s*(?:e27|e14|g9|gu10)",
        r"\b1\s*(?:luz|luce|light|lumi[eè]re|spot|foco|flammig|lichtpunkt|ljuspunkt)",
        r"\bsingle[-\s]?light\b", r"\b1[-\s]?lichts\b", r"\bjednopunkt", r"单头|单灯|1灯|一个灯头|1个灯头",
    ]
    return any(re.search(p, blob, re.I) for p in patterns)


SINGLE_LIGHT_LOW_VALUE_PATTERNS = [
    r"\b1\s*(?:foco|luz|spot|light|luce|lume|lumi[eè]re|lichtpunkt|ljuspunkt|punkt|punto)\b",
    r"\b1[-\s]?(?:light|lichts|flammig|flammige|luce|luz)\b",
    r"\bsingle[-\s]?light\b",
    r"\bjednopunkt\w*\b",
    r"\bà\s*1\s*lumi[eè]re\b",
    r"\bde\s*1\s*luz\b",
    r"\ba\s*1\s*luce\b",
    r"\bmed\s*1\s*ljuspunkt\b",
]


def has_low_value_single_count(title: str) -> bool:
    if not is_single_light_product():
        return False
    t = clean_text(title).lower()
    return any(re.search(p, t, re.I) for p in SINGLE_LIGHT_LOW_VALUE_PATTERNS)



# ------------------------- ES inheritance, title budget and risks -------------------------
def current_es_title() -> str:
    return clean_text(st.session_state.get("confirmed_titles", {}).get("ES", "") or st.session_state.get("selected_es_title", ""))


def title_budget_text() -> str:
    es = current_es_title()
    n = len(es)
    if n >= 190:
        return (
            f"当前 ES 标题很长（{n}/200）。多国语言标题目标控制在 160-185 字符；"
            "只保留A级核心信息，B级只保留1-2个最重要场景/风格，C级全部放入五点或描述。"
        )
    if n >= 170:
        return (
            f"当前 ES 标题较长（{n}/200）。多国语言标题目标控制在 160-190 字符；"
            "避免逐字照搬西语，优先压缩长场景词。"
        )
    return (
        f"当前 ES 标题长度适中（{n}/200）。多国语言标题目标 140-190 字符；"
        "在自然本地化前提下保留核心信息。"
    )


def target_title_max() -> int:
    # For auto recommendation and compression prompt, keep a safety margin when ES is long.
    n = len(current_es_title())
    if n >= 190:
        return 185
    if n >= 170:
        return 190
    return 195


def extract_sockets_from_text(text: str) -> List[str]:
    found = []
    for x in re.findall(r"\b(?:E27|E14|G9|GU10|GU5\.3|G4)\b", text or "", flags=re.I):
        t = x.upper()
        if t not in found:
            found.append(t)
    return found


def current_socket_tokens() -> List[str]:
    """Current product socket/light tokens. ES title wins, then current fact card.
    This prevents old-product G9/GU10 risks from leaking into a new E27 product.
    """
    es = current_es_title()
    fact_socket = str((st.session_state.get("fact_card", {}) or {}).get("socket_or_led", ""))
    fact_notes = " ".join(str((st.session_state.get("fact_card", {}) or {}).get(k, "")) for k in ["must_keep_in_titles", "notes_for_copy"])
    es_sockets = extract_sockets_from_text(es)
    if es_sockets:
        return es_sockets[:2]
    return extract_sockets_from_text(fact_socket + " " + fact_notes)[:2]


def socket_conflict_warning() -> str:
    es_sockets = set(extract_sockets_from_text(current_es_title()))
    fact_sockets = set(extract_sockets_from_text(str((st.session_state.get("fact_card", {}) or {}).get("socket_or_led", ""))))
    if es_sockets and fact_sockets and es_sockets.isdisjoint(fact_sockets):
        return f"事实卡灯头 {', '.join(sorted(fact_sockets))} 与 ES 标题灯头 {', '.join(sorted(es_sockets))} 不一致，请人工检查。"
    return ""


def concept_match_any(text: str, kws: List[str]) -> bool:
    """Semantic keyword matcher with fewer false positives.
    - Long phrases may match by substring.
    - Very short Latin terms (e.g. old bad keyword "or") require word boundaries,
      so they do not match inside dormitorio/comedor/etc.
    - Accented/non-Latin fragments still use substring matching.
    """
    t = clean_text(text).lower()
    for k in kws:
        kk = clean_text(k).lower()
        if not kk:
            continue
        # Avoid matching tiny words inside unrelated words.
        if re.fullmatch(r"[a-z0-9]{1,3}", kk):
            if re.search(rf"(?<![a-z0-9]){re.escape(kk)}(?![a-z0-9])", t):
                return True
            continue
        if re.search(r"^[a-z0-9°øØ .,+-]+$", kk):
            if kk in t:
                return True
        elif kk in t:
            return True
    return False


def dim_variants(dim: str) -> List[str]:
    d = clean_text(dim)
    compact = re.sub(r"\s+", "", d)
    no_dia = d.replace("Ø", "").replace("ø", "")
    return list(dict.fromkeys([d, compact, no_dia, re.sub(r"\s+", "", no_dia)]))


def extract_key_dimensions(text: str) -> List[str]:
    t = clean_text(text)
    dims = []
    # Ø10 cm / 10 cm / 100 cm / 43 x 5,1 x 2,7 cm
    patterns = [
        r"(?:Ø\s*)?\d+(?:[.,]\d+)?\s*(?:cm|mm)",
        r"\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?(?:\s*[x×]\s*\d+(?:[.,]\d+)?)?\s*(?:cm|mm)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, t, flags=re.I):
            d = clean_text(m.group(0))
            if d.lower() not in [x.lower() for x in dims]:
                dims.append(d)
    # Keep at most 3 dimensions in title checks to avoid over-constraining.
    return dims[:3]


def product_type_concept() -> Tuple[str, str, List[str]] | None:
    """Detect product type and provide multilingual equivalent terms.
    This must be semantic, not literal ES-only matching; otherwise DE Stehlampe,
    NL Vloerlamp, PL Lampa podłogowa, etc. are falsely flagged as missing.
    """
    ref = " ".join([
        current_es_title(),
        str((st.session_state.get("fact_card", {}) or {}).get("product_type", "")),
        str((st.session_state.get("fact_card", {}) or {}).get("key_structure", "")),
        str((st.session_state.get("manual_title", ""))),
    ]).lower()

    product_types = [
        ("product_floor", "落地灯类型", [
            "lámpara de pie", "lampara de pie", "floor lamp", "standing lamp", "stehlampe", "stehleuchte",
            "lampadaire", "lampada da terra", "piantana", "candeeiro de pé", "candeeiro de pe", "candeeiro de chão", "candeeiro de chao",
            "vloerlamp", "staande lamp", "lampa podłogowa", "lampa podlogowa", "lampa stojąca", "lampa stojaca",
            "golvlampa", "落地灯"
        ]),
        ("product_pendant", "吊灯类型", [
            "lámpara colgante", "lampara colgante", "colgante", "suspension", "suspensión", "pendant light", "pendant lamp",
            "hanglamp", "hängelampe", "haengelampe", "pendelleuchte", "lampada a sospensione", "sospensione",
            "candeeiro suspenso", "candeeiro de teto", "lampa wisząca", "lampa wiszaca", "pendellampa", "taklampa", "吊灯"
        ]),
        ("product_wall", "壁灯类型", [
            "aplique de pared", "aplique", "wall light", "wall lamp", "wandleuchte", "applique murale", "applique da parete",
            "candeeiro de parede", "wandlamp", "kinkiet", "vägglampa", "vagglampa", "壁灯"
        ]),
        ("product_table", "台灯类型", [
            "lámpara de mesa", "lampara de mesa", "table lamp", "desk lamp", "tischleuchte", "tischlampe", "lampe de table",
            "lampada da tavolo", "candeeiro de mesa", "tafellamp", "lampa stołowa", "lampa stolowa", "bordslampa", "台灯"
        ]),
        ("product_ceiling", "吸顶灯/顶灯类型", [
            "plafón", "plafon", "ceiling light", "ceiling lamp", "deckenleuchte", "plafonnier", "plafoniera", "plafondlamp",
            "lampa sufitowa", "taklampa", "吸顶灯", "顶灯"
        ]),
    ]
    for key, zh, kws in product_types:
        if concept_match_any(ref, kws):
            return (key, zh, kws)
    return None


def current_core_concepts() -> Dict[str, List[Tuple[str, str, List[str]]]]:
    """Return A/B/C title concepts for the CURRENT product only.
    A = must keep in title; B = prefer, but can compress; C = move to bullets/description.
    """
    es = current_es_title()
    fc = st.session_state.get("fact_card", {}) or {}
    ref = " ".join([es, str(fc.get("must_keep_in_titles", "")), str(fc.get("core_selling_points", "")), str(fc.get("key_structure", ""))]).lower()
    a: List[Tuple[str, str, List[str]]] = []
    b: List[Tuple[str, str, List[str]]] = []
    c: List[Tuple[str, str, List[str]]] = []

    pt = product_type_concept()
    if pt:
        a.append(pt)

    for sock in current_socket_tokens():
        a.append((f"socket_{sock}", f"{sock}灯头/光源", [sock.lower()]))

    for d in extract_key_dimensions(es):
        # Dimensions in the final ES title are usually intentional, keep as A.
        a.append((f"dim_{d}", f"关键尺寸 {d}", dim_variants(d)))

    # Main color/material combinations.
    concepts = [
        ("white", "白色/白色哑光", ["blanco", "white", "bianco", "branco", "weiß", "weiss", "wit", "biały", "bialy", "vit", "白"]),
        ("black", "黑色", ["negro", "black", "nero", "preto", "schwarz", "zwart", "czarn", "svart", "黑"]),
        ("gold", "金色/黄铜色", ["dorado", "gold", "oro", "ottone", "messing", "złot", "zlot", "guld", "金色", "黄铜", "latón", "laton", "brass"]),
        ("natural_wood", "天然木/原木", ["madera", "wood", "bois", "legno", "madeira", "holz", "hout", "drewno", "trä", "tra", "木"]),
        ("metal", "金属材质", ["metal", "metálic", "metalic", "metallo", "métal", "metall", "staal", "stål", "stal", "金属", "钢", "acero"]),
        ("glass", "玻璃材质", ["cristal", "vidrio", "glass", "verre", "vetro", "glas", "szkło", "szklo", "玻璃"]),
    ]
    for key, zh, kws in concepts:
        # Only high-confidence title/fact words should become title requirements.
        # Colors such as gold/brass must not be inferred from tiny substrings or old notes.
        in_es = concept_match_any(es, kws)
        in_fact = concept_match_any(" ".join([str(fc.get("materials", "")), str(fc.get("colors", "")), str(fc.get("key_structure", ""))]), kws)
        if in_es:
            a.append((key, zh, kws))
        elif in_fact and key in {"natural_wood", "metal", "glass", "white", "black"}:
            # Material/major visual identity from current fact card is useful, but not a hard error if compressed.
            b.append((key, zh, kws))
        elif in_fact and key == "gold":
            # Gold/brass from fact card is only B-level unless confirmed in final ES title.
            b.append((key, zh, kws))

    # Key functions/features.
    feature_concepts = [
        ("adjustable_cable", "可调线/高度可调", ["cable regulable", "altura ajustable", "adjustable cable", "height adjustable", "câble réglable", "cable regolabile", "cabo regulável", "verstellbar", "höhenverstell", "verstelbare kabel", "przewód regulowany", "justerbar kabel", "可调线", "高度可调"]),
        ("orientable_350", "350°可调", ["350", "350°"]),
        ("integrated_switch", "集成开关", ["interruptor", "switch", "schalter", "interruttore", "interrupteur", "włącznik", "wlacznik", "schakelaar", "strömbrytare", "strombrytare", "开关"]),
        ("cct", "CCT/可调色温", ["cct", "3000", "4000", "6000", "色温", "temperatura de color"]),
        ("usb", "USB接口", ["usb", "usb-c", "type-c"]),
    ]
    for key, zh, kws in feature_concepts:
        if concept_match_any(es, kws):
            a.append((key, zh, kws))
        elif any(x in ref for x in [k.lower() for k in kws]):
            b.append((key, zh, kws))

    # Style and main spaces are B-level: important for SEO but can be compressed when ES is long.
    style_concepts = [
        ("nordic", "北欧风", ["nórdico", "nordico", "nordic", "scandinav", "skandinav", "nordique", "北欧"]),
        ("minimalist", "极简风", ["minimalista", "minimalist", "minimalistisch", "minimalistycz", "极简"]),
        ("vintage", "复古风", ["vintage", "retro", "复古"]),
        ("industrial", "工业风", ["industrial", "industriell", "工业"]),
    ]
    for item in style_concepts:
        if concept_match_any(es, item[2]):
            b.append(item)

    space_concepts = [
        ("kitchen", "厨房/岛台", ["cocina", "kitchen", "cuisine", "cucina", "cozinha", "küche", "kuche", "keuken", "kuchnia", "kök", "kok", "isla", "island", "îlot", "ilha", "岛台", "厨房"]),
        ("dining", "餐厅/餐桌", ["comedor", "dining", "salle à manger", "salle a manger", "sala da pranzo", "sala de jantar", "esszimmer", "eetkamer", "jadalnia", "matplats", "餐厅", "餐桌"]),
        ("bedroom", "卧室/床头", ["dormitorio", "bedroom", "chambre", "camera", "quarto", "schlafzimmer", "slaapkamer", "sypial", "sovrum", "cabecero", "testiera", "cabeceira", "hoofdbord", "bettkopf", "zagłów", "床头", "卧室"]),
        ("reading", "阅读场景", ["lectura", "reading", "lecture", "lettura", "leitura", "lesen", "lees", "läs", "las", "czyt", "阅读"]),
        ("living", "客厅", ["salón", "salon", "living", "soggiorno", "sala", "woonkamer", "wohnzimmer", "vardagsrum", "客厅"]),
    ]
    for item in space_concepts:
        if concept_match_any(es, item[2]):
            b.append(item)

    # C-level info: don't force in titles.
    c.extend([
        ("bulb_not_included", "灯泡不包含", ["bombilla no incluida", "bulb not included", "ampoule non incluse", "灯泡不含"]),
        ("power", "功率/最大瓦数", ["40w", "15w", "60w", "watt", "瓦"]),
        ("g95", "G95兼容", ["g95"]),
        ("installation", "安装细节", ["instalación", "installation", "montage", "安装"]),
    ])

    # De-duplicate by key.
    def dedupe(items):
        seen = set(); out = []
        for item in items:
            if item[0] not in seen:
                seen.add(item[0]); out.append(item)
        return out
    return {"A": dedupe(a), "B": dedupe(b), "C": dedupe(c)}


def concepts_for_prompt() -> str:
    cc = current_core_concepts()
    def line(tier):
        return "、".join(x[1] for x in cc.get(tier, [])) or "无"
    return (
        f"A级必须保留：{line('A')}\n"
        f"B级尽量保留，标题太长时可只保留1-2个：{line('B')}\n"
        f"C级不要强行放标题，放入五点/描述：{line('C')}"
    )


def must_inherit_text_for_prompt() -> str:
    return concepts_for_prompt()


def missing_concepts_by_tier(title: str) -> Dict[str, List[str]]:
    t = clean_text(title)
    cc = current_core_concepts()
    result = {"A": [], "B": []}
    for tier in ["A", "B"]:
        for key, zh, kws in cc.get(tier, []):
            if not concept_match_any(t, kws):
                result[tier].append(zh)
    return result


def missing_es_core_concepts(title: str, lang: str = "") -> List[str]:
    # Backward-compatible helper: A-level missing only.
    return missing_concepts_by_tier(title).get("A", [])


def title_soft_issues(title: str, lang: str = "") -> List[str]:
    issues: List[str] = []
    t = clean_text(title)
    if not t:
        return issues
    if has_low_value_single_count(t):
        issues.append("单灯产品标题突出 1 foco / 1 luz / 1 spot 等低价值数量词，建议删除")
    missing = missing_concepts_by_tier(t)
    if missing.get("A"):
        issues.append("缺失A级核心信息：" + "、".join(missing["A"][:3]))
    # B-level missing is an optimization hint, not a blocking risk. Keep it light to reduce false alarms.
    if missing.get("B") and len(clean_text(title)) < 150 and len(current_es_title()) < 185:
        issues.append("B级信息可优化：" + "、".join(missing["B"][:2]))
    low_value = ["bombilla no incluida", "bulbs not included", "ampoule non incluse", "lampadine non incluse", "lâmpada não incluída", "leuchtmittel nicht enthalten", "żarówka nie", "ljuskälla ingår inte"]
    if any(x in t.lower() for x in low_value):
        issues.append("标题写了灯泡不含，建议放五点而不是标题")
    conflict = socket_conflict_warning()
    if conflict:
        issues.append(conflict)
    return issues


def sanitize_model_risk(risk: str) -> str:
    """Remove model-hallucinated or low-confidence risk notes.

    The model often invents missing sockets/colors from a previous product or from
    loose wording. The rule-based risk engine is the source of truth for hard risks.
    """
    r = clean_text(risk)
    if not r:
        return ""
    sockets = set(current_socket_tokens())
    all_sockets = {"E27", "E14", "G9", "GU10", "GU5.3", "G4"}
    wrong = [x for x in all_sockets if x not in sockets]
    missing_words = ["缺失", "未写", "missing", "manque", "manca", "fehlt", "brak", "saknar"]
    parts = re.split(r"[;；。]\s*", r)
    kept = []
    current_keys = {x[0] for tier in current_core_concepts().values() for x in tier}
    for part in parts:
        pl = part.lower()
        # Drop clauses mentioning a wrong socket as missing.
        if any(ws.lower() in pl for ws in wrong) and any(k in pl for k in missing_words):
            continue
        # Drop generic LLM-generated missing-core clauses; code-generated checks are shown separately.
        if ("缺失a级" in pl or "缺失核心" in pl or "missing core" in pl) and any(k in pl for k in missing_words + ["缺失"]):
            continue
        # Do not let hallucinated gold/brass notes disturb wood products unless gold is current.
        if any(x in pl for x in ["金色", "黄铜", "gold", "brass", "dorado", "latón", "laton", "messing", "ottone"]) and "gold" not in current_keys:
            continue
        kept.append(part)
    return "；".join(x for x in kept if x).strip("； ")

def title_blocking_issues(title: str, lang: str = "") -> List[str]:
    issues = title_quality_issues(title, lang)
    hard_words = ["标题为空", "标题超长", "品牌 Alpinaluz 没有放第一位", "标题含中文", "标题含 SKU", "出现裸 cm"]
    return [x for x in issues if any(w in x for w in hard_words)]


def candidate_score(c: Dict[str, str], lang: str) -> int:
    title = normalize_title(c.get("title", ""), lang)
    n = len(title)
    score = 100
    issues = title_quality_issues(title, lang)
    soft = title_soft_issues(title, lang)
    for issue in issues:
        if "超长" in issue or "含中文" in issue or "品牌" in issue or "SKU" in issue or "裸 cm" in issue:
            score -= 45
        elif "偏短" in issue:
            score -= 14
        elif "接近上限" in issue:
            score -= 6
        else:
            score -= 5
    for issue in soft:
        if "单灯产品" in issue:
            score -= 30
        elif "缺失A级核心信息" in issue:
            score -= 24
        elif "B级信息" in issue:
            score -= 5
        elif "灯泡不含" in issue:
            score -= 14
        elif "不一致" in issue:
            score -= 30
        else:
            score -= 8
    # Prefer safe titles within budget. Do not simply choose the fullest/longest one.
    tmax = target_title_max()
    if 145 <= n <= min(185, tmax):
        score += 16
    elif 120 <= n < 145:
        score += 3
    elif min(185, tmax) < n <= 200:
        score -= 10
    title_l = title.lower()
    good_markers = ["e27", "g9", "gu10", "led", "cm", "350", "interrupt", "switch", "schalter", "interruttore", "interrupteur", "madera", "wood", "bois", "legno", "holz", "madeira", "drewno", "trä"]
    score += min(14, sum(2 for x in good_markers if x in title_l))
    return score

def best_candidate_index(cands: List[Dict[str, str]], lang: str) -> int:
    if not cands:
        return 0
    return max(range(len(cands)), key=lambda i: candidate_score(cands[i], lang))


def auto_select_best_candidate(lang: str, cands: List[Dict[str, str]]) -> None:
    if not cands:
        return
    idx = best_candidate_index(cands, lang)
    st.session_state[f"selected_candidate_idx::{lang}"] = idx
    chosen = cands[idx]
    set_current_title(lang, chosen.get("title", ""), chosen.get("zh", ""))


def auto_confirmable_title(title: str, lang: str) -> bool:
    # One-click auto confirmation is intentionally strict. Yellow titles require human review.
    if title_blocking_issues(title, lang):
        return False
    soft = title_soft_issues(title, lang)
    # A-level missing, single-light count, socket conflict or low-value title text cannot be auto-confirmed.
    risky = [x for x in soft if ("缺失A级" in x or "单灯产品" in x or "不一致" in x or "灯泡不含" in x)]
    if risky:
        return False
    n = len(clean_text(title))
    # Green auto-confirm should leave room; 191-200 is yellow/manual review.
    return 120 <= n <= min(190, target_title_max())

def title_status_for_lang(lang: str) -> Tuple[str, str, str]:
    confirmed = st.session_state.get("confirmed_titles", {}).get(lang, "")
    current = confirmed or st.session_state.get(f"current_title::{lang}", "") or (st.session_state.get("selected_es_title", "") if lang == "ES" else "")
    if confirmed:
        return "s-ok", "已确认", current
    if not current:
        return "s-warn", "未生成", current
    hard = title_blocking_issues(current, lang)
    if hard:
        return "s-bad", "需修改", current
    return "s-warn", "AI推荐待确认", current


def title_quality_issues(title: str, lang: str = "") -> List[str]:
    """Hard/format issues. Soft operating risks are handled by title_soft_issues()."""
    issues: List[str] = []
    t = clean_text(title)
    if not t:
        issues.append("标题为空")
        return issues
    n = len(t)
    if n > 200:
        issues.append(f"标题超长 {n}/200，不能确认")
    elif n > 190:
        issues.append(f"接近上限 {n}/200，后续加词空间很小")
    elif n < 120:
        issues.append(f"标题偏短 {n}/140-200，可能缺少SEO信息")
    if not t.lower().startswith("alpinaluz"):
        issues.append("品牌 Alpinaluz 没有放第一位")
    if re.search(r"[一-鿿]", t):
        issues.append("标题含中文")
    sku = clean_text(st.session_state.get("sku", ""))
    if sku and sku.lower() in t.lower():
        issues.append("标题含 SKU / 型号代码")
    if has_naked_cm(t):
        issues.append("出现裸 cm，前面没有具体数字")
    return issues


def candidate_display_risk(c: Dict[str, str], lang: str) -> str:
    title = c.get("title", "")
    issues = title_quality_issues(title, lang)
    soft = title_soft_issues(title, lang)
    model_risk = sanitize_model_risk(c.get("risk", ""))
    parts = []
    if issues:
        parts.extend(issues)
    if soft:
        parts.extend(soft)
    if model_risk and model_risk not in {"无", "无明显风险", "ninguno", "none", "no", "sem riscos", "aucun risque"}:
        parts.append(model_risk)
    if not parts:
        parts.append("无明显风险")
    return "；".join(dict.fromkeys(parts))

def render_title_length_box(title: str, lang: str) -> bool:
    n = len(clean_text(title))
    issues = title_quality_issues(title, lang)
    soft = title_soft_issues(title, lang)
    hard = title_blocking_issues(title, lang)
    blocking = n > 200 or not clean_text(title) or bool(hard)
    cls = "bad" if blocking else ("warn" if issues or soft else "ok")
    msg = f"标题长度：{n}/200"
    notes = issues + soft
    if notes:
        msg += "｜" + "；".join(notes)
    else:
        msg += "｜可确认"
    st.markdown(f"<div class='{cls}'>{html.escape(msg)}</div>", unsafe_allow_html=True)
    return not blocking

def render_candidate_cards(cands: List[Dict[str, str]], lang: str, prefix: str, compact: bool = None) -> None:
    """Render candidates. In newbie mode show only AI recommended by default; alternatives are folded."""
    if compact is None:
        compact = bool(st.session_state.get("newbie_auto_title", True))
    if not cands:
        return
    selected_idx = int(st.session_state.get(f"selected_candidate_idx::{lang}", best_candidate_index(cands, lang)))
    recommended_idx = best_candidate_index(cands, lang)

    def one_card(i: int, c: Dict[str, str]) -> None:
        title = c.get("title", "")
        zh = c.get("zh", "")
        why = c.get("why", "") or c.get("kept", "")
        risk = candidate_display_risk(c, lang)
        n = len(title)
        selected = (i == selected_idx)
        recommended = (i == recommended_idx)
        border = "#22c55e" if recommended else ("#60a5fa" if selected else "#334155")
        badges = []
        if recommended:
            badges.append("AI推荐")
        if selected:
            badges.append("当前标题")
        if not badges:
            badges.append("备选")
        st.markdown(
            f"""<div class='candidate-card {'recommended' if recommended else ''}' style='border-color:{border};'>
            <div class='small-muted'>候选{i+1} · {n}/200 字符 · {html.escape(' / '.join(badges))}</div>
            <div class='candidate-title'>{html.escape(title)}</div>
            <div class='candidate-zh'>中文：{html.escape(zh or '暂无中文解释')}</div>
            <div class='small-muted'>风险/注意：{html.escape(risk)}</div>
            {f"<div class='small-muted'>核心保留：{html.escape(why)}</div>" if why else ""}
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button(f"选择候选 {i+1}", key=f"select_candidate::{prefix}::{i+1}"):
            st.session_state[f"selected_candidate_idx::{lang}"] = i
            set_current_title(lang, title, zh)
            st.rerun()

    if compact:
        st.markdown("##### AI 推荐标题（新手默认只看这个）")
        one_card(recommended_idx, cands[recommended_idx])
        with st.expander("高级：查看另外两个候选 / 手动选择", expanded=False):
            for i, c in enumerate(cands):
                if i != recommended_idx:
                    one_card(i, c)
    else:
        for i, c in enumerate(cands):
            one_card(i, c)

def clean_listing(data: Dict[str, Any], lang: str) -> Dict[str, Any]:
    title = normalize_title(st.session_state.get("confirmed_titles", {}).get(lang, "") or data.get("title", ""), lang)
    bullets = data.get("bullets") or []
    bullets_zh = data.get("bullets_zh") or []
    if not isinstance(bullets, list):
        bullets = [str(bullets)]
    if not isinstance(bullets_zh, list):
        bullets_zh = [str(bullets_zh)]
    bullets = [clean_text(x) for x in bullets if clean_text(x)][:5]
    bullets_zh = [clean_text(x) for x in bullets_zh if clean_text(x)][:5]
    while len(bullets) < 5:
        bullets.append("")
    while len(bullets_zh) < 5:
        bullets_zh.append("")
    aplus = data.get("aplus") or []
    if not isinstance(aplus, list):
        aplus = []
    return {
        "title": title,
        "title_zh": clean_text(data.get("title_zh") or st.session_state.get("confirmed_title_zh", {}).get(lang, "")),
        "bullets": bullets[:5],
        "bullets_zh": bullets_zh[:5],
        "description": str(data.get("description", "")).strip(),
        "description_zh": str(data.get("description_zh", "")).strip(),
        "search_terms": clean_text(data.get("search_terms", ""))[:250],
        "search_terms_zh": str(data.get("search_terms_zh", "")).strip(),
        "aplus": aplus[:5],
    }


def listing_to_text(lang: str, data: Dict[str, Any]) -> str:
    lines = [f"[{lang}]", "", "[TITLE]", data.get("title", ""), "", "[标题中文解释]", data.get("title_zh", ""), "", "[BULLETS]"]
    for i, b in enumerate(data.get("bullets", [])[:5], 1):
        lines.append(f"{i}. {b}")
    lines += ["", "[五点中文解释]"]
    for i, b in enumerate(data.get("bullets_zh", [])[:5], 1):
        lines.append(f"{i}. {b}")
    lines += ["", "[DESCRIPTION]", data.get("description", ""), "", "[长描述中文解释]", data.get("description_zh", ""), "", "[SEARCH TERMS]", data.get("search_terms", ""), "", "[Search Terms中文解释]", data.get("search_terms_zh", "")]
    if data.get("aplus"):
        lines += ["", "[A+]"]
        for idx, m in enumerate(data.get("aplus", []), 1):
            if not isinstance(m, dict):
                continue
            lines.append(f"模块{idx} 标题：{m.get('title','')}")
            lines.append(f"模块{idx} 正文：{m.get('body','')}")
            lines.append(f"模块{idx} 中文配图提示：{m.get('image_prompt_zh','')}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_stats(data: Dict[str, Any]) -> None:
    title_len = len(data.get("title", ""))
    st.markdown("#### 字数检测")
    st.markdown(f"<div class='{ 'ok' if 120 <= title_len <= 210 else 'warn'}'>标题: {title_len} 字符 / 建议 140-200</div>", unsafe_allow_html=True)
    for i, b in enumerate(data.get("bullets", [])[:5], 1):
        n = len(b)
        cls = "ok" if 130 <= n <= 260 else "warn"
        st.markdown(f"<div class='{cls}'>五点{i}: {n} 字符 / 建议 150-250</div>", unsafe_allow_html=True)
    dlen = len(data.get("description", ""))
    st.markdown(f"<div class='{ 'ok' if dlen >= 700 else 'warn'}'>长描述: {dlen} 字符 / 建议 ≥700</div>", unsafe_allow_html=True)
    slen = len(data.get("search_terms", ""))
    st.markdown(f"<div class='{ 'ok' if slen <= 250 else 'bad'}'>Search Terms: {slen} 字符 / ≤250</div>", unsafe_allow_html=True)


def make_zip() -> bytes:
    mem = io.BytesIO()
    sku = st.session_state.get("sku", "SKU") or "SKU"
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for lang, data in st.session_state.get("listings", {}).items():
            if data:
                z.writestr(f"listing/{lang}_Listing.txt", listing_to_text(lang, data))
        z.writestr("README.txt", f"Alpinaluz Listing Generator {APP_VERSION}\n只导出 listing 文件，标题均来自人工确认标题。\n")
    mem.seek(0)
    return mem.getvalue()

# ------------------------- UI sidebar -------------------------
with st.sidebar:
    st.header("API 与模式")
    st.text_input("OpenAI API Key", type="password", key="openai_api_key")
    st.selectbox("主力模型", ["gpt-5.4", "gpt-5.5", "gpt-4.1"], key="model", index=0)
    st.selectbox("推理强度", ["low", "medium", "high"], key="reasoning_effort", index=1)
    st.selectbox("标题中文快译模型", ["gpt-5.4-mini", "gpt-5.4"], key="translation_model", index=0)
    st.number_input("图片事实识别最多张数", min_value=0, max_value=6, value=3, step=1, key="image_limit", help="建议最多3张：主图、尺寸图、关键细节图。")
    st.checkbox("生成完成声音提示", value=True, key="sound_notify")
    st.checkbox("新手模式：AI自动推荐标题", value=True, key="newbie_auto_title", help="默认只显示AI推荐标题，其他候选折叠到高级区。")
    st.markdown("---")
    st.header("目标国家")
    st.multiselect("选择要做的国家", TARGET_LANGS, default=st.session_state.get("target_langs", TARGET_LANGS), key="target_langs")
    st.selectbox("正文输出范围", ["标准包：标题+五点+描述+Search Terms", "完整包：标准包+A+"], key="listing_mode")
    st.markdown("---")
    totals = usage_totals()
    st.header("费用估算")
    st.metric("调用次数", totals["calls"])
    st.metric("估算费用", f"${totals['cost']:.3f}")
    st.caption(f"输入 {totals['input']:,} / 输出 {totals['output']:,} tokens")
    with st.expander("最近调用", expanded=False):
        for x in reversed(st.session_state.get("api_usage_log", [])[-10:]):
            st.write(f"{x['label']} · {x['model']} · in {x['input_tokens']:,} / out {x['output_tokens']:,} · ${x['cost']:.3f}")
    if st.button("清空费用统计"):
        st.session_state["api_usage_log"] = []
        st.rerun()

# ------------------------- header -------------------------
st.title(f"Alpinaluz Listing Generator {APP_VERSION}")
st.markdown("<div class='info-card'>新流程：①资料与事实卡 → ②ES标题确认 → ③AI预审多国标题 → ④绿色批量确认/黄色人工检查 → ⑤统一生成正文。V17.7 增加低误报风险引擎、多语言产品类型同义词、木色/金色误报修复和更安全的一键确认。</div>", unsafe_allow_html=True)

# ------------------------- Section 1: input and facts -------------------------
st.header("1）资料输入与产品事实卡")
col1, col2 = st.columns([1.05, 1])
with col1:
    st.text_input("SKU", key="sku")
    st.text_input("EAN", key="ean")
    st.text_input("品牌", value=st.session_state.get("brand", "Alpinaluz"), key="brand")
    st.text_input("产品系列名（可选，默认不进标题）", key="series", help="例如 SUNSET / TOURS。默认不会强行写入标题，除非它本身是核心搜索词。")
    st.text_area("旧 Amazon / 网站内容（标题、五点、长描述可一起粘贴）", key="old_content", height=180)
    st.text_area("手动标题 / 原始标题（推荐填）", key="manual_title", height=80)
    st.text_area("技术备注（不能错的事实）", key="tech_notes", height=100, placeholder="例如：E27灯头，灯泡不含；最大40W；不是LED集成；尺寸Ø18 cm；材质金属+玻璃。")
    st.text_area("SEO关键词（可选）", key="seo_keywords", height=70)
    st.text_area("手动长描述（可选）", key="manual_description", height=100)
    uploads = st.file_uploader("上传图片（建议最多3张：主图/尺寸图/细节图）", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    usable_images = []
    if uploads:
        st.markdown("图片用于事实识别（可排除不适合图片）：")
        for idx, f in enumerate(uploads):
            ex = st.checkbox(f"排除：{f.name}", key=uploaded_image_key(f, idx), help="比如不是当前SKU、尺寸不对应、灯泡详情图容易误导等。")
            if not ex:
                usable_images.append(f)

# If the product identity changed, clear generated facts/titles/listings so old socket/concept risks cannot leak into the new product.
reset_generated_state_if_product_changed()

with col2:
    st.subheader("产品事实卡")
    if st.button("AI识别 / 更新产品事实卡"):
        try:
            with st.spinner("正在识别产品事实卡，只做一次，后面会复用以节省token..."):
                raw = llm_multimodal(generate_fact_prompt(), usable_images, "你是灯具产品事实识别专家，只输出产品事实JSON，不写营销文案。", label="产品事实卡")
                data = safe_json(raw, {})
                if isinstance(data, dict):
                    st.session_state["fact_card"] = {k: data.get(k, "") for k in FACT_KEYS}
                    st.success("事实卡已生成，请人工检查。")
                else:
                    st.error("事实卡解析失败，请重试或减少输入内容。")
        except Exception as e:
            st.error(str(e))
    fc = st.session_state.get("fact_card", {}) or {}
    if fc:
        for k in FACT_KEYS:
            val = fc.get(k, "")
            if isinstance(val, list):
                val = ", ".join(str(x) for x in val)
            label = f"{FACT_LABELS.get(k, k)}（{k}）"
            new_val = st.text_area(label, value=str(val or ""), key=f"fact_edit::{k}", height=60 if k not in ["core_selling_points", "must_keep_in_titles", "do_not_claim", "notes_for_copy"] else 95)
            fc[k] = new_val
        st.session_state["fact_card"] = fc
    else:
        st.info("先填写资料并点击 AI识别。事实卡正确后再生成标题。")

# ------------------------- Section 2: ES title chat -------------------------
st.header("2）ES 标题聊天确认")
st.markdown("<div class='info-card'>线性流程：先生成候选 → 点击候选即选中 → 在当前标题框微调 → 输入中文要求生成下一轮 → 确认标题。下一轮永远基于当前选中的标题修改。</div>", unsafe_allow_html=True)

es_cands = st.session_state.get("es_title_candidates", [])

# Step 2A: generate first candidates
if not es_cands:
    if st.button("生成 3 个 ES 标题候选"):
        try:
            with st.spinner("正在生成 ES 标题候选..."):
                raw = llm(es_title_prompt(), "你是 Amazon.es 灯具标题专家。输出严格 JSON。", label="ES标题候选")
                es_cands = parse_candidates(raw, "ES")
                es_cands = maybe_auto_compress_candidates("ES", es_cands, "ES")
                st.session_state["es_title_candidates"] = es_cands
                st.session_state["es_cand_version"] = int(st.session_state.get("es_cand_version", 0)) + 1
                if es_cands:
                    auto_select_best_candidate("ES", es_cands)
                notify_done("ES标题候选已生成")
                st.rerun()
        except Exception as e:
            st.error(str(e))

# Step 2B: show candidates; clicking a candidate selects it
es_cands = st.session_state.get("es_title_candidates", [])
if es_cands:
    st.subheader("ES 候选标题：AI已自动推荐，其他候选在高级区")
    render_candidate_cards(es_cands, "ES", f"es::{st.session_state.get('es_cand_version', 0)}")

# Step 2C: current title
current_es_value = st.session_state.get("selected_es_title", "")
es_edit_key = current_title_widget_key("ES")
edited_es_title = st.text_area("当前 ES 标题（这里就是最终确认对象，可手动微调）", value=current_es_value, key=es_edit_key, height=90)
es_can_confirm = render_title_length_box(edited_es_title, "ES")
if st.session_state.get("selected_es_title_zh"):
    st.markdown(f"<div class='zhbox'><b>当前中文解释：</b>{html.escape(st.session_state.get('selected_es_title_zh',''))}</div>", unsafe_allow_html=True)

# Step 2D: chat refine and confirm
st.text_area("针对当前标题的中文修改要求", key="es_title_chat", height=80, placeholder="例如：保留三头吊灯和75cm；删掉过多场景；更突出餐桌和厨房岛台；控制在190字符以内。")
es_btn1, es_btn2, es_btn3 = st.columns([1, 1, 1])
with es_btn1:
    if st.button("基于当前标题生成下一轮 3 个 ES 选项"):
        try:
            base = normalize_title(edited_es_title, "ES")
            st.session_state.setdefault("title_history", {}).setdefault("ES", []).append(base)
            instr = f"请只基于以下当前标题优化，生成新一轮3个候选；不要回到原始标题重新写。\n当前标题：{base}\n修改要求：{st.session_state.get('es_title_chat','') or '在不改变产品事实的前提下，提高亚马逊标题质量，并保持200字符以内。'}"
            with st.spinner("正在根据当前标题生成下一轮 ES 候选..."):
                raw = llm(es_title_prompt(instr), "你是 Amazon.es 灯具标题专家。输出严格 JSON。", label="ES标题下一轮")
                cands = parse_candidates(raw, "ES")
                cands = maybe_auto_compress_candidates("ES", cands, "ES下一轮")
                st.session_state["es_title_candidates"] = cands
                st.session_state["es_cand_version"] = int(st.session_state.get("es_cand_version", 0)) + 1
                if cands:
                    auto_select_best_candidate("ES", cands)
                notify_done("ES下一轮标题已生成")
                st.rerun()
        except Exception as e:
            st.error(str(e))
with es_btn2:
    if st.button("回退 ES 标题"):
        hist = st.session_state.setdefault("title_history", {}).setdefault("ES", [])
        if hist:
            prev = hist.pop()
            set_current_title("ES", prev, zh_translate_title(prev, "ES"))
            st.rerun()
with es_btn3:
    if st.button("确认当前 ES 标题", disabled=not es_can_confirm):
        title = normalize_title(edited_es_title, "ES")
        st.session_state["selected_es_title"] = title
        st.session_state.setdefault("confirmed_titles", {})["ES"] = title
        zh = st.session_state.get("selected_es_title_zh") or "已按当前 ES 标题确认，请以标题原文为准。"
        st.session_state.setdefault("confirmed_title_zh", {})["ES"] = zh
        st.success("ES 标题已确认")
        st.rerun()
if not es_can_confirm and edited_es_title:
    st.caption("标题超过200字符、含中文或为空时不能确认。请手动缩短，或在中文修改要求里写“压缩到190字符以内”。")

# ------------------------- Section 3: per-language title confirmation -------------------------
st.header("3）逐国语言标题确认")
if not st.session_state.get("confirmed_titles", {}).get("ES"):
    st.warning("请先确认 ES 标题。")
else:
    st.markdown("<div class='info-card'>先一键生成所有国家首轮候选，然后逐国审核。点击候选即选中；下一轮优化永远基于当前标题；确认按钮锁定当前标题框中的标题。</div>", unsafe_allow_html=True)
    target_langs = st.session_state.get("target_langs", TARGET_LANGS)

    # status overview
    status_html = []
    for l in target_langs:
        conf = st.session_state.get("confirmed_titles", {}).get(l, "")
        cur = st.session_state.get(f"current_title::{l}", "")
        issues = title_quality_issues(conf or cur, l) if (conf or cur) else ["未生成"]
        soft = title_soft_issues(conf or cur, l) if (conf or cur) else []
        if conf and not any("超长" in x or "含中文" in x or "标题为空" in x for x in issues):
            cls, txt = "s-ok", "已确认"
        elif cur and any("超长" in x or "含中文" in x for x in issues):
            cls, txt = "s-bad", "需修改"
        elif cur and soft:
            cls, txt = "s-warn", "建议检查"
        elif cur:
            cls, txt = "s-warn", "待确认"
        else:
            cls, txt = "s-warn", "未生成"
        status_html.append(f"<span class='status-pill {cls}'>{l} {txt}</span>")
    st.markdown(" ".join(status_html), unsafe_allow_html=True)

    # Newbie bulk-confirm: confirm all current titles that have no blocking risk.
    auto_ready = []
    auto_blocked = []
    for l in target_langs:
        if st.session_state.get("confirmed_titles", {}).get(l):
            continue
        cur = st.session_state.get(f"current_title::{l}", "")
        if cur and auto_confirmable_title(cur, l):
            auto_ready.append(l)
        elif cur:
            auto_blocked.append(l)
    if auto_ready:
        st.markdown(f"<div class='ok'>AI推荐可直接确认：{', '.join(auto_ready)}</div>", unsafe_allow_html=True)
        if st.button(f"确认全部无风险标题（{len(auto_ready)} 个）"):
            for l in auto_ready:
                title = normalize_title(st.session_state.get(f"current_title::{l}", ""), l)
                st.session_state.setdefault("confirmed_titles", {})[l] = title
                st.session_state.setdefault("confirmed_title_zh", {})[l] = st.session_state.get(f"current_title_zh::{l}", "")
            st.success("已确认全部无风险标题。")
            st.rerun()
    if auto_blocked:
        st.markdown(f"<div class='warn'>这些国家仍需人工检查（硬风险或软风险）：{', '.join(auto_blocked)}</div>", unsafe_allow_html=True)

    batch_col1, batch_col2 = st.columns([1, 2])
    with batch_col1:
        if st.button("一键批量生成所有未生成国家首轮标题候选（推荐）"):
            langs_to_gen = [l for l in target_langs if not st.session_state.get("title_candidates", {}).get(l)]
            if not langs_to_gen:
                st.info("所有目标国家已经有候选标题。")
            else:
                try:
                    with st.spinner("正在一次性生成多国首轮标题候选..."):
                        raw = llm(batch_lang_title_prompt(langs_to_gen), "你是多国 Amazon 灯具标题本地化专家。输出严格 JSON。", label="多国标题首轮批量")
                        result = parse_batch_candidates(raw, langs_to_gen)
                        for lang, cands2 in result.items():
                            cands2 = maybe_auto_compress_candidates(lang, cands2, "多国首轮")
                            st.session_state.setdefault("title_candidates", {})[lang] = cands2
                            bump_lang_version(lang)
                            if cands2:
                                auto_select_best_candidate(lang, cands2)
                        missing_batch = [l for l in langs_to_gen if not result.get(l)]
                        if missing_batch:
                            st.warning("这些语言批量解析失败，可逐国生成：" + ", ".join(missing_batch))
                        notify_done("多国首轮标题候选已生成")
                        st.rerun()
                except Exception as e:
                    st.error(str(e))
    with batch_col2:
        st.caption("候选卡片会显示标题全文、中文解释和风险。标题超过200字符会标红，并禁止确认。")

    tabs = st.tabs(target_langs)
    for tab, lang in zip(tabs, target_langs):
        with tab:
            st.subheader(f"{lang} · {LANGS[lang]['market']} 标题")
            confirmed = st.session_state.get("confirmed_titles", {}).get(lang, "")
            if confirmed:
                st.markdown("<span class='status-pill s-ok'>已确认</span>", unsafe_allow_html=True)
                st.text_area("已确认标题", value=confirmed, key=f"confirmed_show::{lang}", height=90, disabled=True)
                st.markdown(f"<div class='zhbox'><b>中文解释：</b>{html.escape(st.session_state.get('confirmed_title_zh', {}).get(lang,''))}</div>", unsafe_allow_html=True)
                if st.button(f"取消确认并继续修改 {lang}", key=f"unlock::{lang}"):
                    st.session_state.setdefault("confirmed_titles", {}).pop(lang, None)
                    st.session_state.setdefault("confirmed_title_zh", {}).pop(lang, None)
                    st.rerun()
                continue

            # first generation if needed
            if not st.session_state.get("title_candidates", {}).get(lang):
                if st.button(f"生成 {lang} 3 个标题候选", key=f"gen_title::{lang}"):
                    try:
                        with st.spinner(f"正在生成 {lang} 标题候选..."):
                            raw = llm(lang_title_prompt(lang), f"你是 {LANGS[lang]['market']} 灯具标题本地化专家。输出严格 JSON。", label=f"{lang}标题候选")
                            cands2 = parse_candidates(raw, lang)
                            cands2 = maybe_auto_compress_candidates(lang, cands2, f"{lang}首轮")
                            st.session_state.setdefault("title_candidates", {})[lang] = cands2
                            bump_lang_version(lang)
                            if cands2:
                                auto_select_best_candidate(lang, cands2)
                            notify_done(f"{lang} 标题候选已生成")
                            st.rerun()
                    except Exception as e:
                        st.error(str(e))

            cands2 = st.session_state.get("title_candidates", {}).get(lang, [])
            if cands2:
                st.markdown("##### AI推荐标题；其他候选在高级区")
                version = int(st.session_state.setdefault("lang_cand_version", {}).get(lang, 0))
                render_candidate_cards(cands2, lang, f"cand::{lang}::{version}")

            current_key = f"current_title::{lang}"
            zh_key = f"current_title_zh::{lang}"
            current_value = st.session_state.get(current_key, "")
            edit_key = current_title_widget_key(lang)
            edited_title = st.text_area("当前标题（这里就是确认对象，可手动微调）", value=current_value, key=edit_key, height=90)
            can_confirm = render_title_length_box(edited_title, lang)
            if st.session_state.get(zh_key):
                st.markdown(f"<div class='zhbox'><b>当前中文解释：</b>{html.escape(st.session_state.get(zh_key,''))}</div>", unsafe_allow_html=True)

            st.text_area("针对当前标题的中文修改要求", key=f"chat::{lang}", height=80, placeholder="例如：加入餐桌关键词，但压缩到190字符以内；保留3灯和75cm；删掉卧室；语序更自然。")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button(f"基于当前标题生成下一轮 {lang} 3 个选项", key=f"refine::{lang}"):
                    try:
                        base = normalize_title(edited_title, lang)
                        st.session_state.setdefault("title_history", {}).setdefault(lang, []).append(base)
                        instr = f"请只基于以下当前标题优化，生成新一轮3个候选；不要回到ES标题重新直译。\n当前标题：{base}\n修改要求：{st.session_state.get(f'chat::{lang}', '') or '在不改变产品事实的前提下，提高本地Amazon标题质量，并保持200字符以内。'}"
                        with st.spinner(f"正在优化 {lang} 标题..."):
                            raw = llm(lang_title_prompt(lang, instr), f"你是 {LANGS[lang]['market']} 灯具标题本地化专家。输出严格 JSON。", label=f"{lang}标题下一轮")
                            cands_new = parse_candidates(raw, lang)
                            cands_new = maybe_auto_compress_candidates(lang, cands_new, f"{lang}下一轮")
                            st.session_state.setdefault("title_candidates", {})[lang] = cands_new
                            bump_lang_version(lang)
                            if cands_new:
                                auto_select_best_candidate(lang, cands_new)
                            notify_done(f"{lang} 下一轮标题已生成")
                            st.rerun()
                    except Exception as e:
                        st.error(str(e))
            with c2:
                if st.button(f"回退 {lang}", key=f"undo::{lang}"):
                    hist = st.session_state.setdefault("title_history", {}).setdefault(lang, [])
                    if hist:
                        prev = hist.pop()
                        set_current_title(lang, prev, zh_translate_title(prev, lang))
                        st.rerun()
            with c3:
                if st.button(f"确认 {lang} 标题", key=f"confirm::{lang}", disabled=not can_confirm):
                    title = normalize_title(edited_title, lang)
                    st.session_state[current_key] = title
                    st.session_state.setdefault("confirmed_titles", {})[lang] = title
                    zh = st.session_state.get(zh_key) or "已按当前标题确认，请以标题原文为准。"
                    st.session_state.setdefault("confirmed_title_zh", {})[lang] = zh
                    st.success(f"{lang} 标题已确认")
                    st.rerun()
            if not can_confirm and edited_title:
                st.caption("标题超过200字符、含中文或为空时不能确认。请手动缩短，或要求 AI 压缩到190字符以内。")
# ------------------------- Section 4: generate content -------------------------
st.header("4）标题确认后生成正文")
confirmed_titles = st.session_state.get("confirmed_titles", {})
selected_langs = ["ES"] + st.session_state.get("target_langs", TARGET_LANGS)
missing = [l for l in selected_langs if not confirmed_titles.get(l)]
status_cols = st.columns(3)
status_cols[0].metric("已确认标题", len(selected_langs) - len(missing))
status_cols[1].metric("待确认标题", len(missing))
status_cols[2].metric("目标语言", len(selected_langs))
if missing:
    st.warning("还有标题未确认：" + ", ".join(missing) + "。标题未确认前不建议生成正文。")
else:
    include_aplus = st.session_state.get("listing_mode", "").startswith("完整包")
    if st.button("逐国生成所有正文（标题不再修改）"):
        for lang in selected_langs:
            try:
                with st.spinner(f"正在生成 {lang} 正文..."):
                    raw = llm(listing_prompt(lang, include_aplus), f"你是 {LANGS[lang]['market']} 灯具 Listing 本地文案专家。输出严格 JSON。", label=f"{lang}正文生成")
                    data = safe_json(raw, {})
                    if not isinstance(data, dict):
                        raise ValueError("JSON解析失败")
                    st.session_state.setdefault("listings", {})[lang] = clean_listing(data, lang)
            except Exception as e:
                st.error(f"{lang} 失败：{e}")
        notify_done("正文生成完成")

# ------------------------- Section 5: preview and export -------------------------
st.header("5）预览与导出")
listings = st.session_state.get("listings", {})
if listings:
    tabs = st.tabs([l for l in selected_langs if listings.get(l)])
    for tab, lang in zip(tabs, [l for l in selected_langs if listings.get(l)]):
        with tab:
            st.text_area(f"{lang} Listing", value=listing_to_text(lang, listings[lang]), height=560, key=f"listing_text::{lang}")
            render_stats(listings[lang])
    st.download_button(
        "下载 ZIP（只含 listing）",
        data=make_zip(),
        file_name=f"{st.session_state.get('sku','SKU')}_{date.today().isoformat()}_AMAZON_LISTING_V17.zip",
        mime="application/zip",
    )
else:
    st.info("正文生成后会在这里预览，并可下载只含 listing 的 ZIP。")
