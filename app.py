import base64
import io
import json
import re
import html
import hashlib
import zipfile
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import streamlit as st
import streamlit.components.v1 as components

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

APP_VERSION = "V18.2.8"
TITLE_LIMIT = 75
HIGHLIGHT_LIMIT = 125
HIGHLIGHT_IDEAL_MIN = 95
HIGHLIGHT_IDEAL_MAX = 115
HIGHLIGHT_SOFT_MIN = 95
LEGACY_TITLE_LIMIT = 200

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

# Amazon / EU safety: do not mention halogen or deprecated/banned bulb families.
# This is a hard marketplace safety rule for every generated field.
BULB_FORBIDDEN_PATTERNS = [
    r"\bhalogen\w*\b", r"\bhalógen\w*\b", r"\bhalog[eè]n\w*\b", r"\bal[oó]gen\w*\b", r"\bhalogeen\w*\b", r"\bhalogenow\w*\b",
    r"\bincandescent\w*\b", r"\bincandescent[eis]?\w*\b", r"\bgl[oö]dlampa\w*\b",
    r"\bedison\w*\b",
    r"\btraditional\w*\b", r"\btradicional\w*\b", r"\btraditionnel\w*\b", r"\btradizional\w*\b",
    r"\bstandard\s+(?:bulb|bulbs|lamp|lamps|leuchtmittel|lampadine|ampoules)\b",
    r"\bbombillas?\s+(?:tradicionales|est[aá]ndar)\b",
]

SAFE_BULB_COPY_RULE = (
    "灯泡兼容安全规则：只写兼容对应灯头的 LED 灯泡 + 最大功率 + 灯泡不包含。"
    "禁止提及卤素、白炽、Edison、traditional/tradicional、standard bulb 等高风险灯泡类型。"
)

FACT_KEYS = [
    "product_type", "series_name", "key_structure", "materials", "colors", "dimensions", "socket_or_led",
    "bulb_included", "power", "cct_or_dimming", "adjustability", "installation",
    "power_connection", "plug_cable", "switch_included", "switch_type", "cable_length", "plug_type",
    "indoor_outdoor",
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
    "power_connection": "供电方式",
    "plug_cable": "是否带插头线",
    "switch_included": "是否带开关",
    "switch_type": "开关类型 / 位置",
    "cable_length": "电源线长度",
    "plug_type": "插头类型",
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
.concept-ok { color:#bbf7d0!important; font-size:12px; margin-top:4px; }
.concept-muted { color:#94a3b8!important; font-size:12px; margin-top:4px; }
.status-table { width:100%; border-collapse:collapse; margin:8px 0 12px 0; }
.status-table td,.status-table th { border-bottom:1px solid #334155; padding:7px 8px; color:#f8fafc; vertical-align:top; }
.status-table th { color:#cbd5e1; font-weight:700; }

.highlight-callout { background:#052e16; border:2px solid #22c55e; border-radius:12px; padding:10px 12px; margin:8px 0; font-size:15px; font-weight:900; color:#dcfce7!important; line-height:1.45; }
.highlight-callout .label { color:#86efac!important; font-size:12px; letter-spacing:.02em; text-transform:uppercase; display:block; margin-bottom:4px; }
.length-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin:8px 0; }
.length-card { border-radius:12px; padding:10px 12px; border:2px solid #334155; background:#0f172a; }
.length-card.ok-len { border-color:#22c55e; background:#052e16; }
.length-card.warn-len { border-color:#f59e0b; background:#3f2f05; }
.length-card.bad-len { border-color:#ef4444; background:#3f1212; }
.length-card .k { color:#cbd5e1!important; font-size:12px; font-weight:700; }
.length-card .v { color:#f8fafc!important; font-size:22px; font-weight:900; line-height:1.1; }
.length-card .hint { color:#e5e7eb!important; font-size:12px; margin-top:3px; }
.export-warning { background:#451a1a; border:2px solid #ef4444; border-radius:12px; padding:10px 12px; margin:8px 0; color:#fee2e2!important; font-weight:800; }
/* V18.2.8: force any accidental markdown/code/debug blocks to follow dark theme. */
pre, code, .stMarkdown pre, .stMarkdown code, [data-testid="stCodeBlock"], [data-testid="stCodeBlock"] pre, [data-testid="stCodeBlock"] code { background:#0f172a!important; color:#f8fafc!important; border-color:#334155!important; }
.stMarkdown pre, [data-testid="stCodeBlock"] pre { border:1px solid #334155!important; border-radius:10px!important; padding:8px 10px!important; white-space:pre-wrap!important; }
textarea, input, div[contenteditable="true"] { background:#0f172a!important; color:#f8fafc!important; -webkit-text-fill-color:#f8fafc!important; }
.safe-text { white-space:normal; word-break:break-word; }
hr { border-color:#334155!important; }
pre, code, kbd, samp { background:#0f172a!important; color:#f8fafc!important; border:1px solid #334155!important; border-radius:8px!important; white-space:pre-wrap!important; word-break:break-word!important; }
.stCode, [data-testid="stCodeBlock"], [data-testid="stMarkdownContainer"] pre { background:#0f172a!important; color:#f8fafc!important; }
textarea, input, [contenteditable="true"] { background:#0f172a!important; color:#f8fafc!important; -webkit-text-fill-color:#f8fafc!important; caret-color:#f8fafc!important; }
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
        "confirmed_highlights": {},
        "confirmed_highlight_zh": {},
        "confirmed_legacy_titles": {},
        "item_highlights": {},
        "title_candidates": {},
        "title_history": {},
        "listings": {},
        "target_langs": TARGET_LANGS.copy(),
        "es_intent_include": "",
        "es_intent_exclude": "",
        "es_intent_demote": "",
        "es_intent_history": [],
                "es_cand_version": 0,
        "lang_cand_version": {},
        "newbie_auto_title": True,
        "use_compressed_master": True,
        "skip_existing_listings": True,
        "generate_listing_zh": False,
        "compressed_master_cache": "",
        "compressed_master_signature": "",
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
            "confirmed_titles", "confirmed_title_zh", "confirmed_highlights", "confirmed_highlight_zh", "confirmed_legacy_titles", "item_highlights", "title_candidates", "title_history", "listings",
            "selected_es_title_zh_source", "lang_cand_version", "es_cand_version",
            "es_intent_include", "es_intent_exclude", "es_intent_demote", "es_intent_history",
        ]:
            if key in st.session_state:
                if key in ["confirmed_titles", "confirmed_title_zh", "confirmed_highlights", "confirmed_highlight_zh", "confirmed_legacy_titles", "item_highlights", "title_candidates", "title_history", "listings", "fact_card", "lang_cand_version"]:
                    st.session_state[key] = {}
                elif key == "es_intent_history":
                    st.session_state[key] = []
                elif key in ["es_intent_include", "es_intent_exclude", "es_intent_demote"]:
                    st.session_state[key] = ""
                elif key == "es_title_candidates":
                    st.session_state[key] = []
                elif key == "es_cand_version":
                    st.session_state[key] = 0
                else:
                    st.session_state[key] = ""
        # Clear language current titles and edit versions.
        for k in list(st.session_state.keys()):
            if k.startswith(("current_title::", "current_title_zh::", "current_title_zh_source::", "current_highlight::", "current_highlight_zh::", "current_legacy_title::", "highlight_edit::", "legacy_title_edit::", "title_edit_version::", "selected_candidate_idx::", "title_edit::")):
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


def record_usage(label: str, model: str, resp: Any = None, input_hint: str = "", output_hint: str = "", image_count: int = 0, note: str = ""):
    inp, out = _usage_tokens(resp) if resp is not None else (0, 0)
    estimated = False
    if not inp and not out:
        inp = estimate_text_tokens(input_hint) + image_count * 1200
        out = estimate_text_tokens(output_hint)
        estimated = True
    price = PRICE.get(model, PRICE.get("gpt-5.4"))
    cost = inp / 1_000_000 * price["input"] + out / 1_000_000 * price["output"]
    st.session_state.setdefault("api_usage_log", []).append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "label": label, "model": model, "input_tokens": inp, "output_tokens": out,
        "total_tokens": inp + out, "cost": cost, "estimated": estimated, "image_count": image_count,
        "note": note,
    })


def record_rule_step(label: str, note: str = "规则处理 / 跳过，无模型调用"):
    st.session_state.setdefault("api_usage_log", []).append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "label": label, "model": "RULE", "input_tokens": 0, "output_tokens": 0,
        "total_tokens": 0, "cost": 0.0, "estimated": False, "image_count": 0, "note": note,
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


def safe_html_text(s: Any) -> str:
    """HTML-escape text and neutralize markdown code fences/backticks.
    Streamlit markdown may render ``` inside unsafe HTML as a white code block;
    this keeps candidate cards dark and prevents raw JSON/debug boxes.
    """
    return html.escape(str(s or "")).replace("`", "&#96;")


def looks_like_raw_payload(s: Any) -> bool:
    """Detect accidental raw JSON / code-fence content in zh/risk fields."""
    t = str(s or "").strip()
    if not t:
        return False
    low = t.lower()
    if "```" in t or "risk_code" in low:
        return True
    if (t.startswith("{") or t.startswith("[")) and any(k in low for k in ['"title"', '"highlight"', 'item_highlight', 'legacy_title']):
        return True
    if any(k in low for k in ['{"title"', "{'title'", '"highlight"', "'highlight'", 'json array', 'json object']):
        return True
    return False


def looks_like_poor_zh_note(txt: str) -> bool:
    t = clean_text(txt)
    if not t:
        return True
    if t in {"中文解释未生成", "暂无中文解释"}:
        return True
    # Very short comma-separated keyword fragments are not useful for new staff.
    if len(t) < 12 and "、" in t:
        return True
    if t.count("、") >= 3 and not any(p in t for p in "。；：，适合采用带配备支持方便用于可"):
        return True
    # Avoid repeated obvious words like 开关、开关.
    if re.search(r"(开关).{0,4}", t):
        return True
    return False


def clean_display_zh(raw: Any, fallback_source: str = "") -> str:
    """Use natural Chinese explanations. Poor keyword soup falls back to rule summary."""
    if raw is None or looks_like_raw_payload(raw):
        return rule_zh_for_text(fallback_source) if fallback_source else ""
    txt = clean_text(str(raw))
    if looks_like_raw_payload(txt) or len(txt) > 260 or looks_like_poor_zh_note(txt):
        return rule_zh_for_text(fallback_source) if fallback_source else ""
    return txt


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", str(s or "")))


ES_STOPWORDS = {"de", "del", "la", "las", "el", "los", "un", "una", "unos", "unas", "y", "e", "o", "u", "para", "por", "con", "en", "a", "al", "sin", "sobre", "entre", "hasta", "desde"}
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
    t = sanitize_unconfirmed_natural_wood_text(t, lang) if "sanitize_unconfirmed_natural_wood_text" in globals() else t
    t = improve_title_naturalness(t, lang) if "improve_title_naturalness" in globals() else t
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
    """Raw source bundle. V18.2 only uses this for the first fact-card pass and ES work.
    Multi-language title generation and body generation must use compressed_master_text()
    / body_context_text() instead, so old long copy is not sent repeatedly.
    """
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


def source_brief_light() -> str:
    """Small source supplement for ES only: no long old description."""
    return f"""
SKU: {st.session_state.get('sku','')}
EAN: {st.session_state.get('ean','')}
品牌: {st.session_state.get('brand','Alpinaluz')}
系列名: {st.session_state.get('series','')}
原始标题: {st.session_state.get('manual_title','')}
技术备注: {st.session_state.get('tech_notes','')}
SEO关键词: {st.session_state.get('seo_keywords','')}
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


def compact_fact_card_text() -> str:
    """Only the confirmed/high-value facts used after the fact-card step."""
    fc = st.session_state.get("fact_card", {}) or {}
    priority = [
        "product_type", "key_structure", "materials", "colors", "dimensions", "socket_or_led",
        "bulb_included", "power", "cct_or_dimming", "adjustability", "power_connection",
        "plug_cable", "switch_included", "switch_type", "indoor_outdoor", "style", "spaces",
        "core_selling_points", "must_keep_in_titles", "do_not_claim", "notes_for_copy",
    ]
    lines = []
    for k in priority:
        v = fc.get(k, "")
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v if str(x).strip())
        v = clean_text(str(v or ""))
        if v:
            lines.append(f"{k}: {v[:600]}")
    return "\n".join(lines)


def compressed_master_signature() -> str:
    raw = "||".join([
        compact_fact_card_text(),
        current_es_title() if "current_es_title" in globals() else "",
        st.session_state.get("confirmed_highlights", {}).get("ES", ""),
        st.session_state.get("confirmed_legacy_titles", {}).get("ES", ""),
        st.session_state.get("es_intent_include", ""),
        st.session_state.get("es_intent_exclude", ""),
        st.session_state.get("es_intent_demote", ""),
    ])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def compressed_master_text(refresh: bool = False) -> str:
    """Rule-built compressed master for multilingual titles/highlights.
    No raw old listing is included, which is the main V18.2 token reduction.
    """
    sig = compressed_master_signature()
    if (not refresh) and st.session_state.get("compressed_master_signature") == sig and st.session_state.get("compressed_master_cache"):
        return st.session_state["compressed_master_cache"]
    cc = current_core_concepts() if "current_core_concepts" in globals() else {"A": [], "B": [], "C": []}
    def names(tier):
        return "、".join(x[1] for x in cc.get(tier, [])) or "无"
    txt = f"""
压缩母版（V18.2.8，多国语言只传这个，不再传完整旧文案）：
品牌：{st.session_state.get('brand','Alpinaluz')}
SKU/EAN：{st.session_state.get('sku','')} / {st.session_state.get('ean','')}
ES已确认短标题：{current_es_title() if 'current_es_title' in globals() else st.session_state.get('selected_es_title','')}
ES已确认商品亮点：{st.session_state.get('confirmed_highlights', {}).get('ES', st.session_state.get('current_highlight::ES',''))}
ES传统标题参考：{st.session_state.get('confirmed_legacy_titles', {}).get('ES', st.session_state.get('current_legacy_title::ES',''))}

确认事实卡：
{compact_fact_card_text()}

ES人工意图记录：
{intent_ledger_text() if 'intent_ledger_text' in globals() else ''}

标题信息预算：
A级必须进短标题或亮点：{names('A')}
B级尽量保留，可放商品亮点：{names('B')}
C级降级到五点/描述：{names('C')}

硬规则：
- 禁止 halogen/halógena/halogène、incandescent/incandescente、Edison、traditional/tradicional、standard bulb。
- 灯泡兼容只写 LED + 灯头 + 最大功率 + 灯泡不包含。
- 不确认的信息不写。
- 木材表达：Alpinaluz 默认不要过度纠结天然木；除非资料明确写 MDF、仿木、热转印木纹、wood effect、efecto madera、imitation wood 等，否则可按 wood/madera/bois/legno/madeira/Holz 正常表达。
- 商品亮点建议写满95-115字符，不要只写70-80字符；优先承载材质、核心尺寸、调节、开关和场景；如果确认有开关，商品亮点必须出现本地化“开关/Schalter/switch/interrupteur”等表达。
""".strip()
    st.session_state["compressed_master_cache"] = txt
    st.session_state["compressed_master_signature"] = sig
    return txt


def body_context_text(lang: str) -> str:
    """Context for body generation. V18.2: no raw source_brief(), only confirmed facts and intent."""
    es_listing = st.session_state.get("listings", {}).get("ES", {})
    es_ref = ""
    if lang != "ES" and isinstance(es_listing, dict) and es_listing:
        es_ref = "\n".join([
            "ES已生成正文参考（只保留卖点结构，不逐词翻译）：",
            "五点：" + json.dumps(es_listing.get("bullets", []), ensure_ascii=False)[:1200],
            "描述摘要：" + clean_text(str(es_listing.get("description", "")))[:900],
            "Search Terms：" + clean_text(str(es_listing.get("search_terms", "")))[:250],
        ])
    return f"""
确认事实卡：
{compact_fact_card_text()}

压缩母版：
{compressed_master_text()}

已确认短标题：{st.session_state.get('confirmed_titles', {}).get(lang, '')}
已确认商品亮点：{st.session_state.get('confirmed_highlights', {}).get(lang, '')}
传统长标题参考：{st.session_state.get('confirmed_legacy_titles', {}).get(lang, '')}

ES人工意图记录：
{intent_ledger_text() if 'intent_ledger_text' in globals() else ''}

{es_ref}
""".strip()


def title_rules_compact(lang: str) -> str:
    local = {
        "ES": "西班牙语自然标题，重要名词可首字母大写。",
        "FR": "法语自然表达，使用 applique murale/suspension 等本地词。",
        "DE": "德语名词大写，复合词自然，不要夹外语。",
        "IT": "意大利语自然表达，注意性数一致。",
        "NL": "荷兰语自然表达，不要夹英语。",
        "PL": "波兰语自然表达，不要夹英语/西语。",
        "PT": "葡萄牙站自然表达，使用 candeeiro/aplique/casquilho。",
        "SE": "瑞典语自然表达，不要夹英语。",
        "EN": "英国英语自然 Title Case。",
    }
    return f"""
- Alpinaluz 必须第一位。
- 语言：{LANGS[lang]['native']}；站点：{LANGS[lang]['market']}。{local.get(lang, '')}
- 短标题≤75字符：品牌 + 产品类型 + 1-2个最高价值规格。
- 商品亮点≤125字符，目标95-115字符：用逗号短语补充材质、核心尺寸/底座、调节角度、开关、用途、IP、调光、插头线、上下出光等。
- 传统标题≤200字符：仅参考，不作为主标题。
- 不写中文/SKU；不写灯泡不含、安装简单等低价值售后词进短标题。
- 单灯产品不要突出 1 foco / 1 luz / 1 light 等数量词；多灯产品保留数量。
- 禁止卤素/白炽/Edison/traditional/standard bulb 等词。
""".strip()


# ------------------------- fact card Chinese helper -------------------------
FACT_USAGE = {
    "product_type": "标题必用：决定类目词，必须确认。",
    "series_name": "不进标题：通常是系列/SKU/内部型号，默认不要写入标题。",
    "key_structure": "标题必用/五点必用：决定产品核心结构和主卖点。",
    "materials": "标题可用：主材质可进标题，细节材质放五点。",
    "colors": "标题可用：主色必须准确，木色不强制细分。",
    "dimensions": "标题可用：核心尺寸可进标题，全部尺寸放五点/描述。",
    "socket_or_led": "标题必用：灯头或LED集成信息不能错。",
    "bulb_included": "五点/描述用：必须说明灯泡是否包含，但一般不进标题。",
    "power": "五点/描述用：功率和最大瓦数一般不进标题。",
    "cct_or_dimming": "标题可用：若是CCT/调光/遥控等核心功能可进标题。",
    "adjustability": "标题可用：高度可调/角度可调等核心功能可进标题。",
    "installation": "五点/描述用：安装方式一般不进标题。",
    "power_connection": "标题必用/五点必用：壁灯带插头线或直接接线要准确，决定购买场景。",
    "plug_cable": "标题必用（若确认有）：壁灯带插头线是核心卖点；未确认则不要写有/没有。",
    "switch_included": "标题可用/五点必用（若确认有）：只在确认有开关时写；未确认不要写。",
    "switch_type": "标题可用：线控、底座、触摸、脚踏等位置必须准确；未确认不写。",
    "cable_length": "五点/描述用：只有资料确认时才写具体长度，不要猜。",
    "plug_type": "五点/描述用：只有确认有 EU 插头/USB 等才写。",
    "indoor_outdoor": "五点/描述用：IP/室内外信息通常放正文。",
    "style": "标题可用：风格词可保留1-2个，不要堆太多。",
    "spaces": "标题可用：保留1-2个核心场景即可。",
    "core_selling_points": "生成文案用：用于五点、描述和A+。",
    "must_keep_in_titles": "标题必用：AI认为标题应保留的信息，需人工检查是否过多。",
    "do_not_claim": "禁止宣称：必须检查，避免写不存在功能。",
    "notes_for_copy": "生成文案用：后续标题/五点/A+的注意事项。",
}

FACT_TRANSLATION_MAP = [
    ("lámpara colgante", "吊灯"), ("lampada a sospensione", "吊灯"), ("suspension", "吊灯"), ("pendelleuchte", "吊灯"), ("pendant light", "吊灯"),
    ("lámpara de pie", "落地灯"), ("stehlampe", "落地灯"), ("lampadaire", "落地灯"), ("floor lamp", "落地灯"), ("lampada da terra", "落地灯"), ("candeeiro de pé", "落地灯"), ("vloerlamp", "落地灯"), ("golvlampa", "落地灯"),
    ("aplique de pared", "壁灯"), ("wall light", "壁灯"), ("wandleuchte", "壁灯"), ("applique murale", "壁灯"), ("applique da parete", "壁灯"), ("candeeiro de parede", "壁灯"), ("wandlamp", "壁灯"),
    ("madera natural", "天然木"), ("natural wood", "天然木"), ("naturholz", "天然木"), ("bois naturel", "天然木"), ("legno naturale", "天然木"), ("madeira natural", "天然木"), ("drewno naturalne", "天然木"), ("naturträ", "天然木"),
    ("metal negro", "黑色金属"), ("black metal", "黑色金属"), ("metallo nero", "黑色金属"), ("métal noir", "黑色金属"), ("metal preto", "黑色金属"), ("schwarzem metall", "黑色金属"),
    ("blanco", "白色"), ("white", "白色"), ("bianco", "白色"), ("branco", "白色"), ("weiß", "白色"), ("wit", "白色"), ("vit", "白色"),
    ("pantalla", "灯罩"), ("shade", "灯罩"), ("schirm", "灯罩"), ("abat-jour", "灯罩"), ("paralume", "灯罩"), ("cúpula", "灯罩"), ("klosz", "灯罩"), ("skärm", "灯罩"),
    ("jaula", "笼形"), ("cage", "笼形"), ("gabbia", "笼形"), ("käfig", "笼形"), ("gaiola", "笼形"), ("klatk", "笼形"),
    ("altura regulable", "高度可调"), ("adjustable height", "高度可调"), ("höhenverstell", "高度可调"), ("altezza regolabile", "高度可调"), ("hauteur réglable", "高度可调"), ("altura regulável", "高度可调"), ("verstelbare hoogte", "高度可调"),
    ("casquillo", "灯头"), ("socket", "灯头"), ("fassung", "灯头"), ("douille", "灯头"), ("attacco", "灯头"), ("casquilho", "灯头"), ("fitting", "灯头"), ("sockel", "灯座"),
    ("bombilla no incluida", "灯泡不含"), ("bulb not included", "灯泡不含"), ("ampoule non incluse", "灯泡不含"), ("lampadina non inclusa", "灯泡不含"), ("lâmpada não incluída", "灯泡不含"), ("leuchtmittel nicht enthalten", "灯泡不含"),

    ("con cable y enchufe", "带电源线和插头"), ("cable y enchufe", "带电源线和插头"), ("plug in", "插头线供电"), ("plug-in", "插头线供电"), ("with plug", "带插头"), ("enchufe", "插头"), ("stecker", "插头"), ("prise", "插头"), ("spina", "插头"), ("ficha", "插头"),
    ("interruptor en cable", "线控开关"), ("interruptor integrado", "集成开关"), ("interrupteur", "开关"), ("switch", "开关"), ("schalter", "开关"), ("interruttore", "开关"), ("schakelaar", "开关"), ("strömbrytare", "开关"), ("włącznik", "开关"),
    ("conexión directa", "直接接线"), ("hardwired", "硬接线"), ("raccordement filaire", "硬接线"), ("festem kabelanschluss", "硬接线"),
    ("interior", "室内"), ("indoor", "室内"), ("innen", "室内"), ("interno", "室内"), ("intérieur", "室内"),
    ("exterior cubierto", "有遮蔽户外"), ("extérieur couvert", "有遮蔽户外"), ("covered outdoor", "有遮蔽户外"), ("geschützte außen", "有遮蔽户外"), ("überdacht", "有遮蔽户外"), ("esterni coperti", "有遮蔽户外"), ("exterior coberto", "有遮蔽户外"), ("overdekte buiten", "有遮蔽户外"), ("pod zadaszeniem", "有遮蔽户外"), ("skyddad utomhus", "有遮蔽户外"), ("balcón", "阳台"), ("balcon", "阳台"), ("balkon", "阳台"), ("terrasse", "露台"), ("terraza", "露台"), ("terrazza", "露台"), ("terraço", "露台"), ("terras", "露台"), ("patio", "庭院"), ("uteplats", "庭院"),
    ("cocina", "厨房"), ("kitchen", "厨房"), ("cuisine", "厨房"), ("cucina", "厨房"), ("cozinha", "厨房"), ("küche", "厨房"), ("keuken", "厨房"),
    ("comedor", "餐厅"), ("dining", "餐厅"), ("sala da pranzo", "餐厅"), ("sala de jantar", "餐厅"), ("esszimmer", "餐厅"), ("eetkamer", "餐厅"),
    ("salón", "客厅"), ("living room", "客厅"), ("salon", "客厅"), ("soggiorno", "客厅"), ("woonkamer", "客厅"), ("wohnzimmer", "客厅"),
    ("dormitorio", "卧室"), ("bedroom", "卧室"), ("chambre", "卧室"), ("camera", "卧室"), ("quarto", "卧室"), ("schlafzimmer", "卧室"), ("slaapkamer", "卧室"),
    ("nórdico", "北欧风"), ("nordic", "北欧风"), ("scandinav", "斯堪的纳维亚风"), ("skandinav", "斯堪的纳维亚风"), ("industrial", "工业风"), ("minimal", "极简风"),
]


NATURAL_WOOD_TERMS = [
    "madera natural", "natural wood", "bois naturel", "legno naturale", "madeira natural", "naturholz",
    "naturalne drewno", "natuurlijk hout", "naturträ", "naturtra", "天然木", "原木", "实木", "madera maciza", "solid wood"
]

WOOD_GENERIC_TERMS = ["madera", "wood", "bois", "legno", "madeira", "holz", "hout", "drewno", "trä", "tra", "木"]


def natural_wood_confirmed() -> bool:
    """Strict confirmation only from human-provided fields.
    Important: AI-generated fact card text is NOT accepted as confirmation, because it may infer
    "natural wood" from old copy. To allow natural wood wording, the operator must write an explicit
    confirmation in 技术备注 / 手动标题 / 手动长描述, for example:
    天然木确认 / 原木确认 / natural wood confirmed / madera natural confirmada.
    """
    blob = " ".join([
        str(st.session_state.get("tech_notes", "")),
        str(st.session_state.get("manual_title", "")),
        str(st.session_state.get("manual_description", "")),
    ]).lower()
    explicit_patterns = [
        r"(?:天然木|原木|实木).{0,12}(?:确认|已确认|confirm)",
        r"(?:确认|已确认|confirm).{0,12}(?:天然木|原木|实木)",
        r"(?:natural wood|solid wood).{0,18}(?:confirmed|confirmado|confirmada|confermat|confirmé|confirme|bestätigt|bevestigd|potwierd)",
        r"(?:confirmed|confirmado|confirmada|confermat|confirmé|confirme|bestätigt|bevestigd|potwierd).{0,18}(?:natural wood|solid wood)",
        r"madera natural.{0,18}(?:confirmada|confirmado)",
        r"(?:confirmada|confirmado).{0,18}madera natural",
        r"bois naturel.{0,18}(?:confirmé|confirme)",
        r"legno naturale.{0,18}(?:confermato|confermata)",
        r"madeira natural.{0,18}(?:confirmada|confirmado)",
        r"naturholz.{0,18}(?:bestätigt|bestaetigt)",
        r"naturalne drewno.{0,18}(?:potwierdzone|potwierdzono)",
        r"natuurlijk hout.{0,18}(?:bevestigd)",
        r"naturträ.{0,18}(?:bekräftat|bekraftat|bekräftad|bekraftad)",
    ]
    return any(re.search(pat, blob, flags=re.I) for pat in explicit_patterns)

def product_has_wood_reference() -> bool:
    fc = st.session_state.get("fact_card", {}) or {}
    blob = " ".join([
        str(fc.get("materials", "")), str(fc.get("colors", "")), str(fc.get("key_structure", "")),
        str(fc.get("core_selling_points", "")), str(fc.get("must_keep_in_titles", "")), str(fc.get("notes_for_copy", "")),
        str(st.session_state.get("tech_notes", "")), str(st.session_state.get("manual_title", "")),
    ]).lower()
    return any(term.lower() in blob for term in WOOD_GENERIC_TERMS + NATURAL_WOOD_TERMS)

def wood_effect_or_mdf_confirmed() -> bool:
    """Only downgrade wood wording when the input explicitly says MDF / imitation / wood-effect / thermal-transfer etc.
    For Alpinaluz, ordinary wood wording should not be over-policed.
    """
    fc = st.session_state.get("fact_card", {}) or {}
    blob = " ".join([
        str(fc.get("materials", "")), str(fc.get("colors", "")), str(fc.get("key_structure", "")),
        str(fc.get("core_selling_points", "")), str(fc.get("must_keep_in_titles", "")), str(fc.get("notes_for_copy", "")),
        str(st.session_state.get("tech_notes", "")), str(st.session_state.get("manual_title", "")),
        str(st.session_state.get("manual_description", "")),
    ]).lower()
    terms = [
        "mdf", "wood effect", "wood-effect", "imitation wood", "faux wood", "madera efecto", "efecto madera",
        "imitación madera", "imitacion madera", "bois effet", "effet bois", "holzoptik", "effetto legno",
        "efeito madeira", "houtlook", "efekt drewna", "trälook", "traelook", "热转印", "热转印木纹", "仿木", "木纹效果", "贴皮"
    ]
    return any(t in blob for t in terms)


def sanitize_unconfirmed_natural_wood_text(text: str, lang: str = "") -> str:
    """Hard post-process: never upgrade generic wood to natural/solid wood unless explicitly confirmed."""
    if not text:
        return ""
    t = str(text)
    if natural_wood_confirmed() or not wood_effect_or_mdf_confirmed():
        return clean_text(t)

    # Only when MDF/wood-effect/imitation is explicitly confirmed, downgrade natural wood wording.
    # Phrase-level replacements first. Keep a usable local expression such as "wood front" / "façade bois".
    replacements = [
        # ES
        (r"\bfrontal\s+de\s+madera\s+natural\b", "frontal de madera"),
        (r"\bmadera\s+natural\b", "madera"),
        # EN
        (r"\bfront\s+panel\s+in\s+natural\s+wood\b", "wood front panel"),
        (r"\bnatural\s+wood\s+front\s+panel\b", "wood front panel"),
        (r"\bnatural\s+wood\s+front\b", "wood front"),
        (r"\bwith\s+natural\s+wood\b", "with wood front"),
        (r"\bnatural\s+wood\b", "wood"),
        # FR
        (r"\bfa[cç]ade\s+en\s+bois\s+naturel\b", "façade bois"),
        (r"\bfront\s+en\s+bois\s+naturel\b", "front en bois"),
        (r"\bavec\s+bois\s+naturel\b", "avec bois"),
        (r"\bbois\s+naturel\b", "bois"),
        # IT
        (r"\bfrontale\s+in\s+legno\s+naturale\b", "frontale in legno"),
        (r"\bcon\s+legno\s+naturale\b", "con legno"),
        (r"\blegno\s+naturale\b", "legno"),
        # PT
        (r"\bfrente\s+em\s+madeira\s+natural\b", "frente em madeira"),
        (r"\bcom\s+madeira\s+natural\b", "com madeira"),
        (r"\bmadeira\s+natural\b", "madeira"),
        # DE
        (r"\bFront\s+aus\s+Naturholz\b", "Holzfront"),
        (r"\bmit\s+Naturholz\b", "mit Holzfront"),
        (r"\bNaturholzfront\b", "Holzfront"),
        (r"\bNaturholz\b", "Holz"),
        # PL
        (r"\bfrontem\s+z\s+naturalnego\s+drewna\b", "drewnianym frontem"),
        (r"\bz\s+naturalnym\s+drewnem\b", "z drewnianym frontem"),
        (r"\bnaturalne\s+drewno\b", "drewno"),
        (r"\bnaturalnego\s+drewna\b", "drewna"),
        (r"\bnaturalnym\s+drewnem\b", "drewnianym frontem"),
        # NL
        (r"\bfront\s+van\s+natuurlijk\s+hout\b", "houtfront"),
        (r"\bmet\s+natuurlijk\s+hout\b", "met houtfront"),
        (r"\bnatuurlijk\s+hout\b", "hout"),
        # SE
        (r"\bfront\s+i\s+naturtr[äa]\b", "träfront"),
        (r"\bmed\s+naturtr[äa]\b", "med träfront"),
        (r"\bnaturtr[äa]\b", "trä"),
    ]
    for pat, repl in replacements:
        t = re.sub(pat, repl, t, flags=re.I)
    # Additional broad cleanups for comma-separated Amazon titles and marketplace copy.
    broad = [
        (r"\bNatural\s+Wood\b", "wood front"),
        (r"\bMadera\s+Natural\b", "madera"),
        (r"\bBois\s+Naturel\b", "bois"),
        (r"\bLegno\s+Naturale\b", "legno"),
        (r"\bMadeira\s+Natural\b", "madeira"),
        (r"\bNaturholz\b", "Holzfront"),
        (r"\bNatuurlijk\s+Hout\b", "houtfront"),
        (r"\bNaturalne\s+Drewno\b", "drewniany front"),
        (r"\bnaturalnym\s+drewnem\b", "drewnianym frontem"),
        (r"\bNaturtr[äa]\b", "träfront"),
    ]
    for pat, repl in broad:
        t = re.sub(pat, repl, t, flags=re.I)
    return clean_text(t)

def improve_title_naturalness(title: str, lang: str = "") -> str:
    """Deterministic fixes for titles that look like keyword piles or repeat prepositions."""
    t = clean_text(title)
    if not t:
        return t
    if lang == "EN":
        t = re.sub(r"\bWhite\s+Wood\s+Adjustable\s+With\s+Switch\b", "White with Wood Front and Switch", t, flags=re.I)
        t = re.sub(r"\bWhite\s+Natural\s+Wood\s+Adjustable\s+With\s+Switch\b", "White with Wood Front and Switch", t, flags=re.I)
        t = re.sub(r"\bWhite\s+with\s+Wood\s+and\s+Switch\b", "White with Wood Front and Switch", t, flags=re.I)
        t = re.sub(r"\bWhite\s+with\s+Wood\s+Front\s+and\s+Switch\b", "White with Wood Front and Switch", t, flags=re.I)
        t = re.sub(r"\bWith\b", "with", t)
    elif lang == "FR":
        t = re.sub(r"\bBlanche\s+Bois(?:\s+Naturel)?\s+Orientable\s+Interrupteur\b", "Blanche Orientable avec Bois et Interrupteur", t, flags=re.I)
        t = re.sub(r"\bOrientable\s+Interrupteur\b", "Orientable avec Interrupteur", t, flags=re.I)
        t = re.sub(r"\bBlanche\s+Bois\b", "Blanche avec Bois", t, flags=re.I)
        t = re.sub(r"\bavec\s+Bois\s+avec\s+Interrupteur\b", "avec Bois et Interrupteur", t, flags=re.I)
        t = re.sub(r"\bavec\s+Fa[cç]ade\s+Bois\s+avec\s+Interrupteur\b", "avec Façade Bois et Interrupteur", t, flags=re.I)
    elif lang == "IT":
        t = re.sub(r"\bBianca\s+Legno(?:\s+Naturale)?\s+con\s+Interruttore\b", "Bianca con Legno e Interruttore", t, flags=re.I)
        t = re.sub(r"\bBianca\s+Legno\b", "Bianca con Legno", t, flags=re.I)
        t = re.sub(r"\bcon\s+Legno\s+con\s+Interruttore\b", "con Legno e Interruttore", t, flags=re.I)
    elif lang == "PT":
        t = re.sub(r"\bBranco\s+Madeira(?:\s+Natural)?\s+Orientável\s+com\s+Interruptor\b", "Branco com Madeira Orientável e Interruptor", t, flags=re.I)
        t = re.sub(r"\bBranco\s+Madeira\b", "Branco com Madeira", t, flags=re.I)
        t = re.sub(r"\bcom\s+Madeira\s+com\s+Interruptor\b", "com Madeira e Interruptor", t, flags=re.I)
    elif lang == "PL":
        t = re.sub(r"\bBiały\s+Naturalne\s+Drewno\s+Regulowany\s+z\s+Włącznikiem\b", "Biały z Drewnianym Frontem i Włącznikiem", t, flags=re.I)
        t = re.sub(r"\bBiały\s+Drewno\s+Regulowany\s+z\s+Włącznikiem\b", "Biały z Drewnianym Frontem i Włącznikiem", t, flags=re.I)
        t = re.sub(r"\bBiały\s+Naturalne\s+Drewno\b", "Biały z Drewnianym Frontem", t, flags=re.I)
        t = re.sub(r"\bbiały\s+z\s+drewno\b", "biały z drewnianym frontem", t, flags=re.I)
    elif lang == "NL":
        t = re.sub(r"\bWit\s+Natuurlijk\s+Hout\s+Verstelbaar\s+met\s+Schakelaar\b", "Wit met Houtfront en Schakelaar", t, flags=re.I)
        t = re.sub(r"\bWit\s+Hout\s+Verstelbaar\s+met\s+Schakelaar\b", "Wit met Houtfront en Schakelaar", t, flags=re.I)
        t = re.sub(r"\bWit\s+met\s+Hout\s+en\s+Schakelaar\b", "Wit met Houtfront en Schakelaar", t, flags=re.I)
    elif lang == "DE":
        t = re.sub(r"\bWeiß\s+Naturholz\s+schwenkbar\s+mit\s+Schalter\b", "Weiß mit Holzfront und Schalter", t, flags=re.I)
        t = re.sub(r"\bWeiß\s+Holz\s+schwenkbar\s+mit\s+Schalter\b", "Weiß mit Holzfront und Schalter", t, flags=re.I)
        t = re.sub(r"\bWeiß\s+mit\s+Holz\s+und\s+Schalter\b", "Weiß mit Holzfront und Schalter", t, flags=re.I)
    elif lang == "ES":
        t = re.sub(r"\bMadera\s+e\s+Interruptor\b", "Madera e Interruptor", t)
    # Generic cleanup for duplicate connector patterns created by sanitization.
    t = re.sub(r"\bavec\s+([^,]{2,45}?)\s+avec\s+", r"avec \1 et ", t, flags=re.I)
    t = re.sub(r"\bcom\s+([^,]{2,45}?)\s+com\s+", r"com \1 e ", t, flags=re.I)
    # Make comma-pile titles more natural and remove repeated feature words.
    t = re.sub(r",\s*(?:Wood Front|wood front)\s*,", ", wood front,", t, flags=re.I)
    if lang == "EN":
        t = re.sub(r"White,\s*wood front,\s*with Switch", "White with wood front and switch", t, flags=re.I)
        t = re.sub(r"White\s+with\s+wood front\s+and\s+Switch", "White with Wood Front and Switch", t, flags=re.I)
    elif lang == "ES":
        t = re.sub(r"con\s+Madera\s+Orientable\s+e\s+Interruptor", "con Frontal de Madera e Interruptor", t, flags=re.I)
        t = re.sub(r",\s*Madera,", ", Frontal de Madera,", t, flags=re.I)
    elif lang == "FR":
        t = re.sub(r"Blanche,\s*Bois,\s*350", "Blanche avec Bois, 350", t, flags=re.I)
        t = re.sub(r"Blanche\s+avec\s+Bois\s+et\s+Interrupteur", "Blanche avec Bois et Interrupteur", t, flags=re.I)
    elif lang == "PT":
        t = re.sub(r"Branco,\s*Madeira,", "Branco com Madeira,", t, flags=re.I)
        t = re.sub(r"com\s+Madeira\s+e\s+Interruptor", "com Madeira e Interruptor", t, flags=re.I)
    elif lang == "DE":
        t = re.sub(r"Weiß,\s*Holzfront,\s*Schalter", "Weiß mit Holzfront und Schalter", t, flags=re.I)
    elif lang == "PL":
        t = re.sub(r"biały,\s*drewniany front,\s*włącznik", "biały z drewnianym frontem i włącznikiem", t, flags=re.I)
    elif lang == "NL":
        t = re.sub(r"Wit,\s*houtfront,\s*schakelaar", "Wit met houtfront en schakelaar", t, flags=re.I)
    elif lang == "SE":
        t = re.sub(r"vit,\s*träfront,\s*strömbrytare", "vit med träfront och strömbrytare", t, flags=re.I)
    t = re.sub(r"\s*,\s*,+", ", ", t)
    return clean_text(t)

def rule_zh_for_text(text: str, fallback: str = "") -> str:
    """Free, natural Chinese hint for candidate cards and省token导出. No GPT call.
    The goal is a short sentence, not a debug keyword list.
    """
    src = clean_text(text)
    if not src:
        return fallback or "中文解释未生成"
    low = src.lower()
    product = ""
    if any(x in low for x in ["wall light", "wall lamp", "applique", "wandlamp", "wandleuchte", "kinkiet", "vägglampa", "vagglampa", "aplique"]):
        product = "壁灯"
    elif any(x in low for x in ["pendant", "suspension", "colgante", "pendelleuchte"]):
        product = "吊灯"
    elif any(x in low for x in ["floor lamp", "lámpara de pie", "stehlampe"]):
        product = "落地灯"
    specs = []
    for tok in ["GU10", "E27", "G9", "E14", "LED"]:
        if tok.lower() in low:
            specs.append(tok); break
    if any(x in low for x in ["white", "blanco", "blanche", "bianca", "branco", "weiß", "weiss", "wit", "biały", "bialy", "vit"]):
        specs.append("白色")
    if any(x in low for x in ["wood front", "frontal de madera", "façade bois", "facade bois", "frontale in legno", "frente em madeira", "holzfront", "drewnianym frontem", "houtfront", "träfront", "madera", "wood", "bois", "legno", "madeira", "holz", "drewno", "hout", "trä"]):
        specs.append("木质前板")
    material = []
    if any(x in low for x in ["steel", "acero", "acier", "acciaio", "aço", "aco", "stahl", "stal", "stål", "staal"]):
        material.append("钢")
    if any(x in low for x in ["aluminium", "aluminio", "alumínio", "alumin"]):
        material.append("铝")
    features = []
    if "350" in low:
        features.append("灯头约350°可调")
    if any(x in low for x in ["switch", "interrup", "schalter", "włącz", "wlacz", "schakel", "strömbryt", "strombryt"]):
        features.append("带开关")
    dims = []
    for m in re.findall(r"Ø?\d+(?:[,.]\d+)?\s*(?:x|×)\s*Ø?\d+(?:[,.]\d+)?\s*cm|Ø\s*\d+(?:[,.]\d+)?\s*cm", src, flags=re.I):
        d = clean_text(m)
        if d and d not in dims:
            dims.append(d)
    scenes = []
    if any(x in low for x in ["bed", "bedside", "cabecero", "chevet", "testiera", "cabeceira", "bett", "łóż", "lozko", "säng", "sang"]): scenes.append("床头")
    if any(x in low for x in ["reading", "lectura", "lecture", "lettura", "leitura", "lesen", "lezen", "czyt", "läs", "las"]): scenes.append("阅读")
    if any(x in low for x in ["living", "salón", "salon", "soggiorno", "sala", "wohnzimmer", "woonkamer", "vardagsrum", "sofa"]): scenes.append("客厅/沙发旁")
    bits=[]
    if product:
        bits.append(product)
    if specs:
        bits.append("、".join(dict.fromkeys(specs)))
    if material:
        bits.append("材质含"+"、".join(dict.fromkeys(material)))
    if features:
        bits.append("，".join(dict.fromkeys(features)))
    if dims:
        bits.append("尺寸约"+"、".join(dims[:2]))
    if scenes:
        bits.append("适合"+"、".join(dict.fromkeys(scenes)))
    if not bits:
        return fallback or "中文解释未生成"
    sentence = "，".join(bits)
    sentence = re.sub(r"，+", "，", sentence).strip("，")
    return sentence + "。"

def fact_value_zh_hint(value: Any) -> str:
    text = clean_text(", ".join(str(x) for x in value) if isinstance(value, list) else str(value or ""))
    if not text:
        return "暂无"
    # If AI already returned a Chinese part, prefer it.
    m = re.search(r"中文[:：]\s*([^;；\n]+)", text)
    if m:
        return clean_text(m.group(1))
    found = []
    low = text.lower()
    for src, zh in FACT_TRANSLATION_MAP:
        if src.lower() in low and zh not in found:
            found.append(zh)
    # Preserve key technical tokens and sizes.
    for token in re.findall(r"Ø?\d+(?:[.,]\d+)?\s*(?:cm|mm)|\b(?:E27|E14|G9|GU10|LED|CCT|IP\d{2}|\d+W|\d+xE27|\d+\s*x\s*E27)\b", text, flags=re.I):
        tok = token.upper().replace("CM", "cm").replace("MM", "mm")
        if tok not in found:
            found.append(tok)
    return "、".join(found[:10]) if found else "请人工确认：AI未能本地翻译此字段"

def fact_summary_zh() -> str:
    fc = st.session_state.get("fact_card", {}) or {}
    parts = []
    for k in ["product_type", "key_structure", "materials", "colors", "dimensions", "socket_or_led", "power_connection", "plug_cable", "switch_included", "switch_type", "adjustability", "bulb_included", "spaces"]:
        hint = fact_value_zh_hint(fc.get(k, ""))
        if hint and hint not in {"暂无", "请人工确认：AI未能本地翻译此字段"}:
            parts.append(hint)
    # de-duplicate fragments while keeping order
    seen, out = set(), []
    for p in parts:
        for chunk in re.split(r"[、,，;；]", p):
            chunk = clean_text(chunk)
            if chunk and chunk not in seen:
                seen.add(chunk); out.append(chunk)
    if not out:
        return "事实卡已生成，但中文速览不足，请重点检查产品类型、灯头、尺寸、材质、颜色和是否含灯泡。"
    return "；".join(out[:18])

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
- product_type: 产品类型，例如吊灯/壁灯/落地灯/台灯/吸顶灯等；
- series_name: 系列名/型号名，不一定进标题；
- key_structure: 产品核心结构，比如三头吊灯、圆柱射灯、玻璃球壁灯等；
- materials/colors/dimensions/socket_or_led: 核心事实；
- bulb_included: 灯泡是否包含。允许写“灯泡不包含”这种售后关键事实；
- power_connection: 供电方式。只能在确认时写：直接接线 / 带插头线 / USB / 电池 / 太阳能 / 未确认；
- plug_cable: 是否带插头线。写“已确认有 / 已确认无 / 未确认”，并说明证据。壁灯带插头线是核心卖点；
- switch_included: 是否带开关。写“已确认有 / 已确认无 / 未确认”，不要把没看到开关等同于没有；
- switch_type: 开关类型/位置：线控开关、底座开关、灯体开关、脚踏开关、触摸开关、墙壁开关控制、未确认；
- cable_length/plug_type: 只有资料明确时才写，不要猜；
- core_selling_points: 5-8个关键卖点；
- must_keep_in_titles: 标题必须尽量保留的信息，不要太多；
- do_not_claim: 只写需要防止 AI 误写的约束，例如“不要写内置LED/不要写遥控/不要写户外”。未知信息不要写成否定事实；
- notes_for_copy: 后续写文案注意事项。

重要规则：
1. JSON 字段值里只放“事实内容”，不要加入“中文：...”这种注释。中文解释由界面单独生成。
2. 不确定 = 未确认。未确认的信息后续不写有，也不写没有。
3. 已确认没有的功能主要用于防止 AI 误写，不默认写进 Listing，除非人工备注要求说明。
4. 只写已确认的正向事实；不要列负面清单。
5. 灯泡兼容必须保守：只允许 LED + 灯头型号 + 最大功率 + 灯泡不包含。禁止出现 halogen/halógena/halogène、incandescent/incandescente、Edison、traditional/tradicional、standard bulb 等高风险灯泡词。
6. 如果旧文案含有高风险灯泡词，只用于理解旧资料，不要输出到事实卡。

资料：
{source_brief()}
"""


def title_rules(lang: str) -> str:
    common = f"""
标题规则：
- 品牌 Alpinaluz 必须第一位。
- 标题要像 {LANGS[lang]['market']} 上可成交的专业标题，不要碎词拼接。
- 保留高价值事实：产品类型、核心结构、核心材质/颜色、关键尺寸、灯头/LED、风格、核心使用场景。
- 不要把低价值售后/说明塞进标题：bombilla no incluida / bulbs not included / easy installation / incluye accesorios 等。
- 平台安全硬规则：标题绝对禁止出现 halogen/halógena/halogène、incandescent/incandescente、Edison、traditional/tradicional、standard bulb 等灯泡类型词。灯泡兼容只写灯头型号，例如 E27/GU10/G9。
- 不允许中文，不允许 SKU，不允许无具体数字的裸 cm；但 75 cm、Ø20 cm、43 x 5,1 x 2,7 cm 这类前面有数字的写法是允许的。
- 单灯/单头产品：标题不要突出 1 foco / 1 luz / 1 spot / 1 light / 1-flammig / 1 luce 等数量词，除非用户明确要求；直接写 wall light / aplique / Wandleuchte + 灯头即可。
- 多灯/多头产品：2灯以上必须保留数量，例如 3 luces / 3 lights / 3-flammig / 3x E27。
- 如果 ES 最终标题中已经人工删除某个低价值词，多国语言不要把它重新加回来。
- V18 新规模式：短标题必须控制在 75 字符以内（含空格），理想目标 68-72 字符，避免卡到 75/75。
- 短标题只放：品牌 + 产品类型 + 1-2 个最高价值规格/属性。不要为了SEO把所有词塞进标题。
- 商品亮点 Item Highlights 必须控制在 125 字符以内，目标 95-115 字符；用逗号短语补充材质、核心尺寸/底座、调节角度、开关、用途、IP、防水/遮蔽户外、插头线等标题放不下的信息。
- 传统长标题也要生成一个 200 字符以内版本，仅作历史兼容参考，不作为新规主标题。
- 如果信息太多，按 A/B/C 三级取舍：A级进短标题；B级进商品亮点；C级放到五点/描述。
- 短标题和商品亮点尽量不要重复同一个关键词；同一事实不要机械重复，商品亮点要优先补足“材质 + 关键尺寸/结构 + 功能 + 使用场景”。
- 短标题不能为了压缩删除必要介词或连接词，必须保持本地语言自然语法，尤其是 FR/IT/PT/PL/NL/DE。
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

ES轻量资料补充（只限ES阶段使用）：
{source_brief_light()}

输出 JSON 数组，每个元素只保留这些字段，避免浪费 output token：
{{"title":"75字符以内西班牙短标题", "zh":"标题中文审核说明：简洁但完整，说明产品类型、关键规格/材质/灯头/风险点", "highlight":"95-115字符最佳、125字符以内商品亮点", "highlight_zh":"商品亮点中文审核说明：说明亮点主打什么、包含哪些关键参数、是否漏核心卖点", "risk_code":"ok / too_long / grammar_check / missing_core / material_risk"}}
必须输出 zh 和 highlight_zh。中文解释要精简但完整，不强制字数，不要关键词堆叠，不要重复词，不要漏产品类型/材质/灯头/尺寸/风险判断等关键审核点。只输出 JSON。
"""


def lang_title_prompt(lang: str, instruction: str = "") -> str:
    es_title = st.session_state.get("confirmed_titles", {}).get("ES", "") or st.session_state.get("selected_es_title", "")
    return f"""请为 {LANGS[lang]['market']} 生成 3 个本地语言标题候选，语言必须是 {LANGS[lang]['native']}。

V18.2.8压缩输入模式：只使用压缩母版 + ES人工意图 + 事实卡，不再重复传完整旧文案。

本国语言规则：
{title_rules_compact(lang)}

标题信息预算和继承：
{title_budget_text()}
{must_inherit_text_for_prompt()}

用户本轮中文修改要求：{instruction or '首次生成，请给出3个高质量本地标题'}

最终 ES 标题：
{es_title}

压缩母版：
{compressed_master_text()}

输出 JSON 数组，每个元素只保留这些字段，避免浪费 output token：
{{"title":"75字符以内{LANGS[lang]['native']}短标题", "zh":"标题中文审核说明：简洁但完整，说明产品类型、关键规格/材质/灯头/风险点", "highlight":"95-115字符最佳、125字符以内商品亮点", "highlight_zh":"商品亮点中文审核说明：说明亮点主打什么、包含哪些关键参数、是否漏核心卖点", "risk_code":"ok / too_long / grammar_check / missing_core / material_risk"}}
必须输出 zh 和 highlight_zh。中文解释要精简但完整，不强制字数，不要关键词堆叠，不要重复词，不要漏产品类型/材质/灯头/尺寸/风险判断等关键审核点。只输出 JSON。
"""


def batch_lang_title_prompt(langs: List[str]) -> str:
    es_title = st.session_state.get("confirmed_titles", {}).get("ES", "") or st.session_state.get("selected_es_title", "")
    lang_rules = "\n".join([f"{l}: {title_rules_compact(l)}" for l in langs])
    schema = {l: [{"title": f"75字符以内{LANGS[l]['native']}短标题", "zh": "标题中文审核说明，精简但完整", "highlight": "95-115字符最佳、125字符以内商品亮点", "highlight_zh": "商品亮点中文审核说明，精简但完整", "risk_code": "ok / too_long / grammar_check / missing_core / material_risk"}] for l in langs}
    return f"""请为多个 Amazon 国家站一次性生成首轮标题候选。每个国家生成 3 个标题候选。

V18.2.8压缩输入模式：本步骤只允许使用压缩母版，不再读取完整旧文案。请本地化重写，不要机器直译。

通用要求：
- 每个国家必须使用对应本地语言。
- 标题必须继承 ES 已确认意图，但短标题不能超过75字符。
- 每个候选必须输出 zh 和 highlight_zh；中文说明要精简但完整，方便新手截图给主管看，不能只写几个关键词。
- 商品亮点≤125字符，目标95-115字符；补足标题放不下的信息，优先材质、核心尺寸/底座、调节角度、开关和使用场景，避免和标题机械重复。
- 传统长标题≤200字符，仅作历史兼容参考。
- 灯泡安全：禁止 halogen/卤素、incandescent/白炽、Edison、traditional/tradicional、standard bulb 等词。

标题预算：
{title_budget_text()}
{must_inherit_text_for_prompt()}

各国本地化规则：
{lang_rules}

最终 ES 标题：
{es_title}

压缩母版：
{compressed_master_text()}

输出严格 JSON 对象，key 必须是语言代码。示例结构：
{json.dumps(schema, ensure_ascii=False)}

只输出 JSON。"""

def listing_prompt(lang: str, include_aplus: bool = True) -> str:
    title = st.session_state.get("confirmed_titles", {}).get(lang, "")
    return f"""请生成 {LANGS[lang]['market']} Listing 正文，语言必须是 {LANGS[lang]['native']}。

V18.2.8正文模式：只使用确认后的事实卡、压缩母版、ES人工意图和已确认标题/亮点，不再重复传原始旧文案。

关键规则：
- Title 必须完全使用我提供的“已确认短标题”，不得修改、不得缩短、不得重写。
- Item Highlights 必须完全使用我提供的“已确认商品亮点”，不得修改、不得重写。
- 生成完整包：短标题、商品亮点、传统长标题参考、五点、长描述、Search Terms、A+。必须生成完整自然中文解释，方便新手审核；不要输出关键词堆叠。A+ 必须生成5个模块。
- 不要新增不存在功能。灯头/是否含灯泡/尺寸/功率必须准确。
- 灯泡表述采用平台安全模板：只写“兼容对应灯头的 LED 灯泡，最大功率 XW，灯泡不包含”。
- 全文绝对禁止出现 halogen/halógena/halogène/卤素、incandescent/incandescente/白炽、Edison、traditional/tradicional、standard bulb 等高风险灯泡词。
- 未确认的信息不要写；不要自动写 no tiene/no incluye/no es 等负面清单，除非灯泡不包含、IP/室内限制或人工明确要求。
- 木材表达：不要过度降级。除非事实卡/人工资料明确写 MDF、仿木、热转印木纹、wood effect、efecto madera、imitation wood、wood-effect 等，否则可按木质/天然木常规表达；若明确是仿木/木纹效果，才写 wood effect / efecto madera / Holzoptik。
- 五点格式要像 Amazon 最常见的自然格式："自然卖点短标题: 具体说明"。
- 五点顺序必须按产品类型固定，不要自由乱排：
  * 吊灯/吸顶吊灯/pendant/suspension/pendelleuchte：1设计风格/主视觉卖点；2材质工艺/灯罩质感；3尺寸/组合安装/高度调节；4灯头兼容/功率/灯泡不含；5使用场景/安装方式/IP。
  * 壁灯/aplique/wall light：1设计风格/主视觉卖点；2功能结构（开关、插头、可调角度、旋转）；3材质和尺寸；4灯头兼容/功率/灯泡不含；5使用场景/安装方式/室内外。
  * 吸顶灯/LED灯：1光效/外观；2功率/流明/色温；3材质/尺寸；4安装方式/适用空间；5IP/安全/注意事项。
- 中文解释不是逐字翻译，而是“审核说明”：精简但完整，不强制字数；必须说明这条标题/亮点/五点在讲什么、是否覆盖关键事实、有没有明显平台风险。

正文生成上下文：
{body_context_text(lang)}

输出 JSON：
{{
  "title": "必须原样等于已确认短标题",
  "title_zh": "短标题中文审核说明，精简但完整，说明产品类型、关键规格、材质/外观、灯头/功能和风险判断",
  "item_highlights": "必须原样等于已确认商品亮点",
  "item_highlights_zh": "商品亮点中文审核说明，说明主打卖点、包含参数和是否漏核心信息",
  "legacy_title": "传统200字符以内标题参考",
  "legacy_title_zh": "传统标题自然中文解释",
  "bullets": ["5条"],
  "bullets_zh": ["对应5条五点的中文审核说明，必须5条；每条说明该卖点主打什么，不要只做短翻译"],
  "description": "长描述",
  "description_zh": "长描述中文审核摘要，精简说明产品定位、关键参数、场景和风险点",
  "search_terms": "250字符以内，不重复品牌，不加标点堆砌",
  "search_terms_zh": "搜索词中文解释",
  "aplus": [{{"module":1,"title":"","body":"","image_prompt_zh":""}}]
}}
A+要求：必须生成5个模块；每个模块包含标题、正文、中文配图提示。
只输出 JSON。
"""

# ------------------------- candidates and listings -------------------------

def parse_candidate_payload(data: Any, lang: str = "") -> List[Dict[str, str]]:
    if isinstance(data, dict):
        data = data.get("candidates") or data.get("titles") or data.get("items") or []
    out = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, str):
            _t = normalize_title(item, lang); out.append({"title": _t, "zh": rule_zh_for_text(_t), "highlight": "", "highlight_zh": "", "legacy_title": "", "legacy_zh": "", "why": "", "risk": ""})
        elif isinstance(item, dict):
            title = normalize_title(item.get("title", ""), lang)
            if title:
                highlight_value = ensure_switch_in_highlight(sanitize_unconfirmed_natural_wood_text(clean_text(item.get("highlight", "") or item.get("item_highlights", "") or item.get("item_highlight", "") or item.get("product_highlights", "") or item.get("product_highlight", "") or item.get("亮点", "") or item.get("商品亮点", "")), lang), lang)
                legacy_value = normalize_title(item.get("legacy_title", "") or item.get("long_title", "") or item.get("traditional_title", "") or item.get("legacy", "") or item.get("传统长标题", ""), lang)
                out.append({
                    "title": title,
                    "zh": clean_display_zh(item.get("zh", "") or item.get("title_zh", ""), title),
                    "highlight": highlight_value,
                    "highlight_zh": clean_display_zh(item.get("highlight_zh", "") or item.get("item_highlights_zh", "") or item.get("item_highlight_zh", "") or item.get("product_highlights_zh", "") or item.get("product_highlight_zh", "") or item.get("亮点中文", "") or item.get("商品亮点中文解释", ""), highlight_value),
                    "legacy_title": legacy_value,
                    "legacy_zh": clean_display_zh(item.get("legacy_zh", "") or item.get("long_title_zh", "") or item.get("traditional_title_zh", "") or item.get("legacy_title_zh", "") or item.get("传统标题中文解释", ""), legacy_value),
                    "why": clean_display_zh(item.get("why", "") or item.get("kept", ""), ""),
                    "risk": clean_text("" if looks_like_raw_payload(item.get("risk", "")) else (item.get("risk", "") or item.get("risk_code", ""))),
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
        possible_keys = [
            lang, lang.lower(), lang.upper(),
            LANGS[lang]["name"], LANGS[lang]["market"], LANGS[lang]["native"],
        ]
        block = None
        for k in possible_keys:
            if k in data:
                block = data.get(k)
                break
        if block is None and isinstance(data.get("languages"), dict):
            for k in possible_keys:
                if k in data["languages"]:
                    block = data["languages"].get(k)
                    break
        if block is None:
            continue
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
    # V18: regenerate only when all candidates break the hard short-title or highlight limits.
    def bad(c):
        t = clean_text(c.get("title", ""))
        h = clean_text(c.get("highlight", ""))
        # V18 candidate is not usable unless both short title and item highlights exist.
        return (not t) or len(t) > TITLE_LIMIT or (not h) or len(h) > HIGHLIGHT_LIMIT or len(h) < HIGHLIGHT_SOFT_MIN or bool(title_blocking_issues(t, lang))
    return all(bad(c) for c in cands)


def compress_candidates_prompt(lang: str, cands: List[Dict[str, str]]) -> str:
    es_title = current_es_title()
    current_titles = "\n".join([f"{i+1}. 标题: {c.get('title','')} | 亮点: {c.get('highlight','')}" for i, c in enumerate(cands)])
    return f"""下面是 {LANGS[lang]['market']} 的 V18 标题候选，但它们过长、过短或风险偏高。请重新生成 3 个更自然、信息更完整的候选。语言必须是 {LANGS[lang]['native']}。

{title_rules(lang)}

压缩规则：
- 短标题必须 ≤75 字符，优先品牌 + 产品类型 + 1-2 个最高价值规格；理想 68-72 字符，避免卡到 75/75。
- 商品亮点必须 ≤125 字符，目标 95-115 字符，用逗号短语补充材质、核心尺寸/底座、调节角度、开关、用途、IP、调光、插头线、上下出光等信息。
- 传统长标题可生成 ≤200 字符版本，仅作历史兼容参考。
- 短标题和商品亮点尽量不要重复同一个关键词；不要把旧长标题拆成两个重复字段。
- 禁止出现 halogen/卤素、incandescent/白炽、Edison、traditional/tradicional、standard bulb 等高风险灯泡词。
- 如果信息太多：A级进短标题，B级进商品亮点，C级进五点/描述。

最终 ES 短标题：
{es_title}

当前过长/风险候选：
{current_titles}

产品事实卡：
{fact_card_text()}

ES人工意图记录：
{intent_prompt_text()}

输出 JSON 数组，每个元素只保留这些字段：
{{"title":"75字符以内{LANGS[lang]['native']}短标题", "zh":"标题中文审核说明，精简但完整", "highlight":"95-115字符最佳、125字符以内商品亮点", "highlight_zh":"商品亮点中文审核说明，精简但完整", "risk_code":"ok / too_long / grammar_check / missing_core / material_risk"}}
必须输出 zh 和 highlight_zh，中文解释要精简但完整，不强制字数，不要关键词堆叠，不要漏关键审核点。只输出 JSON。"""

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



def set_current_title(lang: str, title: str, zh: str = "", highlight: str = "", highlight_zh: str = "", legacy_title: str = "", legacy_zh: str = "") -> None:
    title = normalize_title(title, lang)
    highlight = clean_text(highlight)
    legacy_title = normalize_title(legacy_title, lang)
    if lang == "ES":
        st.session_state["selected_es_title"] = title
        st.session_state["selected_es_title_zh"] = zh or ""
        st.session_state["selected_es_title_zh_source"] = title if zh else ""
        st.session_state["current_highlight::ES"] = highlight
        st.session_state["current_highlight_zh::ES"] = highlight_zh or ""
        st.session_state["current_legacy_title::ES"] = legacy_title
        st.session_state["current_legacy_title_zh::ES"] = legacy_zh or ""
    else:
        current_key = f"current_title::{lang}"
        zh_key = f"current_title_zh::{lang}"
        st.session_state[current_key] = title
        st.session_state[zh_key] = zh or ""
        st.session_state[f"current_title_zh_source::{lang}"] = title if zh else ""
        st.session_state[f"current_highlight::{lang}"] = highlight
        st.session_state[f"current_highlight_zh::{lang}"] = highlight_zh or ""
        st.session_state[f"current_legacy_title::{lang}"] = legacy_title
        st.session_state[f"current_legacy_title_zh::{lang}"] = legacy_zh or ""
    # Force editable widgets to remount with the new generated/selected content.
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
    return (
        f"V18新规：当前 ES 短标题 {n}/75。多国语言短标题目标 45-75 字符；"
        "商品亮点目标 80-125 字符；传统长标题参考 ≤200 字符。"
        "A级信息进短标题，B级信息进商品亮点，C级信息进五点/描述。"
    )


def target_title_max() -> int:
    return TITLE_LIMIT

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



# ------------------------- ES human intent ledger -------------------------
INTENT_SYNONYMS = {
    # Concept IDs are the bridge between ES supervisor decisions and localized marketplace wording.
    # Keep these lists broad: the risk engine must recognize a good local title instead of creating false warnings.
    "covered_outdoor": ("有遮蔽户外/室外使用", [
        "exterior cubierto", "exteriores cubiertos", "uso exterior cubierto", "outdoor", "covered outdoor", "covered exterior", "covered outdoor use",
        "extérieur couvert", "exterieur couvert", "extérieur abrité", "exterieur abrite", "espace extérieur abrité", "extérieur sous abri",
        "esterni coperti", "esterno coperto", "spazi esterni coperti", "aree esterne coperte",
        "exterior coberto", "áreas exteriores cobertas", "areas exteriores cobertas", "espaços exteriores cobertos", "espacos exteriores cobertos",
        "overdekte buitenruimte", "overdekte buitenruimtes", "overdekte buitenruimten", "overdekt buiten", "beschutte buitenomgeving", "beschutte buitenruimtes",
        "geschützter außenbereich", "geschützte außenbereiche", "geschuetzter aussenbereich", "geschuetzte aussenbereiche", "überdachte terrasse", "ueberdachte terrasse", "überdacht", "ueberdacht",
        "pod zadaszeniem", "na zewnątrz pod zadaszeniem", "na zewnatrz pod zadaszeniem", "zadaszone miejsca", "zadaszonych miejsc", "miejsca pod zadaszeniem",
        "skyddad utomhus", "skyddade utomhus", "skyddad utomhusmiljö", "skyddade utomhusmiljöer", "skyddade utomhusmiljoer", "utomhus under tak",
        "有遮蔽户外", "遮蔽户外", "有顶户外", "室外", "户外", "阳台", "露台", "庭院"
    ]),
    "bathroom": ("浴室/潮湿区域", [
        "baño", "bano", "zona húmeda", "zona humeda", "zonas húmedas", "zonas humedas", "bathroom", "damp area", "damp areas", "moisture-prone",
        "salle de bains", "salle de bain", "zone humide", "zones humides", "bagno", "zone umide", "casa de banho", "zonas húmidas", "zonas humidas",
        "bad", "badezimmer", "feuchtraum", "feuchträume", "feuchtraeume", "badkamer", "vochtige ruimte", "vochtige ruimtes",
        "łazienka", "lazienka", "strefa wilgotna", "strefy wilgotne", "badrum", "fuktiga utrymmen", "fuktigt utrymme", "浴室", "卫生间", "潮湿区域"
    ]),
    "ip54": ("IP54", ["ip54"]),
    "ip44": ("IP44", ["ip44"]),
    "up_down_light": ("上下出光", [
        "luz arriba y abajo", "iluminación arriba y abajo", "iluminacion arriba y abajo", "luz hacia arriba y abajo", "arriba y abajo",
        "up and down", "up & down", "up-and-down", "up and down lighting", "light upwards and downwards", "upwards and downwards",
        "lumière vers le haut et le bas", "lumiere vers le haut et le bas", "éclairage haut et bas", "eclairage haut et bas", "haut et bas", "vers le haut et le bas",
        "lichtaustritt nach oben und unten", "licht nach oben und unten", "nach oben und unten", "oben und unten", "oben unten", "up-&-down-licht", "up and down licht",
        "luce sopra e sotto", "emissione sopra e sotto", "luce verso l’alto e verso il basso", "luce verso l'alto e verso il basso", "verso l’alto e verso il basso", "verso l'alto e verso il basso",
        "luz para cima e para baixo", "iluminação para cima e para baixo", "iluminacao para cima e para baixo", "cima e baixo",
        "licht omhoog en omlaag", "omhoog en omlaag", "licht naar boven en beneden", "naar boven en beneden", "licht naar boven en naar beneden", "omhoog omlaag",
        "światło góra-dół", "swiatlo gora-dol", "światło ku górze i ku dołowi", "swiatlo ku gorze i ku dolowi", "świeci w górę i w dół", "swieci w gore i w dol", "góra-dół", "gora-dol",
        "ljus uppåt och nedåt", "ljus uppat och nedat", "uppåt och nedåt", "uppat och nedat", "upp- och ned", "upp och ned",
        "上下出光", "上下双向", "上下发光", "上出光", "下出光"
    ]),
    "integrated_led": ("内置LED", [
        "led integrado", "led integrados", "integrated led", "built-in led", "led intégré", "led intégrée", "led integre", "led integrato", "led integrata", "led integrada",
        "geïntegreerde led", "geintegreerde led", "integrierte led", "zintegrowany led", "zintegrowane led", "integrerad led", "内置led", "集成led", "内置 LED"
    ]),
    "white_aluminium": ("白色铝材", ["aluminio blanco", "white aluminium", "aluminium blanc", "alluminio bianco", "alumínio branco", "aluminio branco", "weißes aluminium", "weisses aluminium", "wit aluminium", "biała alumini", "biala alumini", "vit aluminium", "白色铝"]),
    "black_aluminium": ("黑色铝材", ["aluminio negro", "black aluminium", "aluminium noir", "alluminio nero", "alumínio preto", "aluminio preto", "schwarzes aluminium", "schwarzem aluminium", "zwart aluminium", "czarne aluminium", "czarnego aluminium", "svart aluminium", "黑色铝"]),
    "frosted_glass": ("磨砂玻璃/哑光玻璃", [
        "cristal mate", "vidrio mate", "vidrio esmerilado", "cristal esmerilado", "frosted glass", "matt glass", "matte glass", "frosted glass diffuser",
        "verre dépoli", "verre depoli", "verre mat", "verre satiné", "verre satine", "diffuseur en verre satiné", "diffuseur en verre depoli",
        "satiniertes glas", "satiniertem glas", "mattglas", "matter glasdiffusor", "diffusor aus satiniertem glas", "glasdiffusor",
        "vetro satinato", "diffusore in vetro satinato", "vetro opaco", "vidro mate", "vidro fosco", "difusor em vidro mate", "difusor em vidro fosco",
        "matglas", "matglas diffuser", "diffuser van matglas", "diffuser van mat glas", "mat glas", "diffuser van matglas",
        "matowe szkło", "matowego szkła", "matowy szklany dyfuzor", "szklany dyfuzor", "frostat glas", "frostade glaset", "磨砂玻璃", "哑光玻璃", "乳白玻璃"
    ]),
    "no_halogen": ("禁止卤素/白炽/Edison/传统灯泡词", ["halogen", "halógena", "halogène", "incandescent", "incandescente", "edison", "traditional", "tradicional", "standard bulb", "卤素", "白炽"]),
    "no_single_light_count": ("禁止单灯数量词", ["1 foco", "1 luz", "1 spot", "1 light", "1-flammig", "1 luce", "1 licht", "1 punkt", "单头", "单灯"]),
    "no_plug": ("禁止插头线/插头，除非事实确认有", ["enchufe", "plug", "plug-in", "stecker", "prise", "spina", "ficha", "插头线", "插头"]),
    "no_remote": ("禁止遥控，除非事实确认有", ["mando", "remote", "télécommande", "telecommande", "telecomando", "fernbedienung", "遥控"]),
    "demote_3d_dimensions": ("三维尺寸放五点/描述，不强制进标题", ["172 x", "90 x", "28 mm", "尺寸", "dimensions", "dimensiones"]),
}

def split_intent_items(text: str) -> List[str]:
    items = []
    for part in re.split(r"[\n,，;；|]+", text or ""):
        p = clean_text(part.strip(" -•*"))
        if p and p not in items:
            items.append(p)
    return items


def add_unique_intent(key: str, items: List[str]) -> None:
    cur = split_intent_items(st.session_state.get(key, ""))
    for item in items:
        it = clean_text(item)
        if it and it not in cur:
            cur.append(it)
    st.session_state[key] = "；".join(cur)


def concept_key_for_text(text: str) -> str | None:
    low = clean_text(text).lower()
    for key, (zh, kws) in INTENT_SYNONYMS.items():
        if low == key or zh.lower() in low or concept_match_any(low, kws):
            return key
    return None


def localize_intent_keywords(items: List[str]) -> List[Tuple[str, str, List[str]]]:
    out = []
    for raw in items:
        item = clean_text(raw)
        if not item:
            continue
        ck = concept_key_for_text(item)
        if ck and ck in INTENT_SYNONYMS:
            zh, kws = INTENT_SYNONYMS[ck]
            out.append((f"intent_{ck}", zh, kws + [item]))
        else:
            out.append(("intent_" + re.sub(r"\W+", "_", item.lower())[:32], item, [item]))
    # de-dupe by key
    seen, ret = set(), []
    for x in out:
        if x[0] not in seen:
            seen.add(x[0]); ret.append(x)
    return ret


def intent_ledger_text() -> str:
    inc = split_intent_items(st.session_state.get("es_intent_include", ""))
    exc = split_intent_items(st.session_state.get("es_intent_exclude", ""))
    dem = split_intent_items(st.session_state.get("es_intent_demote", ""))
    lines = []
    lines.append("ES人工意图记录（主管在西语阶段的加词/否词，会同步到多国语言）：")
    lines.append("必须保留概念：" + ("、".join(inc) if inc else "无"))
    lines.append("禁止出现概念：" + ("、".join(exc) if exc else "无"))
    lines.append("可降级到五点/描述：" + ("、".join(dem) if dem else "无"))
    return "\n".join(lines)


def infer_intent_from_instruction(text: str, title_after: str = "") -> None:
    """Cheap deterministic intent recorder. It does not call the API.
    It captures obvious supervisor decisions from Chinese/Spanish ES title chat.
    """
    raw = clean_text(text or "")
    combined = (raw + " " + clean_text(title_after or "")).lower()
    include = []
    exclude = []
    demote = []
    # Must-keep concepts.
    if any(x in combined for x in ["户外", "室外", "exterior", "outdoor", "balc", "terra", "patio", "covered", "cubierto", "有遮蔽"]):
        include.append("有遮蔽户外/室外使用")
    if any(x in combined for x in ["浴室", "卫生间", "baño", "bathroom", "salle de bains", "bagno", "casa de banho", "badkamer", "badezimmer"]):
        include.append("浴室/潮湿区域")
    if "ip54" in combined: include.append("IP54")
    if "ip44" in combined: include.append("IP44")
    if any(x in combined for x in ["上下", "arriba y abajo", "up and down", "up&down", "haut et bas", "sopra e sotto", "cima e baixo", "omhoog", "omlaag", "oben und unten", "góra", "dol", "uppåt", "nedåt"]):
        include.append("上下出光")
    if any(x in combined for x in ["内置led", "集成led", "led integrado", "integrated led"]):
        include.append("内置LED")
    if any(x in combined for x in ["白色铝", "aluminio blanco", "white aluminium", "aluminium blanc"]):
        include.append("白色铝材")
    if any(x in combined for x in ["黑色铝", "aluminio negro", "black aluminium", "aluminium noir", "alumínio preto", "zwart aluminium", "schwarzes aluminium"]):
        include.append("黑色铝材")
    if any(x in combined for x in ["磨砂玻璃", "哑光玻璃", "cristal mate", "vidrio mate", "frosted glass", "verre dépoli", "verre satiné", "vetro satinato", "vidro fosco", "matglas", "satiniertes glas", "frostat glas"]):
        include.append("磨砂玻璃/哑光玻璃")
    # Exclusions and demotions.
    if any(x in combined for x in ["不要写 1", "不要1", "别写1", "单头不用", "单灯不用", "1 foco", "1 luz", "1 spot"]):
        exclude.append("禁止单灯数量词")
    if any(x in combined for x in ["卤素", "halogen", "halógen", "edison", "traditional", "tradicional", "白炽", "incandescent"]):
        exclude.append("禁止卤素/白炽/Edison/传统灯泡词")
    if any(x in combined for x in ["不要写插头", "别写插头", "不要插头", "plug", "enchufe"]) and any(x in combined for x in ["不要", "别", "禁止", "sin", "no "]):
        exclude.append("禁止插头线/插头，除非事实确认有")
    if any(x in combined for x in ["遥控", "remote", "mando", "télécommande", "fernbedienung"]) and any(x in combined for x in ["不要", "别", "禁止", "sin", "no "]):
        exclude.append("禁止遥控，除非事实确认有")
    if any(x in combined for x in ["尺寸不要", "不要放尺寸", "三维尺寸", "放五点", "放描述"]):
        demote.append("三维尺寸放五点/描述，不强制进标题")
    if include: add_unique_intent("es_intent_include", include)
    if exclude: add_unique_intent("es_intent_exclude", exclude)
    if demote: add_unique_intent("es_intent_demote", demote)
    if include or exclude or demote:
        hist = st.session_state.setdefault("es_intent_history", [])
        hist.append({"input": raw, "include": include, "exclude": exclude, "demote": demote})


def intent_prompt_text() -> str:
    return intent_ledger_text() + "\n规则：必须保留概念要本地化表达；禁止出现概念及其同义词不得出现在标题、五点、描述、Search Terms、A+。可降级信息不要硬塞标题。"

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

    # Supervisor ES intent ledger: human add/deny decisions from ES title loop become global title constraints.
    for item in localize_intent_keywords(split_intent_items(st.session_state.get("es_intent_include", ""))):
        a.append(item)
    for item in localize_intent_keywords(split_intent_items(st.session_state.get("es_intent_demote", ""))):
        c.append(item)

    # Wall light + IP/outdoor evidence: indoor/outdoor is a title-level distinction for wall lights.
    fc_blob = " ".join(str(fc.get(k, "")) for k in ["indoor_outdoor", "spaces", "core_selling_points", "must_keep_in_titles", "notes_for_copy"])
    wallish = pt and pt[0] == "product_wall"
    if wallish and concept_match_any(es + " " + fc_blob, INTENT_SYNONYMS["covered_outdoor"][1] + ["ip44", "ip54"]):
        a.append(("intent_covered_outdoor_auto", "有遮蔽户外/室外使用", INTENT_SYNONYMS["covered_outdoor"][1]))

    for sock in current_socket_tokens():
        a.append((f"socket_{sock}", f"{sock}灯头/光源", [sock.lower()]))

    for d in extract_key_dimensions(es):
        # Diameter/obvious single visual dimensions are useful in title; full 3D dimensions usually belong in bullets.
        if "x" in d.lower() or "×" in d:
            c.append((f"dim_{d}", f"三维尺寸 {d}", dim_variants(d)))
        else:
            a.append((f"dim_{d}", f"关键尺寸 {d}", dim_variants(d)))

    # Main color/material combinations.
    concepts = [
        ("white", "白色/白色哑光", ["blanco", "white", "bianco", "branco", "weiß", "weiss", "wit", "biały", "bialy", "vit", "白"]),
        ("black", "黑色", ["negro", "black", "nero", "preto", "schwarz", "zwart", "czarn", "svart", "黑"]),
        ("gold", "金色/黄铜色", ["dorado", "gold", "oro", "ottone", "messing", "złot", "zlot", "guld", "金色", "黄铜", "latón", "laton", "brass"]),
        ("natural_wood", "天然木/原木", ["madera", "wood", "bois", "legno", "madeira", "holz", "hout", "drewno", "trä", "tra", "木"]),
        ("metal", "金属材质", ["metal", "metálic", "metalic", "metallo", "métal", "metall", "staal", "stål", "stal", "金属", "钢", "acero", "aluminio", "aluminium", "alluminio", "alumínio", "aluminiowa", "aluminiumkropp", "铝"]),
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



def matched_core_concepts(title: str, tier: str = "A") -> List[str]:
    """Trusted rule-based concept recognition for the current title.
    Used to show newbies what the system actually detected, and to remove model false alarms.
    """
    t = clean_text(title)
    out: List[str] = []
    for key, zh, kws in current_core_concepts().get(tier, []):
        if concept_match_any(t, kws) and zh not in out:
            out.append(zh)
    return out


def trusted_missing_core_concepts(title: str, tier: str = "A") -> List[str]:
    t = clean_text(title)
    missing: List[str] = []
    for key, zh, kws in current_core_concepts().get(tier, []):
        if not concept_match_any(t, kws):
            missing.append(zh)
    return missing


def recognized_concepts_summary(title: str, max_items: int = 8) -> str:
    items = matched_core_concepts(title, "A")
    if not items:
        return ""
    txt = "、".join(items[:max_items])
    if len(items) > max_items:
        txt += f" 等{len(items)}项"
    return txt


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
    # V18: do not over-block short title. Many B-level concepts belong in Item Highlights.
    missing = missing_concepts_by_tier(t)
    # Only show A-level missing when title is extremely generic; otherwise highlight can carry details.
    if missing.get("A") and len(t) < 45:
        issues.append("短标题过于泛，可能缺少核心产品识别：" + "、".join(missing["A"][:2]))
    low_value = ["bombilla no incluida", "bulbs not included", "ampoule non incluse", "lampadine non incluse", "lâmpada não incluída", "leuchtmittel nicht enthalten", "żarówka nie", "ljuskälla ingår inte"]
    if any(x in t.lower() for x in low_value):
        issues.append("短标题写了灯泡不含，应放五点而不是标题")
    for key, zh, kws in localize_intent_keywords(split_intent_items(st.session_state.get("es_intent_exclude", ""))):
        if concept_match_any(t, kws):
            issues.append("触发ES禁止概念：" + zh)
    conflict = socket_conflict_warning()
    if conflict:
        issues.append(conflict)
    return issues

def sanitize_model_risk(risk: str, title: str = "") -> str:
    """Remove model-hallucinated or low-confidence risk notes.

    V17.11 principle: the LLM may suggest risks, but only the deterministic
    rule engine decides what a newbie should see. Generic "missing core info"
    notes from the model create many false alarms, especially after localization
    (e.g. NL "licht omhoog en omlaag", "matglas diffuser").
    """
    r = clean_text(risk)
    if not r:
        return ""
    sockets = set(current_socket_tokens())
    all_sockets = {"E27", "E14", "G9", "GU10", "GU5.3", "G4"}
    wrong = [x for x in all_sockets if x not in sockets]
    missing_words = ["缺失", "未写", "没有写", "missing", "manque", "manca", "fehlt", "brak", "saknar", "falta"]
    parts = re.split(r"[;；。]\s*", r)
    kept = []
    current_keys = {x[0] for tier in current_core_concepts().values() for x in tier}
    matched_zh = set(matched_core_concepts(title, "A") + matched_core_concepts(title, "B")) if title else set()
    for part in parts:
        pl = part.lower().strip()
        if not pl:
            continue
        # Drop clauses mentioning a wrong socket as missing.
        if any(ws.lower() in pl for ws in wrong) and any(k in pl for k in missing_words):
            continue
        # Drop all LLM-generated missing-core notes. Actual missing concepts are added by title_soft_issues().
        if any(k in pl for k in missing_words) and any(x in pl for x in ["核心", "a级", "a級", "core", "info", "información", "information", "信息"]):
            continue
        # If a matched concept is mentioned as missing, it is definitely a false alarm.
        if any(k in pl for k in missing_words) and any(zh.lower() in pl for zh in matched_zh):
            continue
        # Do not let hallucinated gold/brass notes disturb wood/black/white aluminium products unless gold is current.
        if any(x in pl for x in ["金色", "黄铜", "gold", "brass", "dorado", "latón", "laton", "messing", "ottone"]) and "gold" not in current_keys:
            continue
        kept.append(part)
    return "；".join(x for x in kept if x).strip("； ")


def title_blocking_issues(title: str, lang: str = "") -> List[str]:
    issues = title_quality_issues(title, lang)
    hard_words = ["短标题为空", "短标题超长", "品牌 Alpinaluz 没有放第一位", "短标题含中文", "短标题含 SKU", "出现裸 cm", "高风险灯泡禁词"]
    return [x for x in issues if any(w in x for w in hard_words)]


def candidate_score(c: Dict[str, str], lang: str) -> int:
    title = normalize_title(c.get("title", ""), lang)
    highlight = clean_text(c.get("highlight", ""))
    n = len(title)
    hn = len(highlight)
    score = 100
    issues = title_quality_issues(title, lang) + highlight_quality_issues(highlight)
    soft = title_soft_issues(title, lang)
    for issue in issues:
        if "超长" in issue or "含中文" in issue or "品牌" in issue or "SKU" in issue or "裸 cm" in issue or "高风险" in issue:
            score -= 45
        elif "偏短" in issue:
            score -= 10
        else:
            score -= 5
    for issue in soft:
        if "单灯产品" in issue:
            score -= 20
        elif "核心" in issue:
            score -= 10
        elif "触发ES禁止概念" in issue or "不一致" in issue:
            score -= 30
        else:
            score -= 6
    # Prefer clean short titles and informative highlights.
    if 45 <= n <= TITLE_LIMIT:
        score += 20
    elif 35 <= n < 45:
        score += 6
    if HIGHLIGHT_IDEAL_MIN <= hn <= HIGHLIGHT_IDEAL_MAX:
        score += 28
    elif HIGHLIGHT_SOFT_MIN <= hn <= HIGHLIGHT_LIMIT:
        score += 16
    elif 45 <= hn < HIGHLIGHT_SOFT_MIN:
        score -= 14
    joined = (title + " " + highlight).lower()
    good_markers = ["e27", "g9", "gu10", "led", "ip44", "ip54", "cm", "350", "interrupt", "switch", "schalter", "interruttore", "interrupteur", "madera", "wood", "bois", "legno", "holz", "madeira", "drewno", "aluminium", "aluminio"]
    score += min(16, sum(2 for x in good_markers if x in joined))
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
    set_current_title(lang, chosen.get("title", ""), chosen.get("zh", ""), chosen.get("highlight", ""), chosen.get("highlight_zh", ""), chosen.get("legacy_title", ""), chosen.get("legacy_zh", ""))


def auto_confirmable_title(title: str, lang: str, highlight: str = "") -> bool:
    if title_blocking_issues(title, lang):
        return False
    h_issues = highlight_quality_issues(highlight)
    if any("超长" in x or "含中文" in x or "高风险" in x or "为空" in x for x in h_issues):
        return False
    soft = title_soft_issues(title, lang)
    risky = [x for x in soft if ("单灯产品" in x or "不一致" in x or "灯泡不含" in x or "触发ES禁止概念" in x)]
    if risky:
        return False
    return 35 <= len(clean_text(title)) <= TITLE_LIMIT and HIGHLIGHT_SOFT_MIN <= len(clean_text(highlight)) <= HIGHLIGHT_LIMIT


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

def forbidden_bulb_hits(text: str) -> List[str]:
    """Return high-risk bulb words that Amazon/EU marketplace should not see."""
    hits: List[str] = []
    src = text or ""
    for pat in BULB_FORBIDDEN_PATTERNS:
        for m in re.finditer(pat, src, flags=re.I):
            h = clean_text(m.group(0))
            if h and h.lower() not in [x.lower() for x in hits]:
                hits.append(h)
    return hits


def sanitize_forbidden_bulb_text(text: str) -> str:
    """Remove/neutralize high-risk bulb family wording while preserving LED/socket facts."""
    if not text:
        return ""
    t = str(text)
    # Common compatibility phrases from earlier versions; collapse them to LED-only wording.
    replacements = [
        (r"LED\s*,?\s*Edison\s*(?:or|y|e|oder|ou|o|lub)?\s*(?:standard|est[aá]ndar|tradicional(?:es)?|traditional)?\s*(?:bulbs?|bombillas?|lampadine|ampoules?|l[aâ]mpadas?|Leuchtmittel|lampen)?", "LED bulbs"),
        (r"LED[-\s]*,?\s*Edison[-\s]*(?:oder)?\s*Standard(?:lampen|leuchtmittel)?", "LED-Lampen"),
        (r"LED\s*,?\s*Edison\s*(?:ou)?\s*standard", "LED"),
        (r"LED\s*,?\s*Edison\s*(?:o)?\s*standard", "LED"),
        (r"LED\s*,?\s*Edison\s*(?:lub)?\s*standardowe", "LED"),
    ]
    for pat, repl in replacements:
        t = re.sub(pat, repl, t, flags=re.I)
    # Remove forbidden words themselves if they remain.
    for pat in BULB_FORBIDDEN_PATTERNS:
        t = re.sub(pat, "", t, flags=re.I)
    # Cleanup repeated separators/spaces left by removal.
    t = re.sub(r"\s+([,;:.])", r"\1", t)
    t = re.sub(r"([,;])\s*([,;])", r"\1", t)
    t = re.sub(r"\(\s*\)", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" ,;.-")
    return clean_text(t)


def title_quality_issues(title: str, lang: str = "") -> List[str]:
    """Hard/format issues for V18 short title."""
    issues: List[str] = []
    t = clean_text(title)
    if not t:
        issues.append("短标题为空")
        return issues
    n = len(t)
    if n > TITLE_LIMIT:
        issues.append(f"短标题超长 {n}/{TITLE_LIMIT}，不能确认")
    elif n < 25:
        issues.append(f"短标题偏短 {n}/{TITLE_LIMIT}，可能不够清楚")
    elif n >= 73:
        issues.append(f"短标题接近上限 {n}/{TITLE_LIMIT}，建议压到68-72字符留余量")
    if not t.lower().startswith("alpinaluz"):
        issues.append("品牌 Alpinaluz 没有放第一位")
    if re.search(r"[一-鿿]", t):
        issues.append("短标题含中文")
    sku = clean_text(st.session_state.get("sku", ""))
    if sku and sku.lower() in t.lower():
        issues.append("短标题含 SKU / 型号代码")
    if has_naked_cm(t):
        issues.append("出现裸 cm，前面没有具体数字")
    forbidden = forbidden_bulb_hits(t)
    if forbidden:
        issues.append("短标题含 Amazon 高风险灯泡禁词：" + ", ".join(forbidden[:4]))
    return issues


def highlight_quality_issues(highlight: str) -> List[str]:
    issues: List[str] = []
    h = clean_text(highlight)
    if not h:
        issues.append("商品亮点为空")
        return issues
    n = len(h)
    if n > HIGHLIGHT_LIMIT:
        issues.append(f"商品亮点超长 {n}/{HIGHLIGHT_LIMIT}")
    elif n < HIGHLIGHT_SOFT_MIN:
        issues.append(f"商品亮点偏短 {n}/{HIGHLIGHT_LIMIT}，建议补充材质、Ø尺寸/底座、调节、开关和使用场景")
    elif n < HIGHLIGHT_IDEAL_MIN:
        issues.append(f"商品亮点可再丰富 {n}/{HIGHLIGHT_LIMIT}，目标 {HIGHLIGHT_IDEAL_MIN}-{HIGHLIGHT_IDEAL_MAX} 字符")
    if re.search(r"[一-鿿]", h):
        issues.append("商品亮点含中文")
    forbidden = forbidden_bulb_hits(h)
    if forbidden:
        issues.append("商品亮点含 Amazon 高风险灯泡禁词：" + ", ".join(forbidden[:4]))
    return issues


def candidate_display_risk(c: Dict[str, str], lang: str) -> str:
    title = c.get("title", "")
    highlight = c.get("highlight", "")
    issues = title_quality_issues(title, lang) + highlight_quality_issues(highlight)
    soft = title_soft_issues(title, lang)
    model_risk = sanitize_model_risk(c.get("risk", ""), title + " " + highlight)
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


def length_card_html(label: str, value: int, limit: int, state: str, hint: str = "") -> str:
    return (
        f"<div class='length-card {state}'>"
        f"<div class='k'>{html.escape(label)}</div>"
        f"<div class='v'>{value}/{limit}</div>"
        f"<div class='hint'>{html.escape(hint)}</div>"
        f"</div>"
    )


def render_title_length_box(title: str, lang: str, highlight: str = "") -> bool:
    n = len(clean_text(title))
    hn = len(clean_text(highlight))
    issues = title_quality_issues(title, lang) + highlight_quality_issues(highlight)
    soft = title_soft_issues(title, lang)
    hard = title_blocking_issues(title, lang)
    blocking = n > TITLE_LIMIT or hn > HIGHLIGHT_LIMIT or not clean_text(title) or not clean_text(highlight) or bool(hard) or any("高风险灯泡禁词" in x or "含中文" in x for x in issues)
    title_state = "bad-len" if (not clean_text(title) or n > TITLE_LIMIT or bool(hard)) else ("warn-len" if n < 35 else "ok-len")
    high_state = "bad-len" if (not clean_text(highlight) or hn > HIGHLIGHT_LIMIT or any("商品亮点含" in x for x in issues)) else ("warn-len" if hn < HIGHLIGHT_IDEAL_MIN else "ok-len")
    title_hint = "可确认" if title_state == "ok-len" else ("过长/硬风险" if title_state == "bad-len" else "偏短，建议检查")
    high_hint = f"理想 {HIGHLIGHT_IDEAL_MIN}-{HIGHLIGHT_IDEAL_MAX}" if high_state != "bad-len" else "为空/过长/风险"
    html_cards = "<div class='length-grid'>" + length_card_html("短标题", n, TITLE_LIMIT, title_state, title_hint) + length_card_html("商品亮点", hn, HIGHLIGHT_LIMIT, high_state, high_hint) + length_card_html("传统标题", len(clean_text(st.session_state.get('current_legacy_title::' + lang, '') if lang != 'ES' else st.session_state.get('current_legacy_title::ES', ''))), LEGACY_TITLE_LIMIT, "ok-len", "参考") + "</div>"
    st.markdown(html_cards, unsafe_allow_html=True)
    if highlight:
        st.markdown(f"<div class='highlight-callout'><span class='label'>商品亮点 / Item Highlights</span>{safe_html_text(clean_text(highlight))}</div>", unsafe_allow_html=True)
    notes = issues + soft
    if notes:
        st.markdown(f"<div class='{ 'bad' if blocking else 'warn'}'><b>检查提示：</b>{safe_html_text('；'.join(notes))}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='ok'><b>字数与硬规则：</b>可确认</div>", unsafe_allow_html=True)
    rec = recognized_concepts_summary((title or "") + " " + (highlight or ""))
    if rec and not blocking:
        st.markdown(f"<div class='zhbox'><b>规则已识别核心：</b>{html.escape(rec)}</div>", unsafe_allow_html=True)
    return not blocking


def render_candidate_cards(cands: List[Dict[str, str]], lang: str, prefix: str, compact: bool = None) -> None:
    """Render V18 candidates: short title + item highlights + legacy title."""
    if compact is None:
        compact = bool(st.session_state.get("newbie_auto_title", True))
    if not cands:
        return
    selected_idx = int(st.session_state.get(f"selected_candidate_idx::{lang}", best_candidate_index(cands, lang)))
    recommended_idx = best_candidate_index(cands, lang)

    def one_card(i: int, c: Dict[str, str]) -> None:
        title = c.get("title", "")
        zh = c.get("zh", "")
        highlight = c.get("highlight", "")
        highlight_zh = c.get("highlight_zh", "")
        legacy_title = c.get("legacy_title", "")
        legacy_zh = c.get("legacy_zh", "")
        why = c.get("why", "") or c.get("kept", "")
        risk = candidate_display_risk(c, lang)
        n = len(title)
        hn = len(highlight)
        ln = len(legacy_title)
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
        recognized = recognized_concepts_summary((title or "") + " " + (highlight or ""))
        rec_html = f"<div class='concept-ok'>规则识别：✓ {safe_html_text(recognized)}</div>" if recognized else ""
        legacy_html = f"<div class='small-muted'><b>传统200字标题参考（{ln}/200）：</b>{safe_html_text(legacy_title)}</div><div class='small-muted'>中文：{safe_html_text(legacy_zh)}</div>" if legacy_title else ""
        # V18.2.8: newbie-first card. Default view shows only what a new operator needs
        # to confirm; all supervisor/debug details stay folded to avoid visual noise.
        with st.container(border=True):
            st.caption(f"候选{i+1} · {' / '.join(badges)} · 短标题 {n}/{TITLE_LIMIT} · 亮点 {hn}/{HIGHLIGHT_LIMIT}")
            st.markdown(f"**短标题：** {title}")
            st.success(f"**商品亮点 / Item Highlights** · {hn}/{HIGHLIGHT_LIMIT}\n\n{highlight}")
            quick_zh = zh or clean_display_zh('', title)
            quick_high_zh = highlight_zh or clean_display_zh('', highlight)
            st.info(f"中文快看：{quick_zh}\n\n亮点说明：{quick_high_zh}")
            if risk and risk != "无明显风险":
                st.warning(f"规则提示：{risk}")
            else:
                st.caption("规则提示：无明显硬风险，可作为一键确认候选。")
            with st.expander("主管/高级信息：传统标题、规则识别、完整检查", expanded=False):
                if legacy_title:
                    st.write(f"传统200字标题参考（{ln}/200）：{legacy_title}")
                    if legacy_zh:
                        st.write(f"传统标题中文：{legacy_zh}")
                st.write(f"规则检查：{risk}")
                if recognized:
                    st.write(f"规则识别：✓ {recognized}")
        if st.button(f"选择候选 {i+1}", key=f"select_candidate::{prefix}::{i+1}"):
            st.session_state[f"selected_candidate_idx::{lang}"] = i
            set_current_title(lang, title, zh, highlight, highlight_zh, legacy_title, legacy_zh)
            st.rerun()

    if compact:
        st.markdown("##### AI 推荐：短标题 + 商品亮点（新手默认只看这个）")
        one_card(recommended_idx, cands[recommended_idx])
        with st.expander("高级：查看另外两个候选 / 手动选择", expanded=False):
            for i, c in enumerate(cands):
                if i != recommended_idx:
                    one_card(i, c)
    else:
        for i, c in enumerate(cands):
            one_card(i, c)


SWITCH_TERMS_BY_LANG = {
    "ES": ["interruptor"], "EN": ["switch"], "FR": ["interrupteur"], "IT": ["interruttore"],
    "PT": ["interruptor"], "DE": ["schalter"], "NL": ["schakelaar"], "PL": ["włącznik", "wlacznik"], "SE": ["strömbrytare", "strombrytare"],
}

def switch_confirmed() -> bool:
    fc = st.session_state.get("fact_card", {}) or {}
    blob = " ".join([
        str(fc.get("switch_included", "")), str(fc.get("switch_type", "")),
        str(fc.get("core_selling_points", "")), str(fc.get("must_keep_in_titles", "")),
        str(fc.get("notes_for_copy", "")), str(st.session_state.get("tech_notes", "")),
    ]).lower()
    positive = ["已确认有", "confirmado", "confirmada", "confirmed", "integrado", "integrated", "incorporado", "built-in", "interrup", "switch", "schalter", "włącz", "wlacz", "schakel", "strömbryt", "strombryt", "开关"]
    negative = ["已确认无", "sin interruptor", "no switch", "ohne schalter", "senza interruttore", "sem interruptor", "未确认"]
    return any(x in blob for x in positive) and not any(x in blob for x in negative)

def highlight_has_switch(text: str, lang: str = "") -> bool:
    low = clean_text(text).lower()
    terms = SWITCH_TERMS_BY_LANG.get(lang, []) + ["switch", "interrup", "schalter", "włącz", "wlacz", "schakel", "strömbryt", "strombryt", "开关"]
    return any(t.lower() in low for t in terms)

def switch_phrase_for_lang(lang: str) -> str:
    return {
        "ES": "con interruptor", "EN": "with switch", "FR": "avec interrupteur", "IT": "con interruttore",
        "PT": "com interruptor", "DE": "mit Schalter", "NL": "met schakelaar", "PL": "z włącznikiem", "SE": "med strömbrytare",
    }.get(lang, "with switch")

def ensure_switch_in_highlight(text: str, lang: str = "") -> str:
    h = clean_text(text)
    if not h or not switch_confirmed() or highlight_has_switch(h, lang):
        return h
    phrase = switch_phrase_for_lang(lang)
    candidate = clean_text(h.rstrip(" .,;") + ", " + phrase)
    if len(candidate) <= HIGHLIGHT_LIMIT:
        return candidate
    # If too long, replace a lower-value ending scene phrase with the switch phrase.
    scene_patterns = [
        r",?\s*ideal\s+para\s+[^,;]{8,40}$", r",?\s*ideal\s+for\s+[^,;]{8,40}$", r",?\s*idéal(?:e)?\s+[^,;]{8,40}$",
        r",?\s*ideale\s+per\s+[^,;]{8,40}$", r",?\s*ideal\s+[^,;]{8,40}$", r",?\s*idealny\s+[^,;]{8,40}$",
        r",?\s*perfekt\s+[^,;]{8,40}$", r",?\s*ideaal\s+[^,;]{8,40}$",
    ]
    for pat in scene_patterns:
        replaced = re.sub(pat, ", " + phrase, h, flags=re.I)
        if replaced != h and len(clean_text(replaced)) <= HIGHLIGHT_LIMIT:
            return clean_text(replaced)
    # Last resort: truncate at previous comma and append switch.
    base = h
    while len(clean_text(base.rstrip(" .,;") + ", " + phrase)) > HIGHLIGHT_LIMIT and "," in base:
        base = base.rsplit(",", 1)[0]
    return clean_text(base.rstrip(" .,;") + ", " + phrase)[:HIGHLIGHT_LIMIT].rstrip(" ,.;")

def clean_listing(data: Dict[str, Any], lang: str) -> Dict[str, Any]:
    title = normalize_title(sanitize_forbidden_bulb_text(st.session_state.get("confirmed_titles", {}).get(lang, "") or data.get("title", "")), lang)
    item_highlights = ensure_switch_in_highlight(sanitize_unconfirmed_natural_wood_text(sanitize_forbidden_bulb_text(clean_text(st.session_state.get("confirmed_highlights", {}).get(lang, "") or data.get("item_highlights", "") or data.get("highlight", ""))), lang), lang)[:HIGHLIGHT_LIMIT]
    legacy_title = normalize_title(sanitize_unconfirmed_natural_wood_text(sanitize_forbidden_bulb_text(st.session_state.get("confirmed_legacy_titles", {}).get(lang, "") or data.get("legacy_title", "")), lang), lang)[:LEGACY_TITLE_LIMIT]
    bullets = data.get("bullets") or []
    bullets_zh = data.get("bullets_zh") or []
    if not isinstance(bullets, list):
        bullets = [str(bullets)]
    if not isinstance(bullets_zh, list):
        bullets_zh = [str(bullets_zh)]
    bullets = [sanitize_unconfirmed_natural_wood_text(sanitize_forbidden_bulb_text(clean_text(x)), lang) for x in bullets if clean_text(x)][:5]
    bullets_zh = [clean_text(x) for x in bullets_zh if clean_text(x)][:5]
    while len(bullets) < 5:
        bullets.append("")
    while len(bullets_zh) < 5:
        bullets_zh.append("")
    aplus = data.get("aplus") or []
    if not isinstance(aplus, list):
        aplus = []
    cleaned_aplus = []
    for m in aplus[:5]:
        if isinstance(m, dict):
            mm = dict(m)
            mm["title"] = sanitize_unconfirmed_natural_wood_text(sanitize_forbidden_bulb_text(mm.get("title", "")), lang)
            mm["body"] = sanitize_unconfirmed_natural_wood_text(sanitize_forbidden_bulb_text(mm.get("body", "")), lang)
            cleaned_aplus.append(mm)
    return {
        "title": title,
        "title_zh": clean_display_zh(data.get("title_zh", ""), title),
        "item_highlights": item_highlights,
        "item_highlights_zh": clean_display_zh(data.get("item_highlights_zh", ""), item_highlights),
        "legacy_title": legacy_title,
        "legacy_title_zh": clean_display_zh(data.get("legacy_title_zh", ""), legacy_title),
        "bullets": bullets[:5],
        "bullets_zh": [clean_display_zh(x, bullets[i] if i < len(bullets) else "") for i, x in enumerate(bullets_zh[:5])] if any(clean_text(x) for x in bullets_zh[:5]) else [],
        "description": sanitize_unconfirmed_natural_wood_text(sanitize_forbidden_bulb_text(str(data.get("description", "")).strip()), lang),
        "description_zh": clean_display_zh(data.get("description_zh", ""), sanitize_unconfirmed_natural_wood_text(sanitize_forbidden_bulb_text(str(data.get("description", "")).strip()), lang)[:1200]),
        "search_terms": sanitize_unconfirmed_natural_wood_text(sanitize_forbidden_bulb_text(clean_text(data.get("search_terms", ""))), lang)[:250],
        "search_terms_zh": clean_display_zh(data.get("search_terms_zh", ""), data.get("search_terms", "")) or "搜索词围绕产品类型、灯头、颜色材质、开关、可调节、尺寸和使用场景。",
        "aplus": cleaned_aplus[:5],
    }



def listing_zh_prompt(lang: str, data: Dict[str, Any]) -> str:
    return f"""请把下面 {LANGS[lang]['native']} Listing 的主要内容翻译/解释成中文，供中国运营审核。
要求：
- 只输出 JSON；
- 不要改外语原文；
- bullets_zh 必须5条，对应5条五点；
- description_zh 只需摘要，不要逐字长翻；
- search_terms_zh 简短说明搜索词方向。

Listing JSON:
{json.dumps({
    'title': data.get('title',''),
    'item_highlights': data.get('item_highlights',''),
    'legacy_title': data.get('legacy_title',''),
    'bullets': data.get('bullets',[]),
    'description': data.get('description',''),
    'search_terms': data.get('search_terms',''),
}, ensure_ascii=False)}

输出 JSON:
{{"title_zh":"", "item_highlights_zh":"", "legacy_title_zh":"", "bullets_zh":["","","","",""], "description_zh":"", "search_terms_zh":""}}
"""



def listing_zh_is_good(data: Dict[str, Any]) -> bool:
    """中文解释是否足够给新手看。不能是空白、不能只是关键词碎片。"""
    def good_sentence(x: Any, min_len: int = 8) -> bool:
        t = clean_text(str(x or ""))
        if not t or t in {"中文解释未生成", "暂无中文解释"}:
            return False
        if len(t) < min_len:
            return False
        # Keyword-only strings usually have many Chinese commas but no sentence ending or verbs.
        if "、" in t and not any(p in t for p in "。；，适合采用带配备支持方便用于可"):
            return False
        return has_cjk(t)
    if not good_sentence(data.get("title_zh"), 16):
        return False
    if not good_sentence(data.get("item_highlights_zh"), 16):
        return False
    bzh = data.get("bullets_zh") or []
    if not isinstance(bzh, list) or len([x for x in bzh if good_sentence(x, 6)]) < 5:
        return False
    if not good_sentence(data.get("description_zh"), 20):
        return False
    if not good_sentence(data.get("search_terms_zh"), 10):
        return False
    return True

def enrich_listing_with_zh(lang: str, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        raw = llm(listing_zh_prompt(lang, data), "你是电商 Listing 中文审核解释助手。只输出 JSON。", model=st.session_state.get("translation_model", "gpt-5.4-mini"), effort="medium", label=f"{lang}中文解释mini")
        zh = safe_json(raw, {})
        if isinstance(zh, dict):
            for key in ["title_zh", "item_highlights_zh", "legacy_title_zh", "description_zh", "search_terms_zh"]:
                if clean_text(zh.get(key, "")):
                    data[key] = clean_text(zh.get(key, ""))
            if isinstance(zh.get("bullets_zh"), list):
                data["bullets_zh"] = [clean_text(x) for x in zh.get("bullets_zh", [])][:5]
    except Exception as e:
        record_rule_step(f"{lang}中文解释mini失败", str(e))
    return data

def listing_validation_errors(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not clean_text(data.get("title", "")):
        errors.append("缺少短标题")
    if len(clean_text(data.get("title", ""))) > TITLE_LIMIT:
        errors.append("短标题超长")
    if not clean_text(data.get("item_highlights", "")):
        errors.append("缺少商品亮点")
    if len(clean_text(data.get("item_highlights", ""))) > HIGHLIGHT_LIMIT:
        errors.append("商品亮点超长")
    bullets = [clean_text(x) for x in data.get("bullets", []) if clean_text(x)]
    if len(bullets) < 5:
        errors.append(f"五点不完整：{len(bullets)}/5")
    if len(clean_text(data.get("description", ""))) < 300:
        errors.append("长描述过短或为空")
    if len(clean_text(data.get("search_terms", ""))) < 30:
        errors.append("Search Terms 过短或为空")
    aplus = data.get("aplus", [])
    valid_aplus = [m for m in aplus if isinstance(m, dict) and clean_text(m.get("title", "")) and clean_text(m.get("body", ""))]
    if len(valid_aplus) < 5:
        errors.append(f"A+模块不完整：{len(valid_aplus)}/5")
    combined = listing_to_text_for_validation(data)
    forbidden = forbidden_bulb_hits(combined)
    if forbidden:
        errors.append("存在高风险灯泡词：" + ", ".join(forbidden[:4]))
    return errors


def listing_to_text_for_validation(data: Dict[str, Any]) -> str:
    parts = [
        data.get("title", ""), data.get("item_highlights", ""), data.get("legacy_title", ""),
        " ".join(data.get("bullets", []) if isinstance(data.get("bullets", []), list) else []),
        data.get("description", ""), data.get("search_terms", ""),
    ]
    for m in data.get("aplus", []) if isinstance(data.get("aplus", []), list) else []:
        if isinstance(m, dict):
            parts.extend([str(m.get("title", "")), str(m.get("body", ""))])
    return " ".join(parts)


def is_listing_complete(data: Dict[str, Any]) -> bool:
    return bool(data) and not listing_validation_errors(data)

def listing_to_text(lang: str, data: Dict[str, Any]) -> str:
    lines = [f"[{lang}]", "", "[TITLE ≤75]", data.get("title", ""), "", "[标题中文解释]", data.get("title_zh", ""), "", "[ITEM HIGHLIGHTS ≤125]", data.get("item_highlights", ""), "", "[商品亮点中文解释]", data.get("item_highlights_zh", ""), "", "[LEGACY TITLE ≤200 - 参考]", data.get("legacy_title", ""), "", "[传统标题中文解释]", data.get("legacy_title_zh", ""), "", "[BULLETS]"]
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
    high_len = len(data.get("item_highlights", ""))
    legacy_len = len(data.get("legacy_title", ""))
    st.markdown("#### 字数检测")
    st.markdown(
        "<div class='length-grid'>"
        + length_card_html("短标题", title_len, TITLE_LIMIT, "ok-len" if 35 <= title_len <= TITLE_LIMIT else "bad-len", "主标题")
        + length_card_html("商品亮点", high_len, HIGHLIGHT_LIMIT, "ok-len" if HIGHLIGHT_IDEAL_MIN <= high_len <= HIGHLIGHT_LIMIT else ("warn-len" if high_len < HIGHLIGHT_IDEAL_MIN and high_len <= HIGHLIGHT_LIMIT else "bad-len"), f"理想 {HIGHLIGHT_IDEAL_MIN}-{HIGHLIGHT_IDEAL_MAX}")
        + length_card_html("传统标题", legacy_len, LEGACY_TITLE_LIMIT, "ok-len" if legacy_len <= LEGACY_TITLE_LIMIT else "bad-len", "参考")
        + "</div>",
        unsafe_allow_html=True,
    )
    if data.get("item_highlights"):
        st.markdown(f"<div class='highlight-callout'><span class='label'>商品亮点 / Item Highlights</span>{html.escape(clean_text(data.get('item_highlights', '')))}</div>", unsafe_allow_html=True)
    errors = listing_validation_errors(data)
    if errors:
        st.markdown(f"<div class='export-warning'>导出拦截风险：{html.escape('；'.join(errors))}</div>", unsafe_allow_html=True)
    for i, b in enumerate(data.get("bullets", [])[:5], 1):
        n = len(b)
        cls = "ok" if 130 <= n <= 300 else "warn"
        st.markdown(f"<div class='{cls}'><b>五点{i}</b>: {n} 字符 / 建议 150-280</div>", unsafe_allow_html=True)
    dlen = len(data.get("description", ""))
    st.markdown(f"<div class='{ 'ok' if dlen >= 700 else 'warn'}'><b>长描述</b>: {dlen} 字符 / 建议 ≥700</div>", unsafe_allow_html=True)
    slen = len(data.get("search_terms", ""))
    st.markdown(f"<div class='{ 'ok' if 30 <= slen <= 250 else 'bad'}'><b>Search Terms</b>: {slen} 字符 / 30-250</div>", unsafe_allow_html=True)

def make_zip() -> bytes:
    mem = io.BytesIO()
    sku = st.session_state.get("sku", "SKU") or "SKU"
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        skipped = []
        for lang, data in st.session_state.get("listings", {}).items():
            if data and is_listing_complete(data):
                z.writestr(f"listing/{lang}_Listing.txt", listing_to_text(lang, data))
            elif data:
                skipped.append(f"{lang}: " + "；".join(listing_validation_errors(data)))
        readme = f"Alpinaluz Listing Generator {APP_VERSION}\n只导出完整 listing 文件。V18.2.8 固定五点顺序模板，中文解释精简但完整，不新增上报卡，保留新手截图流程；明确仿木/MDF/机器编织时才降级材质表达。\n"
        if skipped:
            readme += "\n以下国家因正文不完整未导出：\n" + "\n".join(skipped) + "\n"
            z.writestr("_INCOMPLETE_SKIPPED.txt", "\n".join(skipped))
        z.writestr("README.txt", readme)
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
    st.checkbox("V18.2.8：多国只用压缩母版", value=True, key="use_compressed_master", help="多国语言标题和正文不再重复传完整旧文案。")
    st.checkbox("正文生成跳过已生成国家", value=True, key="skip_existing_listings", help="已经生成过正文的国家不会重复烧 token，除非先删除/取消。")
    st.checkbox("生成完整中文解释（默认开启，给主管审核用）", value=True, key="generate_listing_zh", help="默认开启：每个国家生成自然中文解释，方便不会外语的同事审核；不要为了省这点 token 影响使用。")
    st.markdown("---")
    st.header("目标国家")
    st.multiselect("选择要做的国家", TARGET_LANGS, default=st.session_state.get("target_langs", TARGET_LANGS), key="target_langs")
    st.markdown("---")
    totals = usage_totals()
    st.header("费用估算")
    st.metric("调用次数", totals["calls"])
    st.metric("估算费用", f"${totals['cost']:.3f}")
    st.caption(f"输入 {totals['input']:,} / 输出 {totals['output']:,} tokens")
    with st.expander("费用明细 / 每一步 token", expanded=False):
        logs = st.session_state.get("api_usage_log", [])
        if not logs:
            st.caption("暂无调用记录。规则检查和跳过步骤会显示为 RULE / 0 token。")
        else:
            for x in reversed(logs[-30:]):
                note = f" · {x.get('note','')}" if x.get('note') else ""
                st.write(f"{x.get('time','')} · {x['label']} · {x['model']} · in {x['input_tokens']:,} / out {x['output_tokens']:,} / total {x.get('total_tokens', x['input_tokens'] + x['output_tokens']):,} · ${x['cost']:.3f}{note}")
    logs_for_csv = st.session_state.get("api_usage_log", [])
    if logs_for_csv:
        csv_lines = ["time,label,model,input_tokens,output_tokens,total_tokens,cost,note"]
        for x in logs_for_csv:
            row = [
                str(x.get("time", "")), str(x.get("label", "")).replace(",", " "), str(x.get("model", "")),
                str(x.get("input_tokens", 0)), str(x.get("output_tokens", 0)), str(x.get("total_tokens", 0)),
                f"{x.get('cost', 0.0):.6f}", str(x.get("note", "")).replace(",", " ").replace("\n", " "),
            ]
            csv_lines.append(",".join(row))
        st.download_button("下载 Token 明细 CSV", data="\n".join(csv_lines).encode("utf-8-sig"), file_name=f"token_usage_{APP_VERSION}.csv", mime="text/csv")
    if st.button("清空费用统计"):
        st.session_state["api_usage_log"] = []
        st.rerun()

# ------------------------- header -------------------------
st.title(f"Alpinaluz Listing Generator {APP_VERSION}")
st.markdown("<div class='info-card'>新流程：①资料与事实卡 → ②ES标题确认 → ③AI预审多国标题 → ④绿色批量确认/黄色人工检查 → ⑤统一生成完整正文包。V18.2.8：保持新手截图流程，不新增上报卡；固定五点顺序；中文解释精简但完整；明确仿木/MDF才降级材质表达。</div>", unsafe_allow_html=True)

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
    st.text_area("技术备注（不能错的事实）", key="tech_notes", height=100, placeholder="例如：E27灯头，灯泡不含；最大40W；壁灯带插头线和线控开关/或直接接线；不是LED集成；尺寸Ø18 cm；材质金属+玻璃。")
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
                    st.session_state["compressed_master_cache"] = ""
                    st.session_state["compressed_master_signature"] = ""
                    record_rule_step("事实卡缓存刷新", "规则处理：清空旧压缩母版缓存")
                    st.success("事实卡已生成，请人工检查。")
                else:
                    st.error("事实卡解析失败，请重试或减少输入内容。")
        except Exception as e:
            st.error(str(e))
    fc = st.session_state.get("fact_card", {}) or {}
    if fc:
        st.markdown(f"<div class='ok'><b>中文事实速览：</b>{html.escape(fact_summary_zh())}</div>", unsafe_allow_html=True)
        st.caption("新手先看上面的中文速览：产品类型、灯头、尺寸、材质、颜色、是否含灯泡如果大方向正确，再检查下面重点字段。")
        st.markdown("<div class='info-card'><b>新手重点：</b>供电方式、是否带插头线、是否带开关、开关位置、灯头/是否内置LED 必须尽量确认。未确认的内容不要写有，也不要写没有。壁灯如果确认带插头线+开关，这是标题核心卖点；如果确认直接接线，就不能写插头线。</div>", unsafe_allow_html=True)
        for k in FACT_KEYS:
            val = fc.get(k, "")
            if isinstance(val, list):
                val = ", ".join(str(x) for x in val)
            label = f"{FACT_LABELS.get(k, k)}（{k}）"
            usage = FACT_USAGE.get(k, "生成文案用：请人工确认。")
            zh_hint = fact_value_zh_hint(val)
            st.markdown(
                f"<div class='small-muted'><b>{html.escape(label)}</b> ｜ {html.escape(usage)}<br>中文参考：{html.escape(zh_hint)}</div>",
                unsafe_allow_html=True,
            )
            new_val = st.text_area(label, value=str(val or ""), key=f"fact_edit::{k}", height=60 if k not in ["core_selling_points", "must_keep_in_titles", "do_not_claim", "notes_for_copy"] else 95, label_visibility="collapsed")
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

# Step 2C: current short title + item highlights
current_es_value = st.session_state.get("selected_es_title", "")
current_es_highlight = st.session_state.get("current_highlight::ES", "")
current_es_legacy = st.session_state.get("current_legacy_title::ES", "")
es_can_confirm = render_title_length_box(current_es_value, "ES", current_es_highlight)
if current_es_value:
    st.markdown("#### 新手一键确认区")
    st.info(f"当前AI推荐标题：{current_es_value}\n\n中文快看：{st.session_state.get('selected_es_title_zh','') or clean_display_zh('', current_es_value)}")
    if st.button("✅ 一键确认当前 ES 推荐标题+商品亮点", disabled=not es_can_confirm, type="primary"):
        title = normalize_title(current_es_value, "ES")
        highlight = clean_text(current_es_highlight)
        legacy = normalize_title(current_es_legacy, "ES")[:LEGACY_TITLE_LIMIT]
        infer_intent_from_instruction(st.session_state.get("es_title_chat", ""), title + " " + highlight)
        st.session_state["selected_es_title"] = title
        st.session_state["current_highlight::ES"] = highlight
        st.session_state["current_legacy_title::ES"] = legacy
        st.session_state.setdefault("confirmed_titles", {})["ES"] = title
        st.session_state.setdefault("confirmed_highlights", {})["ES"] = highlight
        st.session_state.setdefault("confirmed_legacy_titles", {})["ES"] = legacy
        zh = st.session_state.get("selected_es_title_zh") or "已按当前 ES 短标题确认，请以标题原文为准。"
        st.session_state.setdefault("confirmed_title_zh", {})["ES"] = zh
        st.session_state.setdefault("confirmed_highlight_zh", {})["ES"] = st.session_state.get("current_highlight_zh::ES", "")
        st.session_state["compressed_master_cache"] = ""
        st.session_state["compressed_master_signature"] = ""
        record_rule_step("ES确认后生成压缩母版", "规则处理：后续多国只使用压缩母版")
        _ = compressed_master_text(refresh=True)
        st.success("ES 短标题和商品亮点已确认，压缩母版已刷新")
        st.rerun()
else:
    st.caption("先生成 ES 标题候选，系统会自动推荐一个可确认标题。")

with st.expander("高级编辑 / 重生 ES 标题（主管或熟手使用）", expanded=False):
    es_edit_key = current_title_widget_key("ES")
    edited_es_title = st.text_area("当前 ES 短标题（≤75字符，最终确认对象）", value=current_es_value, key=es_edit_key, height=70)
    edited_es_highlight = st.text_area("当前 ES 商品亮点（≤125字符，标题放不下的核心卖点）", value=current_es_highlight, key=f"highlight_edit::ES::{st.session_state.get('title_edit_version::ES',0)}", height=80)
    edited_es_legacy = st.text_area("传统长标题参考（≤200字符，可选，不作为新规主标题）", value=current_es_legacy, key=f"legacy_title_edit::ES::{st.session_state.get('title_edit_version::ES',0)}", height=80)
    es_can_confirm_edit = render_title_length_box(edited_es_title, "ES", edited_es_highlight)
    if st.session_state.get("selected_es_title_zh"):
        st.markdown(f"<div class='zhbox'><b>当前标题中文：</b>{html.escape(st.session_state.get('selected_es_title_zh',''))}</div>", unsafe_allow_html=True)
    if st.session_state.get("current_highlight_zh::ES"):
        st.markdown(f"<div class='zhbox'><b>当前亮点中文：</b>{html.escape(st.session_state.get('current_highlight_zh::ES',''))}</div>", unsafe_allow_html=True)

    st.text_area("针对当前标题的中文修改要求", key="es_title_chat", height=80, placeholder="例如：短标题保留产品类型和IP54；商品亮点加入户外/浴室/上下出光；传统长标题自然即可。")
    es_btn1, es_btn2, es_btn3 = st.columns([1, 1, 1])
    with es_btn1:
        if st.button("基于当前标题生成下一轮 3 个 ES 选项"):
            try:
                base = normalize_title(edited_es_title, "ES")
                st.session_state.setdefault("title_history", {}).setdefault("ES", []).append(base)
                instr = f"请只基于以下当前标题优化，生成新一轮3个候选；不要回到原始标题重新写。\n当前标题：{base}\n修改要求：{st.session_state.get('es_title_chat','') or '在不改变产品事实的前提下，优化75字符短标题和125字符商品亮点，并生成一个200字符以内传统长标题参考。'}"
                infer_intent_from_instruction(st.session_state.get('es_title_chat',''), base)
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
        if st.button("确认当前 ES 短标题+商品亮点", disabled=not es_can_confirm_edit):
            title = normalize_title(edited_es_title, "ES")
            highlight = clean_text(edited_es_highlight)
            legacy = normalize_title(edited_es_legacy, "ES")[:LEGACY_TITLE_LIMIT]
            infer_intent_from_instruction(st.session_state.get("es_title_chat", ""), title + " " + highlight)
            st.session_state["selected_es_title"] = title
            st.session_state["current_highlight::ES"] = highlight
            st.session_state["current_legacy_title::ES"] = legacy
            st.session_state.setdefault("confirmed_titles", {})["ES"] = title
            st.session_state.setdefault("confirmed_highlights", {})["ES"] = highlight
            st.session_state.setdefault("confirmed_legacy_titles", {})["ES"] = legacy
            zh = st.session_state.get("selected_es_title_zh") or "已按当前 ES 短标题确认，请以标题原文为准。"
            st.session_state.setdefault("confirmed_title_zh", {})["ES"] = zh
            st.session_state.setdefault("confirmed_highlight_zh", {})["ES"] = st.session_state.get("current_highlight_zh::ES", "")
            st.session_state["compressed_master_cache"] = ""
            st.session_state["compressed_master_signature"] = ""
            record_rule_step("ES确认后生成压缩母版", "规则处理：后续多国只使用压缩母版")
            _ = compressed_master_text(refresh=True)
            st.success("ES 短标题和商品亮点已确认，压缩母版已刷新")
            st.rerun()
    if not es_can_confirm_edit and edited_es_title:
        st.caption("短标题必须≤75字符，商品亮点必须≤125字符，且不能含中文/禁词。")


# ------------------------- ES human intent ledger UI -------------------------
if st.session_state.get("confirmed_titles", {}).get("ES") or st.session_state.get("selected_es_title"):
    st.markdown("### ES人工意图记录（同步到多国语言）")
    st.markdown("<div class='info-card'>这里记录你在西班牙标题循环中人工加过/否定过的核心词。多国语言会按这些概念本地化，不需要每个国家重复输入。新手可用中文填写。</div>", unsafe_allow_html=True)
    i1, i2, i3 = st.columns(3)
    with i1:
        st.text_area("必须保留概念（多国标题要本地化体现）", key="es_intent_include", height=90, placeholder="例如：有遮蔽户外/室外使用；IP54；浴室；上下出光；内置LED")
    with i2:
        st.text_area("禁止出现概念（多国都不能写）", key="es_intent_exclude", height=90, placeholder="例如：卤素；Edison；traditional；1 foco；插头线；遥控")
    with i3:
        st.text_area("可降级到五点/描述（不强制标题）", key="es_intent_demote", height=90, placeholder="例如：三维尺寸；安装细节；密封圈；驱动保护")
    st.caption("建议：ES标题定稿后，如果你发现必须加一个概念（如户外/浴室/IP54），直接填到这里，再在第3步点“应用ES人工意图重生未确认/建议检查国家”。")

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
        if cur and auto_confirmable_title(cur, l, st.session_state.get(f"current_highlight::{l}", "")):
            auto_ready.append(l)
        elif cur:
            auto_blocked.append(l)
    if auto_ready:
        st.markdown(f"<div class='ok'>AI推荐可直接确认：{', '.join(auto_ready)}</div>", unsafe_allow_html=True)
        if st.button(f"确认全部无风险短标题+商品亮点（{len(auto_ready)} 个）"):
            for l in auto_ready:
                title = normalize_title(st.session_state.get(f"current_title::{l}", ""), l)
                st.session_state.setdefault("confirmed_titles", {})[l] = title
                st.session_state.setdefault("confirmed_title_zh", {})[l] = st.session_state.get(f"current_title_zh::{l}", "")
                st.session_state.setdefault("confirmed_highlights", {})[l] = st.session_state.get(f"current_highlight::{l}", "")
                st.session_state.setdefault("confirmed_highlight_zh", {})[l] = st.session_state.get(f"current_highlight_zh::{l}", "")
                st.session_state.setdefault("confirmed_legacy_titles", {})[l] = st.session_state.get(f"current_legacy_title::{l}", "")
            st.success("已确认全部无风险短标题和商品亮点。")
            st.rerun()
    if auto_blocked:
        st.markdown(f"<div class='warn'>这些国家仍需人工检查（硬风险或真实缺失）：{', '.join(auto_blocked)}</div>", unsafe_allow_html=True)

    def generate_batch_for_langs(langs_to_gen: List[str], label: str) -> None:
        original_langs = list(langs_to_gen)
        langs_to_gen = [l for l in langs_to_gen if not st.session_state.get("confirmed_titles", {}).get(l)]
        skipped = [l for l in original_langs if l not in langs_to_gen]
        if skipped:
            record_rule_step("跳过已确认国家标题", "已确认不重生：" + ", ".join(skipped))
        if not langs_to_gen:
            st.info("没有需要处理的国家。")
            return
        _ = compressed_master_text(refresh=True)
        try:
            with st.spinner(f"正在批量生成/重生多国标题候选：{', '.join(langs_to_gen)}..."):
                raw = llm(batch_lang_title_prompt(langs_to_gen), "你是多国 Amazon 灯具标题本地化专家。必须执行ES人工意图记录，输出严格 JSON。", label=label)
                result = parse_batch_candidates(raw, langs_to_gen)
                for lang, cands2 in result.items():
                    cands2 = maybe_auto_compress_candidates(lang, cands2, label)
                    st.session_state.setdefault("title_candidates", {})[lang] = cands2
                    bump_lang_version(lang)
                    if cands2:
                        auto_select_best_candidate(lang, cands2)
                missing_batch = [l for l in langs_to_gen if not result.get(l)]
                if missing_batch:
                    st.warning("这些语言批量解析失败，可逐国生成：" + ", ".join(missing_batch))
                notify_done("多国标题候选已生成")
                st.rerun()
        except Exception as e:
            st.error(str(e))

    batch_col1, batch_col2, batch_col3 = st.columns([1, 1, 2])
    with batch_col1:
        if st.button("一键生成未生成国家首轮候选"):
            langs_to_gen = [l for l in target_langs if not st.session_state.get("title_candidates", {}).get(l) and not st.session_state.get("confirmed_titles", {}).get(l)]
            generate_batch_for_langs(langs_to_gen, "多国标题首轮批量")
    with batch_col2:
        if st.button("应用ES人工意图重生未确认/建议检查国家"):
            langs_to_regen = []
            for l in target_langs:
                if st.session_state.get("confirmed_titles", {}).get(l):
                    continue
                cur = st.session_state.get(f"current_title::{l}", "")
                if (not cur) or title_soft_issues(cur, l) or title_blocking_issues(cur, l):
                    langs_to_regen.append(l)
            if not langs_to_regen:
                langs_to_regen = [l for l in target_langs if not st.session_state.get("confirmed_titles", {}).get(l)]
            generate_batch_for_langs(langs_to_regen, "应用ES人工意图重生")
    with batch_col3:
        st.caption("如果ES阶段补了关键词/否定词（如户外、IP54、不要1 foco），先填在第2步的ES人工意图记录，再点“应用ES人工意图”。系统只重生未确认/建议检查国家，不覆盖已确认标题。")

    tabs = st.tabs(target_langs)
    for tab, lang in zip(tabs, target_langs):
        with tab:
            st.subheader(f"{lang} · {LANGS[lang]['market']} 标题")
            confirmed = st.session_state.get("confirmed_titles", {}).get(lang, "")
            if confirmed:
                st.markdown("<span class='status-pill s-ok'>已确认</span>", unsafe_allow_html=True)
                st.text_area("已确认短标题", value=confirmed, key=f"confirmed_show::{lang}", height=70, disabled=True)
                st.text_area("已确认商品亮点", value=st.session_state.get("confirmed_highlights", {}).get(lang, ""), key=f"confirmed_highlight_show::{lang}", height=80, disabled=True)
                st.text_area("传统长标题参考", value=st.session_state.get("confirmed_legacy_titles", {}).get(lang, ""), key=f"confirmed_legacy_show::{lang}", height=80, disabled=True)
                st.markdown(f"<div class='zhbox'><b>标题中文：</b>{html.escape(st.session_state.get('confirmed_title_zh', {}).get(lang,''))}<br><b>亮点中文：</b>{html.escape(st.session_state.get('confirmed_highlight_zh', {}).get(lang,''))}</div>", unsafe_allow_html=True)
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
            current_highlight = st.session_state.get(f"current_highlight::{lang}", "")
            current_legacy = st.session_state.get(f"current_legacy_title::{lang}", "")
            can_confirm = render_title_length_box(current_value, lang, current_highlight)
            if current_value:
                st.markdown("#### 新手一键确认区")
                st.info(f"当前AI推荐标题：{current_value}\n\n中文快看：{st.session_state.get(zh_key,'') or clean_display_zh('', current_value)}")
                if st.button(f"✅ 一键确认当前 {lang} 推荐标题+亮点", key=f"quick_confirm::{lang}", disabled=not can_confirm, type="primary"):
                    title = normalize_title(current_value, lang)
                    highlight = clean_text(current_highlight)
                    legacy = normalize_title(current_legacy, lang)[:LEGACY_TITLE_LIMIT]
                    st.session_state[current_key] = title
                    st.session_state[f"current_highlight::{lang}"] = highlight
                    st.session_state[f"current_legacy_title::{lang}"] = legacy
                    st.session_state.setdefault("confirmed_titles", {})[lang] = title
                    st.session_state.setdefault("confirmed_highlights", {})[lang] = highlight
                    st.session_state.setdefault("confirmed_legacy_titles", {})[lang] = legacy
                    zh = st.session_state.get(zh_key) or "已按当前短标题确认，请以标题原文为准。"
                    st.session_state.setdefault("confirmed_title_zh", {})[lang] = zh
                    st.session_state.setdefault("confirmed_highlight_zh", {})[lang] = st.session_state.get(f"current_highlight_zh::{lang}", "")
                    st.success(f"{lang} 短标题和商品亮点已确认")
                    st.rerun()
            else:
                st.caption("先生成该国家标题候选，系统会自动推荐一个可确认标题。")

            with st.expander(f"高级编辑 / 重生 {lang} 标题（主管或熟手使用）", expanded=False):
                edit_key = current_title_widget_key(lang)
                edited_title = st.text_area("当前短标题（≤75字符，确认对象）", value=current_value, key=edit_key, height=70)
                edited_highlight = st.text_area("当前商品亮点（≤125字符）", value=current_highlight, key=f"highlight_edit::{lang}::{st.session_state.get(f'title_edit_version::{lang}',0)}", height=80)
                edited_legacy = st.text_area("传统长标题参考（≤200字符，可选）", value=current_legacy, key=f"legacy_title_edit::{lang}::{st.session_state.get(f'title_edit_version::{lang}',0)}", height=80)
                can_confirm_edit = render_title_length_box(edited_title, lang, edited_highlight)
                if st.session_state.get(zh_key):
                    st.markdown(f"<div class='zhbox'><b>当前标题中文：</b>{html.escape(st.session_state.get(zh_key,''))}<br><b>当前亮点中文：</b>{html.escape(st.session_state.get(f'current_highlight_zh::{lang}',''))}</div>", unsafe_allow_html=True)

                st.text_area("针对当前标题/亮点的中文修改要求", key=f"chat::{lang}", height=80, placeholder="例如：短标题保留产品类型+IP54；亮点加入浴室/遮蔽户外；删除重复词。")
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    if st.button(f"基于当前标题生成下一轮 {lang} 3 个选项", key=f"refine::{lang}"):
                        try:
                            base = normalize_title(edited_title, lang)
                            st.session_state.setdefault("title_history", {}).setdefault(lang, []).append(base)
                            instr = f"请只基于以下当前标题优化，生成新一轮3个候选；不要回到ES标题重新直译。\n当前标题：{base}\n修改要求：{st.session_state.get(f'chat::{lang}', '') or '在不改变产品事实的前提下，优化75字符短标题和125字符商品亮点，并生成200字符以内传统长标题参考。'}"
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
                    if st.button(f"确认 {lang} 短标题+亮点", key=f"confirm::{lang}", disabled=not can_confirm_edit):
                        title = normalize_title(edited_title, lang)
                        highlight = clean_text(edited_highlight)
                        legacy = normalize_title(edited_legacy, lang)[:LEGACY_TITLE_LIMIT]
                        st.session_state[current_key] = title
                        st.session_state[f"current_highlight::{lang}"] = highlight
                        st.session_state[f"current_legacy_title::{lang}"] = legacy
                        st.session_state.setdefault("confirmed_titles", {})[lang] = title
                        st.session_state.setdefault("confirmed_highlights", {})[lang] = highlight
                        st.session_state.setdefault("confirmed_legacy_titles", {})[lang] = legacy
                        zh = st.session_state.get(zh_key) or "已按当前短标题确认，请以标题原文为准。"
                        st.session_state.setdefault("confirmed_title_zh", {})[lang] = zh
                        st.session_state.setdefault("confirmed_highlight_zh", {})[lang] = st.session_state.get(f"current_highlight_zh::{lang}", "")
                        st.success(f"{lang} 短标题和商品亮点已确认")
                        st.rerun()
                if not can_confirm_edit and edited_title:
                    st.caption("短标题必须≤75字符，商品亮点必须≤125字符，且不能含中文/禁词。")
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
    include_aplus = True
    st.markdown("<div class='ok'>正文将固定生成完整包：短标题 + 商品亮点 + 传统长标题参考 + 五点 + 描述 + Search Terms + A+。V18.2.8：固定五点顺序模板；中文解释精简但完整；不新增上报卡；天然木/手工编织不过度纠结，明确仿木/MDF才降级。</div>", unsafe_allow_html=True)
    already_done = [l for l in selected_langs if is_listing_complete(st.session_state.get("listings", {}).get(l, {}))]
    incomplete_existing = [l for l in selected_langs if st.session_state.get("listings", {}).get(l) and not is_listing_complete(st.session_state.get("listings", {}).get(l, {}))]
    if already_done and st.session_state.get("skip_existing_listings", True):
        st.markdown(f"<div class='warn'>已生成且完整的国家将跳过：{html.escape(', '.join(already_done))}</div>", unsafe_allow_html=True)
    if incomplete_existing:
        st.markdown(f"<div class='export-warning'>发现不完整正文，将自动重跑，不会跳过：{html.escape(', '.join(incomplete_existing))}</div>", unsafe_allow_html=True)
    if st.button("逐国生成完整正文包（含 A+，标题和商品亮点不再修改）"):
        _ = compressed_master_text(refresh=True)
        success_count = 0
        fail_count = 0
        for lang in selected_langs:
            existing = st.session_state.get("listings", {}).get(lang, {})
            if st.session_state.get("skip_existing_listings", True) and is_listing_complete(existing):
                record_rule_step(f"{lang}正文跳过", "已生成且通过完整性校验，不重复消耗token")
                continue
            try:
                with st.spinner(f"正在生成 {lang} 正文..."):
                    raw = llm(listing_prompt(lang, include_aplus), f"你是 {LANGS[lang]['market']} 灯具 Listing 本地文案专家。输出严格 JSON。", label=f"{lang}正文生成")
                    data = safe_json(raw, {})
                    if not isinstance(data, dict):
                        raise ValueError("JSON解析失败")
                    cleaned = clean_listing(data, lang)
                    if st.session_state.get("generate_listing_zh", True) or not listing_zh_is_good(cleaned):
                        cleaned = enrich_listing_with_zh(lang, cleaned)
                    errors = listing_validation_errors(cleaned)
                    if errors:
                        fail_count += 1
                        st.session_state.setdefault("listings", {}).pop(lang, None)
                        record_rule_step(f"{lang}正文校验失败", "未保存：" + "；".join(errors))
                        st.error(f"{lang} 正文不完整，未保存：" + "；".join(errors))
                        continue
                    st.session_state.setdefault("listings", {})[lang] = cleaned
                    success_count += 1
            except Exception as e:
                fail_count += 1
                st.error(f"{lang} 失败：{e}")
        notify_done(f"正文生成完成：成功 {success_count}，失败 {fail_count}")

# ------------------------- Section 5: preview and export -------------------------
st.header("5）预览与导出")
listings = st.session_state.get("listings", {})
if listings:
    st.markdown("### 主管审批摘要")
    review_rows = []
    for l in [x for x in selected_langs if listings.get(x)]:
        d = listings[l]
        errors = listing_validation_errors(d)
        review_rows.append({
            "国家": l,
            "状态": "✅ 可审" if not errors else "❌ 不完整",
            "标题": f"{len(clean_text(d.get('title','')))}/{TITLE_LIMIT}",
            "亮点": f"{len(clean_text(d.get('item_highlights','')))}/{HIGHLIGHT_LIMIT}",
            "五点": len(d.get('bullets', []) or []),
            "A+": len(d.get('aplus', []) or []),
            "主管关注": "；".join(errors[:2]) if errors else clean_text(d.get('item_highlights',''))[:80],
        })
    st.table(review_rows)
    st.caption("主管主要看：状态是否✅、商品亮点是否包含核心卖点、标题是否接近上限、是否有材质/安装/灯泡风险。详细文案在下方各国家标签页。")
    invalid_langs = [l for l in selected_langs if listings.get(l) and not is_listing_complete(listings.get(l, {}))]
    if invalid_langs:
        st.markdown(f"<div class='export-warning'>以下国家正文不完整，不会导出，请重跑：{html.escape(', '.join(invalid_langs))}</div>", unsafe_allow_html=True)
    tabs = st.tabs([l for l in selected_langs if listings.get(l)])
    for tab, lang in zip(tabs, [l for l in selected_langs if listings.get(l)]):
        with tab:
            st.text_area(f"{lang} Listing", value=listing_to_text(lang, listings[lang]), height=560, key=f"listing_text::{lang}")
            render_stats(listings[lang])
    st.download_button(
        "下载 ZIP（只含 listing）",
        data=make_zip(),
        file_name=f"{st.session_state.get('sku','SKU')}_{date.today().isoformat()}_AMAZON_LISTING_V18_2_8.zip",
        mime="application/zip",
    )
else:
    st.info("正文生成后会在这里预览，并可下载只含 listing 的 ZIP。")
