import base64
import io
import json
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Dict, List, Tuple, Any

import streamlit as st
import streamlit.components.v1 as components

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(page_title="Alpinaluz Listing Generator V16.9", layout="wide")

st.markdown("""
<style>
/* V14.5 统一深色界面：黑底浅字，高对比度预览，兼容浏览器浅色模式 */
:root { --bg:#0b0f17; --panel:#111827; --panel2:#1f2937; --text:#f3f4f6; --muted:#cbd5e1; --line:#374151; }
html, body, .stApp, [data-testid="stAppViewContainer"] { background: var(--bg) !important; color: var(--text) !important; }
[data-testid="stHeader"], [data-testid="stToolbar"] { background: rgba(11,15,23,.95) !important; }
[data-testid="stSidebar"] { background: #0f172a !important; color: var(--text) !important; }
div[data-testid="stMarkdownContainer"], label, p, span, h1, h2, h3, h4, h5, h6 { color: var(--text) !important; }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div, .stNumberInput input {
    background-color: var(--panel2) !important;
    color: var(--text) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
}
.stTextArea textarea, pre, code, .stCodeBlock {
    background-color: #0f172a !important;
    color: #f8fafc !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
}
button, .stButton button, .stDownloadButton button { border-radius: 8px !important; border: 1px solid var(--line) !important; }
section[data-testid="stExpander"] { background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 10px !important; }
[data-testid="stTabs"] button { color: var(--text) !important; }
.fact-card, .dark-card { background: var(--panel) !important; color: var(--text) !important; border: 1px solid var(--line) !important; border-radius: 12px !important; padding: 12px !important; }
.stat-ok { background:#052e16 !important; color:#dcfce7 !important; padding:8px 12px; border-radius:8px; margin:4px 0; border:1px solid #166534; }
.stat-bad { background:#3f1212 !important; color:#fee2e2 !important; padding:8px 12px; border-radius:8px; margin:4px 0; border:1px solid #991b1b; }

/* V14.5 强制按钮、下拉、标签在浅色模式也清晰 */
.stButton button, .stDownloadButton button, button[kind="primary"], button[kind="secondary"] {
    background-color: #1f2937 !important;
    color: #f8fafc !important;
    border: 1px solid #475569 !important;
    font-weight: 600 !important;
}
.stButton button:hover, .stDownloadButton button:hover {
    background-color: #334155 !important;
    color: #ffffff !important;
    border-color: #60a5fa !important;
}
[data-baseweb="tag"] {
    background-color: #ef4444 !important;
    color: #ffffff !important;
}
[data-baseweb="popover"], [data-baseweb="menu"] {
    background-color: #111827 !important;
    color: #f8fafc !important;
}
[role="option"] { background-color: #111827 !important; color: #f8fafc !important; }
[role="option"]:hover { background-color: #334155 !important; color: #ffffff !important; }
textarea, input { caret-color: #f8fafc !important; }


/* V14.7 进一步修复白底白字 / hover 难读 / 上传控件浅色问题 */
* { box-sizing: border-box; }
.stApp, .main, .block-container { color: #f8fafc !important; }
[data-testid="stFileUploader"], [data-testid="stFileUploaderDropzone"] {
    background: #111827 !important;
    color: #f8fafc !important;
    border: 1px dashed #475569 !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"] * { color: #f8fafc !important; }
[data-testid="stFileUploader"] button, [data-testid="stFileUploader"] small {
    background: #1f2937 !important;
    color: #f8fafc !important;
}
[data-testid="stFileUploaderFileName"], [data-testid="stFileUploaderFileSize"], [data-testid="stFileUploaderDeleteBtn"] {
    color: #f8fafc !important;
}
textarea, input, select, div[contenteditable="true"] {
    background-color: #111827 !important;
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
}
textarea:focus, input:focus, div[data-baseweb="select"]:focus-within {
    background-color: #0f172a !important;
    color: #ffffff !important;
    border-color: #60a5fa !important;
}
.stTextArea label, .stTextInput label, .stSelectbox label, .stMultiSelect label, .stRadio label, .stCheckbox label {
    color: #f8fafc !important;
}
.stRadio div[role="radiogroup"] label, .stCheckbox label, .stMultiSelect [data-baseweb="tag"] span {
    color: #f8fafc !important;
}
[data-baseweb="select"] * { color: #f8fafc !important; }
[data-baseweb="select"] input { color: #f8fafc !important; -webkit-text-fill-color: #f8fafc !important; }
[data-baseweb="menu"] li, [role="listbox"] [role="option"] {
    background: #111827 !important;
    color: #f8fafc !important;
}
[data-baseweb="menu"] li:hover, [role="listbox"] [role="option"]:hover, [aria-selected="true"] {
    background: #334155 !important;
    color: #ffffff !important;
}
.stButton button:disabled, .stDownloadButton button:disabled {
    background: #111827 !important;
    color: #94a3b8 !important;
    border-color: #334155 !important;
}
.stAlert, [data-testid="stAlert"] {
    background: #111827 !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
}
.stCaptionContainer, .stCaptionContainer * { color: #cbd5e1 !important; }
hr { border-color: #334155 !important; }

/* V14.8: disabled text/white hover fix */
.stTextArea textarea[disabled], .stTextInput input[disabled], textarea:disabled, input:disabled {
    background-color: #0f172a !important;
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
    opacity: 1 !important;
    border: 1px solid #475569 !important;
}
.stTextArea textarea:hover, .stTextInput input:hover, .stNumberInput input:hover {
    background-color: #111827 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-testid="stExpander"] div, [data-testid="stExpander"] p, [data-testid="stExpander"] span {
    color: #f8fafc !important;
}
.stRadio label, .stCheckbox label, .stMultiSelect span, .stSelectbox span {
    color: #f8fafc !important;
}
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    background-color: #0f172a !important;
    color: #f8fafc !important;
}



/* V14.9 强力修复白底白字：所有表单、Expander、提示框、disabled/hover统一深色 */
.stTextArea textarea, .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div, [data-testid="stExpander"], [data-testid="stExpander"] div,
[data-testid="stAlert"], .stAlert, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] {
    background-color: #0f172a !important;
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
}
.stTextArea textarea[disabled], .stTextInput input[disabled], textarea:disabled, input:disabled,
.stTextArea textarea[aria-disabled="true"], .stTextInput input[aria-disabled="true"] {
    background-color: #111827 !important;
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
    opacity: 1 !important;
}
.stTextArea textarea:hover, .stTextInput input:hover, .stSelectbox div[data-baseweb="select"]:hover,
.stMultiSelect div[data-baseweb="select"]:hover {
    background-color: #1e293b !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
.stAlert * , [data-testid="stAlert"] * , [data-testid="stExpander"] * {
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
}
input::placeholder, textarea::placeholder { color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; }


/* V15.1 keyword editor: prevent clipped first letters and keep tri-state table readable */
[data-testid="stDataFrame"] div, [data-testid="stDataFrame"] span, [data-testid="stDataFrame"] input,
[data-testid="stDataEditor"] div, [data-testid="stDataEditor"] span, [data-testid="stDataEditor"] input {
    color: #f8fafc !important;
}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    background-color: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
}
.kw-chip-row { display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 10px 0; }
.kw-chip { display:inline-block; padding:4px 9px; border-radius:999px; font-size:12px; font-weight:700; border:1px solid transparent; }
.kw-must { background:#dc2626; color:#fff; border-color:#f87171; }
.kw-ban { background:#111827; color:#fecaca; border-color:#ef4444; text-decoration: line-through; }
.kw-neutral { background:#1f2937; color:#cbd5e1; border-color:#475569; }
.kw-help { color:#cbd5e1; font-size:13px; line-height:1.45; }



/* V15.2: compact title iteration panel */
.title-compact-note { color:#cbd5e1; font-size:13px; line-height:1.45; margin:4px 0 8px 0; }
section[data-testid="stExpander"] div[role="button"] p { font-weight:700 !important; }
.kw-chip { max-width: 100%; white-space: nowrap; }

</style>
""", unsafe_allow_html=True)

LANGS = {
    "ES": {"market": "Amazon.es", "name": "Español"},
    "FR": {"market": "Amazon.fr", "name": "Français"},
    "DE": {"market": "Amazon.de", "name": "Deutsch"},
    "IT": {"market": "Amazon.it", "name": "Italiano"},
    "NL": {"market": "Amazon.nl", "name": "Nederlands"},
    "PL": {"market": "Amazon.pl", "name": "Polski"},
    "PT": {"market": "Amazon.pt", "name": "Português"},
    "SE": {"market": "Amazon.se", "name": "Svenska"},
    "EN": {"market": "Amazon.co.uk", "name": "English"},
}
ALL_TARGETS = ["FR", "DE", "IT", "NL", "PL", "PT", "SE", "EN"]

PRODUCT_TYPE_OPTIONS = [
    "壁灯", "浴室壁灯", "画灯", "镜前灯", "吊灯", "设计吊灯", "吸顶灯", "Plafón", "落地灯", "设计落地灯", "台灯",
    "户外投光灯", "户外壁灯", "户外柱灯/路灯", "灯串", "LED灯带", "室内LED灯带", "户外LED灯带",
    "嵌入式筒灯", "厨房/衣柜筒灯", "射灯", "轨道灯", "LED面板灯", "线性灯/灯管", "应急灯",
    "夜灯/感应灯", "带灯风扇", "灯泡", "灯泡套装", "LED灯管", "电线带开关插头", "吊灯配件", "吸顶盘/顶盘", "LED变压器"
]

FIELD_OPTIONS = {
    "产品类型": PRODUCT_TYPE_OPTIONS,
    "材质": ["钢", "铝", "铁", "金属", "木", "玻璃", "水晶", "藤编", "竹", "布艺", "亚克力", "塑料", "水泥", "陶瓷", "硅胶"],
    "颜色": ["黑色", "白色", "金色", "银色", "灰色", "绿色", "红色", "蓝色", "粉色", "米色", "木色", "黄铜色", "铬色", "透明", "烟灰色", "黑白", "黑金", "白金"],
    "灯头": ["E27", "E14", "GU10", "G9", "G4", "GX53", "LED integrado", "Sin portalámparas"],
    "风格": ["现代", "极简", "北欧", "复古", "Vintage", "Retro Cinema", "工业", "Wabi-sabi", "经典", "波西米亚", "自然", "日式", "地中海", "Art Déco", "儿童"],
    "适用空间": ["卧室", "客厅", "酒店", "公寓", "床头", "走廊", "书房", "餐厅", "厨房", "厨房岛台", "浴室", "花园", "露台", "门廊", "办公室", "商业空间"],
    "安装方式": ["壁挂", "吊装", "吸顶", "落地", "台面", "嵌入式", "轨道安装", "插电使用", "户外固定安装"],
    "室内/室外": ["室内", "室外", "室内/室外"],
    "是否含灯泡": ["否", "是", "不适用（LED集成）"],
    "是否LED": ["否", "是", "LED集成", "兼容LED灯泡"],
    "调节能力": ["不可调", "轻微角度调整", "可定向调节", "高自由度多角度调节"],
}


# 多选字段：AI 可以识别多个值，新手也可以一次确认多个。
FIELD_MULTI = {"材质", "风格", "适用空间"}

# 新增精细调节字段：物理方向、CCT光色、亮度调光、控制方式分开，避免“可调节”含义混乱。
ADJUSTMENT_EXTRA_FIELDS = ["方向调节", "光色调节", "亮度调节", "控制方式", "用途标签"]

FIELD_OPTIONS.update({
    "方向调节": ["不可调", "轻微角度调整", "可定向调节", "350°旋转", "多角度调节"],
    "光色调节": ["无", "三档CCT 3000K/4000K/6000K", "CCT可调", "无极调色", "遥控调色"],
    "亮度调节": ["无", "可调亮度", "无极调光", "三档亮度", "未提供"],
    "控制方式": ["未提供", "按钮", "拨码开关", "触控", "遥控", "墙控"],
    "用途标签": ["床头阅读", "酒店客房", "USB充电", "功能型壁灯", "收纳托盘", "阅读角", "客厅辅助照明", "卧室氛围灯"],
})

VALUE_MAP: Dict[str, Dict[str, Dict[str, str]]] = {
    "颜色": {
        "黑色": {"ES":"negro","FR":"noir","DE":"schwarz","IT":"nero","NL":"zwart","PL":"czarny","PT":"preto","SE":"svart","EN":"black"},
        "白色": {"ES":"blanco","FR":"blanc","DE":"weiß","IT":"bianco","NL":"wit","PL":"biały","PT":"branco","SE":"vit","EN":"white"},
        "金色": {"ES":"dorado","FR":"doré","DE":"gold","IT":"oro","NL":"goud","PL":"złoty","PT":"dourado","SE":"guld","EN":"gold"},
        "银色": {"ES":"plateado","FR":"argenté","DE":"silber","IT":"argento","NL":"zilver","PL":"srebrny","PT":"prateado","SE":"silver","EN":"silver"},
        "灰色": {"ES":"gris","FR":"gris","DE":"grau","IT":"grigio","NL":"grijs","PL":"szary","PT":"cinzento","SE":"grå","EN":"grey"},
        "绿色": {"ES":"verde","FR":"vert","DE":"grün","IT":"verde","NL":"groen","PL":"zielony","PT":"verde","SE":"grön","EN":"green"},
        "红色": {"ES":"rojo","FR":"rouge","DE":"rot","IT":"rosso","NL":"rood","PL":"czerwony","PT":"vermelho","SE":"röd","EN":"red"},
        "蓝色": {"ES":"azul","FR":"bleu","DE":"blau","IT":"blu","NL":"blauw","PL":"niebieski","PT":"azul","SE":"blå","EN":"blue"},
        "粉色": {"ES":"rosa","FR":"rose","DE":"rosa","IT":"rosa","NL":"roze","PL":"różowy","PT":"rosa","SE":"rosa","EN":"pink"},
        "米色": {"ES":"beige","FR":"beige","DE":"beige","IT":"beige","NL":"beige","PL":"beżowy","PT":"bege","SE":"beige","EN":"beige"},
        "木色": {"ES":"madera natural","FR":"bois naturel","DE":"holzfarben","IT":"legno naturale","NL":"houtkleur","PL":"kolor drewna","PT":"madeira natural","SE":"träfärg","EN":"natural wood"},
        "黄铜色": {"ES":"latón","FR":"laiton","DE":"Messing","IT":"ottone","NL":"messing","PL":"mosiądz","PT":"latão","SE":"mässing","EN":"brass"},
        "铬色": {"ES":"cromo","FR":"chrome","DE":"Chrom","IT":"cromo","NL":"chroom","PL":"chrom","PT":"cromado","SE":"krom","EN":"chrome"},
        "透明": {"ES":"transparente","FR":"transparent","DE":"transparent","IT":"trasparente","NL":"transparant","PL":"przezroczysty","PT":"transparente","SE":"transparent","EN":"transparent"},
        "烟灰色": {"ES":"gris ahumado","FR":"gris fumé","DE":"rauchgrau","IT":"grigio fumé","NL":"rookgrijs","PL":"dymiony szary","PT":"cinzento fumado","SE":"rökgrå","EN":"smoked grey"},
        "黑白": {"ES":"blanco y negro","FR":"noir et blanc","DE":"schwarz-weiß","IT":"bianco e nero","NL":"zwart-wit","PL":"czarno-biały","PT":"preto e branco","SE":"svart och vit","EN":"black and white"},
        "黑金": {"ES":"negro y dorado","FR":"noir et doré","DE":"schwarz-gold","IT":"nero e oro","NL":"zwart-goud","PL":"czarno-złoty","PT":"preto e dourado","SE":"svart och guld","EN":"black and gold"},
        "白金": {"ES":"blanco y dorado","FR":"blanc et doré","DE":"weiß-gold","IT":"bianco e oro","NL":"wit-goud","PL":"biało-złoty","PT":"branco e dourado","SE":"vit och guld","EN":"white and gold"},
    },
    "产品类型": {
        "壁灯": {"ES":"aplique de pared","FR":"applique murale","DE":"Wandleuchte","IT":"applique da parete","NL":"wandlamp","PL":"kinkiet","PT":"aplique de parede","SE":"vägglampa","EN":"wall light"},
        "浴室壁灯": {"ES":"aplique de baño","FR":"applique de salle de bain","DE":"Bad Wandleuchte","IT":"applique bagno","NL":"badkamer wandlamp","PL":"kinkiet łazienkowy","PT":"aplique de casa de banho","SE":"badrumsvägglampa","EN":"bathroom wall light"},
        "画灯": {"ES":"aplique para cuadro","FR":"applique pour tableau","DE":"Bilderleuchte","IT":"lampada per quadri","NL":"schilderijlamp","PL":"lampa do obrazów","PT":"aplique para quadro","SE":"tavellampa","EN":"picture light"},
        "镜前灯": {"ES":"aplique de espejo","FR":"applique miroir","DE":"Spiegelleuchte","IT":"luce per specchio","NL":"spiegellamp","PL":"lampa nad lustro","PT":"luz de espelho","SE":"spegellampa","EN":"mirror light"},
        "吊灯": {"ES":"lámpara colgante","FR":"suspension","DE":"Pendelleuchte","IT":"lampada a sospensione","NL":"hanglamp","PL":"lampa wisząca","PT":"candeeiro suspenso","SE":"pendellampa","EN":"pendant light"},
        "设计吊灯": {"ES":"lámpara colgante de diseño","FR":"suspension design","DE":"Design-Pendelleuchte","IT":"lampada a sospensione design","NL":"design hanglamp","PL":"designerska lampa wisząca","PT":"candeeiro suspenso de design","SE":"designpendellampa","EN":"designer pendant light"},
        "吸顶灯": {"ES":"lámpara de techo","FR":"plafonnier","DE":"Deckenleuchte","IT":"plafoniera","NL":"plafondlamp","PL":"lampa sufitowa","PT":"plafon","SE":"taklampa","EN":"ceiling light"},
        "Plafón": {"ES":"plafón","FR":"plafonnier","DE":"Deckenleuchte","IT":"plafoniera","NL":"plafondlamp","PL":"plafon","PT":"plafon","SE":"plafondlampa","EN":"ceiling light"},
        "落地灯": {"ES":"lámpara de pie","FR":"lampadaire","DE":"Stehleuchte","IT":"lampada da terra","NL":"vloerlamp","PL":"lampa podłogowa","PT":"candeeiro de pé","SE":"golvlampa","EN":"floor lamp"},
        "设计落地灯": {"ES":"lámpara de pie de diseño","FR":"lampadaire design","DE":"Design-Stehleuchte","IT":"lampada da terra design","NL":"design vloerlamp","PL":"designerska lampa podłogowa","PT":"candeeiro de pé de design","SE":"designgolvlampa","EN":"designer floor lamp"},
        "台灯": {"ES":"lámpara de mesa","FR":"lampe de table","DE":"Tischlampe","IT":"lampada da tavolo","NL":"tafellamp","PL":"lampka stołowa","PT":"candeeiro de mesa","SE":"bordslampa","EN":"table lamp"},
        "户外投光灯": {"ES":"proyector LED exterior","FR":"projecteur LED extérieur","DE":"LED Außenstrahler","IT":"faretto LED da esterno","NL":"LED buitenstraler","PL":"naświetlacz LED zewnętrzny","PT":"projetor LED exterior","SE":"LED-strålkastare utomhus","EN":"outdoor LED floodlight"},
        "户外壁灯": {"ES":"aplique exterior","FR":"applique extérieure","DE":"Außenwandleuchte","IT":"applique da esterno","NL":"buitenwandlamp","PL":"kinkiet zewnętrzny","PT":"aplique exterior","SE":"utomhusvägglampa","EN":"outdoor wall light"},
        "户外柱灯/路灯": {"ES":"baliza exterior","FR":"borne lumineuse extérieure","DE":"Außenpollerleuchte","IT":"lampioncino da esterno","NL":"buitenpaal lamp","PL":"słupek ogrodowy","PT":"balizador exterior","SE":"pollarlampa utomhus","EN":"outdoor bollard light"},
        "灯串": {"ES":"guirnalda de luces","FR":"guirlande lumineuse","DE":"Lichterkette","IT":"catena luminosa","NL":"lichtslinger","PL":"girlanda świetlna","PT":"grinalda de luzes","SE":"ljusslinga","EN":"string lights"},
        "LED灯带": {"ES":"tira LED","FR":"ruban LED","DE":"LED-Streifen","IT":"striscia LED","NL":"LED-strip","PL":"taśma LED","PT":"fita LED","SE":"LED-list","EN":"LED strip light"},
        "室内LED灯带": {"ES":"tira LED interior","FR":"ruban LED intérieur","DE":"LED-Streifen innen","IT":"striscia LED interna","NL":"LED-strip binnen","PL":"taśma LED wewnętrzna","PT":"fita LED interior","SE":"LED-list inomhus","EN":"indoor LED strip light"},
        "户外LED灯带": {"ES":"tira LED exterior","FR":"ruban LED extérieur","DE":"LED-Streifen außen","IT":"striscia LED da esterno","NL":"LED-strip buiten","PL":"taśma LED zewnętrzna","PT":"fita LED exterior","SE":"LED-list utomhus","EN":"outdoor LED strip light"},
        "嵌入式筒灯": {"ES":"foco empotrable","FR":"spot encastrable","DE":"Einbaustrahler","IT":"faretto da incasso","NL":"inbouwspot","PL":"oprawa wpuszczana","PT":"foco de encastrar","SE":"infälld spotlight","EN":"recessed spotlight"},
        "厨房/衣柜筒灯": {"ES":"foco para cocina y armario","FR":"spot pour cuisine et placard","DE":"Spot für Küche und Schrank","IT":"faretto per cucina e armadio","NL":"spot voor keuken en kast","PL":"spot do kuchni i szafy","PT":"foco para cozinha e armário","SE":"spot för kök och skåp","EN":"kitchen and cabinet spotlight"},
        "射灯": {"ES":"foco orientable","FR":"spot orientable","DE":"verstellbarer Spot","IT":"faretto orientabile","NL":"richtbare spot","PL":"reflektor regulowany","PT":"foco orientável","SE":"justerbar spot","EN":"adjustable spotlight"},
        "轨道灯": {"ES":"foco de carril","FR":"spot sur rail","DE":"Schienenstrahler","IT":"faretto a binario","NL":"railspot","PL":"reflektor szynowy","PT":"foco de calha","SE":"skenstrålkastare","EN":"track spotlight"},
        "LED面板灯": {"ES":"panel LED","FR":"panneau LED","DE":"LED-Panel","IT":"pannello LED","NL":"LED-paneel","PL":"panel LED","PT":"painel LED","SE":"LED-panel","EN":"LED panel light"},
        "线性灯/灯管": {"ES":"regleta LED","FR":"réglette LED","DE":"LED-Lichtleiste","IT":"plafoniera lineare LED","NL":"LED lichtbalk","PL":"oprawa liniowa LED","PT":"régua LED","SE":"LED-armatur","EN":"LED batten light"},
        "应急灯": {"ES":"luz de emergencia","FR":"éclairage de secours","DE":"Notleuchte","IT":"luce di emergenza","NL":"noodverlichting","PL":"oświetlenie awaryjne","PT":"luz de emergência","SE":"nödbelysning","EN":"emergency light"},
        "夜灯/感应灯": {"ES":"luz nocturna con sensor","FR":"veilleuse avec capteur","DE":"Nachtlicht mit Sensor","IT":"luce notturna con sensore","NL":"nachtlamp met sensor","PL":"lampka nocna z czujnikiem","PT":"luz noturna com sensor","SE":"nattlampa med sensor","EN":"sensor night light"},
        "带灯风扇": {"ES":"ventilador de techo con luz","FR":"ventilateur de plafond avec lumière","DE":"Deckenventilator mit Licht","IT":"ventilatore da soffitto con luce","NL":"plafondventilator met lamp","PL":"wentylator sufitowy z oświetleniem","PT":"ventoinha de teto com luz","SE":"takfläkt med lampa","EN":"ceiling fan with light"},
        "灯泡": {"ES":"bombilla","FR":"ampoule","DE":"Glühbirne","IT":"lampadina","NL":"lamp","PL":"żarówka","PT":"lâmpada","SE":"glödlampa","EN":"bulb"},
        "灯泡套装": {"ES":"pack de bombillas","FR":"lot d'ampoules","DE":"Glühbirnen-Set","IT":"set di lampadine","NL":"set lampen","PL":"zestaw żarówek","PT":"pack de lâmpadas","SE":"set med lampor","EN":"bulb pack"},
        "LED灯管": {"ES":"tubo LED","FR":"tube LED","DE":"LED-Röhre","IT":"tubo LED","NL":"LED-buis","PL":"świetlówka LED","PT":"tubo LED","SE":"LED-lysrör","EN":"LED tube"},
        "电线带开关插头": {"ES":"cable con enchufe e interruptor","FR":"câble avec prise et interrupteur","DE":"Kabel mit Stecker und Schalter","IT":"cavo con spina e interruttore","NL":"kabel met stekker en schakelaar","PL":"przewód z wtyczką i przełącznikiem","PT":"cabo com ficha e interruptor","SE":"kabel med kontakt och strömbrytare","EN":"cable with plug and switch"},
        "吊灯配件": {"ES":"accesorio para lámpara colgante","FR":"accessoire pour suspension","DE":"Zubehör für Pendelleuchte","IT":"accessorio per lampada a sospensione","NL":"accessoire voor hanglamp","PL":"akcesorium do lampy wiszącej","PT":"acessório para candeeiro suspenso","SE":"tillbehör för pendellampa","EN":"pendant light accessory"},
        "吸顶盘/顶盘": {"ES":"florón de techo","FR":"rosace de plafond","DE":"Deckenbaldachin","IT":"rosone da soffitto","NL":"plafondkap","PL":"rozeta sufitowa","PT":"florão de teto","SE":"takrosett","EN":"ceiling rose"},
        "LED变压器": {"ES":"transformador LED","FR":"transformateur LED","DE":"LED-Trafo","IT":"trasformatore LED","NL":"LED-transformator","PL":"transformator LED","PT":"transformador LED","SE":"LED-transformator","EN":"LED transformer"},
    },
    "材质": {
        "钢": {"ES":"acero","FR":"acier","DE":"Stahl","IT":"acciaio","NL":"staal","PL":"stal","PT":"aço","SE":"stål","EN":"steel"},
        "铝": {"ES":"aluminio","FR":"aluminium","DE":"Aluminium","IT":"alluminio","NL":"aluminium","PL":"aluminium","PT":"alumínio","SE":"aluminium","EN":"aluminium"},
        "铁": {"ES":"hierro","FR":"fer","DE":"Eisen","IT":"ferro","NL":"ijzer","PL":"żelazo","PT":"ferro","SE":"järn","EN":"iron"},
        "金属": {"ES":"metal","FR":"métal","DE":"Metall","IT":"metallo","NL":"metaal","PL":"metal","PT":"metal","SE":"metall","EN":"metal"},
        "木": {"ES":"madera","FR":"bois","DE":"Holz","IT":"legno","NL":"hout","PL":"drewno","PT":"madeira","SE":"trä","EN":"wood"},
        "玻璃": {"ES":"vidrio","FR":"verre","DE":"Glas","IT":"vetro","NL":"glas","PL":"szkło","PT":"vidro","SE":"glas","EN":"glass"},
        "水晶": {"ES":"cristal","FR":"cristal","DE":"Kristall","IT":"cristallo","NL":"kristal","PL":"kryształ","PT":"cristal","SE":"kristall","EN":"crystal"},
        "藤编": {"ES":"ratán","FR":"rotin","DE":"Rattan","IT":"rattan","NL":"rotan","PL":"rattan","PT":"rattan","SE":"rotting","EN":"rattan"},
        "竹": {"ES":"bambú","FR":"bambou","DE":"Bambus","IT":"bambù","NL":"bamboe","PL":"bambus","PT":"bambu","SE":"bambu","EN":"bamboo"},
        "布艺": {"ES":"tela","FR":"tissu","DE":"Stoff","IT":"tessuto","NL":"stof","PL":"tkanina","PT":"tecido","SE":"tyg","EN":"fabric"},
        "亚克力": {"ES":"acrílico","FR":"acrylique","DE":"Acryl","IT":"acrilico","NL":"acryl","PL":"akryl","PT":"acrílico","SE":"akryl","EN":"acrylic"},
    },
    "灯头": {
        "E27": {lang:"E27" for lang in LANGS}, "E14": {lang:"E14" for lang in LANGS}, "GU10": {lang:"GU10" for lang in LANGS},
        "G9": {lang:"G9" for lang in LANGS}, "G4": {lang:"G4" for lang in LANGS}, "GX53": {lang:"GX53" for lang in LANGS},
        "LED integrado": {"ES":"LED integrado","FR":"LED intégré","DE":"integrierte LED","IT":"LED integrato","NL":"geïntegreerde LED","PL":"zintegrowane LED","PT":"LED integrado","SE":"integrerad LED","EN":"integrated LED"},
        "Sin portalámparas": {"ES":"sin portalámparas","FR":"sans douille","DE":"ohne Fassung","IT":"senza portalampada","NL":"zonder fitting","PL":"bez oprawki","PT":"sem casquilho","SE":"utan sockel","EN":"without lamp holder"},
    },
    "安装方式": {
        "壁挂": {"ES":"montaje en pared","FR":"montage mural","DE":"Wandmontage","IT":"montaggio a parete","NL":"wandmontage","PL":"montaż ścienny","PT":"montagem na parede","SE":"väggmontering","EN":"wall mounted"},
        "吊装": {"ES":"instalación colgante","FR":"suspension","DE":"hängende Montage","IT":"installazione sospesa","NL":"hangmontage","PL":"montaż wiszący","PT":"instalação suspensa","SE":"hängande montering","EN":"suspended installation"},
        "吸顶": {"ES":"montaje en techo","FR":"montage au plafond","DE":"Deckenmontage","IT":"montaggio a soffitto","NL":"plafondmontage","PL":"montaż sufitowy","PT":"montagem no teto","SE":"takmontering","EN":"ceiling mounted"},
        "嵌入式": {"ES":"instalación empotrada","FR":"installation encastrée","DE":"Einbaumontage","IT":"installazione a incasso","NL":"inbouwmontage","PL":"montaż wpuszczany","PT":"instalação embutida","SE":"infälld montering","EN":"recessed installation"},
        "插电使用": {"ES":"con cable y enchufe","FR":"avec câble et prise","DE":"mit Kabel und Stecker","IT":"con cavo e spina","NL":"met kabel en stekker","PL":"z przewodem i wtyczką","PT":"com cabo e ficha","SE":"med kabel och kontakt","EN":"with cable and plug"},
        "轨道安装": {"ES":"montaje en carril","FR":"montage sur rail","DE":"Schienenmontage","IT":"montaggio su binario","NL":"railmontage","PL":"montaż szynowy","PT":"montagem em calha","SE":"skenmontering","EN":"track mounted"},
    },
    "室内/室外": {
        "室内": {"ES":"interior","FR":"intérieur","DE":"Innenbereich","IT":"interni","NL":"binnen","PL":"wewnętrzne","PT":"interior","SE":"inomhus","EN":"indoor"},
        "室外": {"ES":"exterior","FR":"extérieur","DE":"Außenbereich","IT":"esterni","NL":"buiten","PL":"zewnętrzne","PT":"exterior","SE":"utomhus","EN":"outdoor"},
        "室内/室外": {"ES":"interior y exterior","FR":"intérieur et extérieur","DE":"innen und außen","IT":"interni ed esterni","NL":"binnen en buiten","PL":"wewnątrz i na zewnątrz","PT":"interior e exterior","SE":"inomhus och utomhus","EN":"indoor and outdoor"},
    },
    "是否含灯泡": {
        "否": {"ES":"bombilla no incluida","FR":"ampoule non incluse","DE":"Leuchtmittel nicht enthalten","IT":"lampadina non inclusa","NL":"lamp niet inbegrepen","PL":"żarówka brak w zestawie","PT":"lâmpada não incluída","SE":"ljuskälla ingår ej","EN":"bulb not included"},
        "是": {"ES":"bombilla incluida","FR":"ampoule incluse","DE":"Leuchtmittel enthalten","IT":"lampadina inclusa","NL":"lamp inbegrepen","PL":"żarówka w zestawie","PT":"lâmpada incluída","SE":"ljuskälla ingår","EN":"bulb included"},
        "不适用（LED集成）": {"ES":"LED integrado","FR":"LED intégré","DE":"integrierte LED","IT":"LED integrato","NL":"geïntegreerde LED","PL":"zintegrowane LED","PT":"LED integrado","SE":"integrerad LED","EN":"integrated LED"},
    },
    "风格": {
        "现代": {"ES":"moderno","FR":"moderne","DE":"modern","IT":"moderno","NL":"modern","PL":"nowoczesny","PT":"moderno","SE":"modern","EN":"modern"},
        "极简": {"ES":"minimalista","FR":"minimaliste","DE":"minimalistisch","IT":"minimalista","NL":"minimalistisch","PL":"minimalistyczny","PT":"minimalista","SE":"minimalistisk","EN":"minimalist"},
        "北欧": {"ES":"nórdico","FR":"nordique","DE":"skandinavisch","IT":"nordico","NL":"Scandinavisch","PL":"skandynawski","PT":"nórdico","SE":"nordisk","EN":"Nordic"},
        "复古": {"ES":"vintage","FR":"vintage","DE":"Vintage","IT":"vintage","NL":"vintage","PL":"vintage","PT":"vintage","SE":"vintage","EN":"vintage"},
        "Vintage": {"ES":"vintage","FR":"vintage","DE":"Vintage","IT":"vintage","NL":"vintage","PL":"vintage","PT":"vintage","SE":"vintage","EN":"vintage"},
        "Retro Cinema": {"ES":"retro estilo cine","FR":"rétro style cinéma","DE":"Retro-Kinostil","IT":"stile cinema rétro","NL":"retro bioscoopstijl","PL":"retro styl kinowy","PT":"retro estilo cinema","SE":"retro biografstil","EN":"retro cinema style"},
        "工业": {"ES":"industrial","FR":"industriel","DE":"industriell","IT":"industriale","NL":"industrieel","PL":"industrialny","PT":"industrial","SE":"industriell","EN":"industrial"},
        "Wabi-sabi": {"ES":"wabi-sabi","FR":"wabi-sabi","DE":"Wabi-Sabi","IT":"wabi-sabi","NL":"wabi-sabi","PL":"wabi-sabi","PT":"wabi-sabi","SE":"wabi-sabi","EN":"wabi-sabi"},
        "经典": {"ES":"clásico","FR":"classique","DE":"klassisch","IT":"classico","NL":"klassiek","PL":"klasyczny","PT":"clássico","SE":"klassisk","EN":"classic"},
    },
    "适用空间": {
        "卧室": {"ES":"dormitorio","FR":"chambre","DE":"Schlafzimmer","IT":"camera da letto","NL":"slaapkamer","PL":"sypialnia","PT":"quarto","SE":"sovrum","EN":"bedroom"},
        "客厅": {"ES":"salón","FR":"salon","DE":"Wohnzimmer","IT":"soggiorno","NL":"woonkamer","PL":"salon","PT":"sala","SE":"vardagsrum","EN":"living room"},
        "酒店": {"ES":"hotel","FR":"hôtel","DE":"Hotel","IT":"hotel","NL":"hotel","PL":"hotel","PT":"hotel","SE":"hotell","EN":"hotel"},
        "厨房岛台": {"ES":"isla de cocina","FR":"îlot de cuisine","DE":"Kücheninsel","IT":"isola cucina","NL":"kookeiland","PL":"wyspa kuchenna","PT":"ilha de cozinha","SE":"köksö","EN":"kitchen island"},
        "餐厅": {"ES":"comedor","FR":"salle à manger","DE":"Esszimmer","IT":"sala da pranzo","NL":"eetkamer","PL":"jadalnia","PT":"sala de jantar","SE":"matsal","EN":"dining room"},
        "浴室": {"ES":"baño","FR":"salle de bain","DE":"Bad","IT":"bagno","NL":"badkamer","PL":"łazienka","PT":"casa de banho","SE":"badrum","EN":"bathroom"},
    },
}


# 补充新增字段和常用枚举的多语言映射。
VALUE_MAP.setdefault("方向调节", {}).update({
    "不可调": {"ES":"no orientable","FR":"non orientable","DE":"nicht verstellbar","IT":"non orientabile","NL":"niet verstelbaar","PL":"bez regulacji","PT":"não orientável","SE":"ej justerbar","EN":"not adjustable"},
    "轻微角度调整": {"ES":"ligera orientación","FR":"légère orientation","DE":"leichte Ausrichtung","IT":"leggera orientabilità","NL":"licht verstelbaar","PL":"lekka regulacja","PT":"ligeira orientação","SE":"lätt justering","EN":"slightly adjustable"},
    "可定向调节": {"ES":"orientable","FR":"orientable","DE":"schwenkbar","IT":"orientabile","NL":"richtbaar","PL":"regulowany","PT":"orientável","SE":"riktbar","EN":"adjustable"},
    "350°旋转": {"ES":"orientable 350°","FR":"orientable à 350°","DE":"350° schwenkbar","IT":"orientabile a 350°","NL":"350° draaibaar","PL":"obrotowy 350°","PT":"orientável 350°","SE":"vridbar 350°","EN":"350° rotatable"},
    "多角度调节": {"ES":"orientable en múltiples ángulos","FR":"orientable multi-angle","DE":"mehrwinklig verstellbar","IT":"orientabile multi-angolo","NL":"meerdere hoeken verstelbaar","PL":"regulacja wielokątowa","PT":"orientável em vários ângulos","SE":"justerbar i flera vinklar","EN":"multi-angle adjustable"},
})
VALUE_MAP.setdefault("方向调节", {}).update({
    "高自由度多角度调节": {"ES":"orientable 360°","FR":"orientable à 360°","DE":"360° drehbar","IT":"orientabile a 360°","NL":"360° draaibaar","PL":"obrotowy 360°","PT":"orientável 360°","SE":"360° vridbar","EN":"360° adjustable"}
})
VALUE_MAP.setdefault("安装方式", {}).update({
    "台面": {"ES":"de sobremesa","FR":"à poser","DE":"Tischaufstellung","IT":"da appoggio","NL":"tafelmodel","PL":"na biurko","PT":"de mesa","SE":"för bord","EN":"tabletop"},
    "落地": {"ES":"de pie","FR":"sur pied","DE":"stehend","IT":"da terra","NL":"staand","PL":"stojąca","PT":"de pé","SE":"stående","EN":"floor standing"}
})
VALUE_MAP.setdefault("光色调节", {}).update({
    "无": {lang:"" for lang in LANGS},
    "三档CCT 3000K/4000K/6000K": {"ES":"CCT 3000K/4000K/6000K","FR":"CCT 3000K/4000K/6000K","DE":"CCT 3000K/4000K/6000K","IT":"CCT 3000K/4000K/6000K","NL":"CCT 3000K/4000K/6000K","PL":"CCT 3000K/4000K/6000K","PT":"CCT 3000K/4000K/6000K","SE":"CCT 3000K/4000K/6000K","EN":"CCT 3000K/4000K/6000K"},
    "CCT可调": {"ES":"CCT ajustable","FR":"CCT réglable","DE":"einstellbare Farbtemperatur","IT":"CCT regolabile","NL":"instelbare kleurtemperatuur","PL":"regulacja CCT","PT":"CCT ajustável","SE":"justerbar färgtemperatur","EN":"adjustable CCT"},
    "无极调色": {"ES":"temperatura de color regulable sin pasos","FR":"température de couleur réglable en continu","DE":"stufenlose Farbtemperatureinstellung","IT":"temperatura colore regolabile continua","NL":"traploos instelbare kleurtemperatuur","PL":"płynna regulacja barwy","PT":"temperatura de cor ajustável contínua","SE":"steglöst justerbar färgtemperatur","EN":"stepless colour temperature adjustment"},
})
VALUE_MAP.setdefault("亮度调节", {}).update({
    "无": {"ES":"sin regulación de intensidad","FR":"sans variation d'intensité","DE":"nicht dimmbar","IT":"non dimmerabile","NL":"niet dimbaar","PL":"bez ściemniania","PT":"sem regulação de intensidade","SE":"ej dimbar","EN":"not dimmable"},
    "可调亮度": {"ES":"intensidad regulable","FR":"intensité réglable","DE":"dimmbar","IT":"luminosità regolabile","NL":"dimbaar","PL":"ściemnialny","PT":"intensidade regulável","SE":"dimbar","EN":"dimmable"},
    "未提供": {lang:"" for lang in LANGS},
})
VALUE_MAP.setdefault("控制方式", {}).update({
    "未提供": {lang:"" for lang in LANGS},
    "按钮": {"ES":"botón","FR":"bouton","DE":"Taste","IT":"pulsante","NL":"knop","PL":"przycisk","PT":"botão","SE":"knapp","EN":"button"},
    "拨码开关": {"ES":"selector","FR":"sélecteur","DE":"Schalter","IT":"selettore","NL":"schakelaar","PL":"przełącznik","PT":"seletor","SE":"väljare","EN":"selector switch"},
    "触控": {"ES":"control táctil","FR":"commande tactile","DE":"Touch-Steuerung","IT":"controllo touch","NL":"touchbediening","PL":"sterowanie dotykowe","PT":"controlo tátil","SE":"touchkontroll","EN":"touch control"},
    "遥控": {"ES":"mando a distancia","FR":"télécommande","DE":"Fernbedienung","IT":"telecomando","NL":"afstandsbediening","PL":"pilot","PT":"controlo remoto","SE":"fjärrkontroll","EN":"remote control"},
})

VALUE_MAP.setdefault("是否LED", {}).update({
    "否": {"ES":"no LED integrado","FR":"non LED intégré","DE":"keine integrierte LED","IT":"non LED integrato","NL":"geen geïntegreerde LED","PL":"bez zintegrowanego LED","PT":"sem LED integrado","SE":"ej integrerad LED","EN":"not integrated LED"},
    "是": {"ES":"LED","FR":"LED","DE":"LED","IT":"LED","NL":"LED","PL":"LED","PT":"LED","SE":"LED","EN":"LED"},
    "LED集成": {"ES":"LED integrado","FR":"LED intégré","DE":"integrierte LED","IT":"LED integrato","NL":"geïntegreerde LED","PL":"zintegrowane LED","PT":"LED integrado","SE":"integrerad LED","EN":"integrated LED"},
    "兼容LED灯泡": {"ES":"compatible con bombillas LED","FR":"compatible avec ampoules LED","DE":"kompatibel mit LED-Leuchtmitteln","IT":"compatibile con lampadine LED","NL":"compatibel met LED-lampen","PL":"kompatybilny z żarówkami LED","PT":"compatível com lâmpadas LED","SE":"kompatibel med LED-lampor","EN":"compatible with LED bulbs"},
})
VALUE_MAP.setdefault("用途标签", {}).update({
    "床头阅读": {"ES":"lectura en cabecero","FR":"lecture au chevet","DE":"Lesen am Bett","IT":"lettura a letto","NL":"lezen bij het bed","PL":"czytanie przy łóżku","PT":"leitura na cabeceira","SE":"läsning vid sängen","EN":"bedside reading"},
    "酒店客房": {"ES":"habitación de hotel","FR":"chambre d'hôtel","DE":"Hotelzimmer","IT":"camera d'hotel","NL":"hotelkamer","PL":"pokój hotelowy","PT":"quarto de hotel","SE":"hotellrum","EN":"hotel room"},
    "USB充电": {"ES":"carga USB","FR":"charge USB","DE":"USB-Laden","IT":"ricarica USB","NL":"USB opladen","PL":"ładowanie USB","PT":"carregamento USB","SE":"USB-laddning","EN":"USB charging"},
    "功能型壁灯": {"ES":"aplique funcional","FR":"applique fonctionnelle","DE":"funktionale Wandleuchte","IT":"applique funzionale","NL":"functionele wandlamp","PL":"funkcjonalny kinkiet","PT":"aplique funcional","SE":"funktionell vägglampa","EN":"functional wall light"},
    "收纳托盘": {"ES":"bandeja integrada","FR":"plateau intégré","DE":"integrierte Ablage","IT":"vassoio integrato","NL":"geïntegreerd plateau","PL":"zintegrowana półka","PT":"bandeja integrada","SE":"integrerad hylla","EN":"integrated tray"},
    "阅读角": {"ES":"rincón de lectura","FR":"coin lecture","DE":"Leseecke","IT":"angolo lettura","NL":"leeshoek","PL":"kącik do czytania","PT":"canto de leitura","SE":"läshörna","EN":"reading corner"},
    "客厅辅助照明": {"ES":"iluminación auxiliar de salón","FR":"éclairage d'appoint du salon","DE":"Zusatzbeleuchtung im Wohnzimmer","IT":"illuminazione ausiliaria soggiorno","NL":"extra verlichting woonkamer","PL":"oświetlenie dodatkowe salonu","PT":"iluminação auxiliar da sala","SE":"extra belysning i vardagsrum","EN":"living room accent lighting"},
    "卧室氛围灯": {"ES":"luz ambiental de dormitorio","FR":"lumière d'ambiance chambre","DE":"Stimmungslicht Schlafzimmer","IT":"luce d'atmosfera camera","NL":"sfeerverlichting slaapkamer","PL":"światło nastrojowe sypialni","PT":"luz ambiente de quarto","SE":"stämningsbelysning sovrum","EN":"bedroom ambient light"},
})


# V14.2 补充：避免“床头/书房/CCT”等中文残留到多语言标题和字段卡。
VALUE_MAP.setdefault("适用空间", {}).update({
    "床头": {"ES":"cabecero","FR":"chevet","DE":"Bettbereich","IT":"comodino","NL":"bedzijde","PL":"przy łóżku","PT":"cabeceira","SE":"sängplats","EN":"bedside"},
    "书房": {"ES":"estudio","FR":"bureau","DE":"Arbeitszimmer","IT":"studio","NL":"werkkamer","PL":"gabinet","PT":"escritório","SE":"arbetsrum","EN":"study room"},
    "公寓": {"ES":"apartamento","FR":"appartement","DE":"Wohnung","IT":"appartamento","NL":"appartement","PL":"apartament","PT":"apartamento","SE":"lägenhet","EN":"apartment"},
    "走廊": {"ES":"pasillo","FR":"couloir","DE":"Flur","IT":"corridoio","NL":"gang","PL":"korytarz","PT":"corredor","SE":"korridor","EN":"hallway"},
    "办公室": {"ES":"oficina","FR":"bureau","DE":"Büro","IT":"ufficio","NL":"kantoor","PL":"biuro","PT":"escritório","SE":"kontor","EN":"office"},
    "商业空间": {"ES":"espacio comercial","FR":"espace commercial","DE":"Gewerberaum","IT":"spazio commerciale","NL":"commerciële ruimte","PL":"przestrzeń komercyjna","PT":"espaço comercial","SE":"kommersiellt utrymme","EN":"commercial space"},
    "阅读角": {"ES":"rincón de lectura","FR":"coin lecture","DE":"Leseecke","IT":"angolo lettura","NL":"leeshoek","PL":"kącik do czytania","PT":"canto de leitura","SE":"läshörna","EN":"reading corner"},
})
VALUE_MAP.setdefault("光色调节", {}).update({
    "三档CCT 3000K、4000K、6000K": {"ES":"CCT 3000K/4000K/6000K","FR":"CCT 3000K/4000K/6000K","DE":"CCT 3000K/4000K/6000K","IT":"CCT 3000K/4000K/6000K","NL":"CCT 3000K/4000K/6000K","PL":"CCT 3000K/4000K/6000K","PT":"CCT 3000K/4000K/6000K","SE":"CCT 3000K/4000K/6000K","EN":"CCT 3000K/4000K/6000K"},
    "三档CCT 3000K, 4000K, 6000K": {"ES":"CCT 3000K/4000K/6000K","FR":"CCT 3000K/4000K/6000K","DE":"CCT 3000K/4000K/6000K","IT":"CCT 3000K/4000K/6000K","NL":"CCT 3000K/4000K/6000K","PL":"CCT 3000K/4000K/6000K","PT":"CCT 3000K/4000K/6000K","SE":"CCT 3000K/4000K/6000K","EN":"CCT 3000K/4000K/6000K"},
})

TRAILING_BAD = {"and", "with", "for", "of", "para", "con", "pour", "un", "una", "que", "med", "och", "e", "et", "y", "or", "o", "de", "del", "en", "a", "al", "por", "per", "di", "von", "mit", "voor", "z", "w"}
WATER_TITLE_PHRASES = ["ideal para", "perfecto para", "perfecta para", "perfecto", "ideal", "bonito", "precioso", "elegante y funcional", "para todo tipo de espacios", "de alta calidad"]
TITLE_FORBIDDEN_VALUE_PHRASES = ["bombilla no incluida", "no incluye bombilla", "sin bombilla", "compatible con bombillas", "compatible con bombilla", "compatible con LED", "compatible LED", "incluye bombilla", "bombilla incluida"]
DANGEROUS_PHRASES = ["incluye bombilla", "bombilla incluida", "incluyendo LED", "Edison o tradicionales", "incluyendo led", "incluyendo bombilla", "bombillas incluidas"]

PRODUCT_DEFAULTS = {
    "壁灯": {"安装方式": "壁挂", "室内/室外": "室内", "是否含灯泡": "否", "是否LED": "兼容LED灯泡"},
    "浴室壁灯": {"安装方式": "壁挂", "室内/室外": "室内", "是否含灯泡": "否", "是否LED": "兼容LED灯泡"},
    "吊灯": {"安装方式": "吊装", "室内/室外": "室内", "是否含灯泡": "否", "是否LED": "兼容LED灯泡"},
    "吸顶灯": {"安装方式": "吸顶", "室内/室外": "室内", "是否含灯泡": "否"},
    "落地灯": {"安装方式": "落地", "室内/室外": "室内", "是否含灯泡": "否"},
    "台灯": {"安装方式": "台面", "室内/室外": "室内", "是否含灯泡": "否"},
    "户外投光灯": {"安装方式": "户外固定安装", "室内/室外": "室外", "是否LED": "LED集成", "是否含灯泡": "不适用（LED集成）"},
    "户外壁灯": {"安装方式": "壁挂", "室内/室外": "室外", "是否含灯泡": "否"},
    "户外柱灯/路灯": {"安装方式": "户外固定安装", "室内/室外": "室外", "是否含灯泡": "否"},
    "灯串": {"安装方式": "插电使用", "室内/室外": "室内/室外", "是否LED": "LED集成", "是否含灯泡": "不适用（LED集成）"},
    "LED灯带": {"安装方式": "插电使用", "是否LED": "LED集成", "是否含灯泡": "不适用（LED集成）"},
    "嵌入式筒灯": {"安装方式": "嵌入式", "是否LED": "LED集成", "是否含灯泡": "不适用（LED集成）"},
    "轨道灯": {"安装方式": "轨道安装", "是否含灯泡": "否"},
    "应急灯": {"安装方式": "壁挂", "是否LED": "LED集成", "是否含灯泡": "不适用（LED集成）"},
}

CORE_FACT_FIELDS = [
    "产品类型", "材质", "颜色", "灯头", "风格", "适用空间", "安装方式", "室内/室外", "是否含灯泡", "是否LED", "调节能力"
]
COLOR_PART_FIELDS = ["主色", "灯罩颜色", "底座颜色", "电线颜色", "顶盘颜色", "变体主颜色"]
EXTRA_FACT_FIELDS = ["尺寸", "直径", "高度", "宽度", "最大功率W", "流明lm", "色温K", "IP等级", "是否含遥控", "是否调光", "系列名", "核心卖点1", "核心卖点2", "核心卖点3", "禁用风格词", "特殊禁止写法", "图片注意事项"] + ADJUSTMENT_EXTRA_FIELDS


def init_state() -> None:
    defaults = {
        "model": "gpt-5.4",
        "ai_title_explanations": False,
        "image_analysis_mode": "标准：分析前3张图（推荐）",
        "targets": ALL_TARGETS.copy(),
        "variant_neutral": False,
        "variant_scope": "标题+Search terms",
        "variant_fields": [],
        "variant_terms": "",
        "es_locked": False,
        "max_title": 200,
        "min_title": 160,
        "min_bullet": 180,
        "max_bullet": 260,
        "min_description": 700,
        "max_search_terms": 250,
        "ean": "",
        "sku": "",
        "brand": "Alpinaluz",
        "manual_series_name": "",
        "title_include_series": False,
        "mode": "新手模式",
        "title_final_history": [],
        "title_strategy": "优先优化原始标题",
        "source_quality_mode": "优质原文保留增强（推荐）",
        "reasoning_effort": "medium",
        "title_format_mode": "自然亚马逊标题（推荐）",
        "source_text": "",
        "selected_title_idx": 0,
        "content_safety_strict": True,
        "image_light_effect_required": False,
        "foreign_title_mode": "语义骨架本地化（推荐，快且稳）",
        "multilang_generation_mode": "批量合并生成（推荐，快）",
        "multilang_batch_size": 8,
        "multilang_only_missing": False,
        "sound_notify": True,
        "notify_after_multilang": False,
        "api_usage_log": [],
        "last_title_zh": "",
        "last_title_zh_source": "",
        "export_quality_files": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def normalize_to_list(value: Any) -> List[str]:
    """把 AI 返回的 list、字符串列表、逗号/顿号分隔值统一成列表。"""
    if value is None:
        return []
    if isinstance(value, list):
        raw = value
    else:
        txt = str(value).strip()
        if not txt:
            return []
        # 兼容 "['钢', '铝']" 这种被转成字符串的列表
        try:
            parsed = json.loads(txt.replace("'", '"'))
            if isinstance(parsed, list):
                raw = parsed
            else:
                raw = [txt]
        except Exception:
            raw = re.split(r"[,，、/]+", txt)
    out = []
    for x in raw:
        x = str(x).strip().strip("[]'\"")
        if x and x not in out:
            out.append(x)
    return out


def normalize_field_display(value: Any) -> str:
    vals = normalize_to_list(value)
    return "、".join(vals) if vals else ""


def set_pick_value(label: str, value: Any) -> None:
    if value is None:
        return
    values = normalize_to_list(value)
    if not values:
        return
    mode_key = f"data::{label}__mode"
    val_key = f"data::{label}__val"
    custom_key = f"data::{label}__custom"
    options = FIELD_OPTIONS.get(label, [])

    if label in FIELD_MULTI:
        preset_vals = [v for v in values if v in options]
        if preset_vals and len(preset_vals) == len(values):
            st.session_state[mode_key] = "预设"
            st.session_state[val_key] = preset_vals
            st.session_state[f"data::{label}"] = "、".join(preset_vals)
        else:
            st.session_state[mode_key] = "自定义"
            st.session_state[custom_key] = "、".join(values)
            st.session_state[f"data::{label}"] = "、".join(values)
        return

    value_str = values[0]
    if value_str in options:
        st.session_state[mode_key] = "预设"
        st.session_state[val_key] = value_str
    else:
        st.session_state[mode_key] = "自定义"
        st.session_state[custom_key] = value_str
    st.session_state[f"data::{label}"] = value_str


def raw_input_blob() -> str:
    parts = [
        st.session_state.get("source_text", ""),
        st.session_state.get("manual_title", ""),
        st.session_state.get("manual_series_name", ""),
        st.session_state.get("manual_description", ""),
        st.session_state.get("keywords", ""),
        st.session_state.get("tech_notes", ""),
        " ".join([getattr(f, "name", "") for f in st.session_state.get("uploaded_images", []) or []]),
    ]
    return "\n".join(str(x) for x in parts if x).lower()


def postprocess_facts(facts: Dict[str, Any]) -> Dict[str, Any]:
    """规则层兜底：事实优先，避免 AI 根据图片/旧事实误判 LED/CCT/E27。"""
    facts = dict(facts or {})
    raw_blob = raw_input_blob().lower()
    ai_blob = json.dumps(facts, ensure_ascii=False).lower()
    full_blob = raw_blob + "\n" + ai_blob

    socket_match = re.search(r"\b(e27|e14|gu10|g9|g4|gx53)\b", raw_blob, flags=re.I)
    explicit_integrated_led = any(m in raw_blob for m in [
        "led integrado", "integrated led", "led intégr", "led integr", "内置led", "集成led",
        "módulo led", "modulo led", "chip led", "led 6w", "6w led", "cct", "selector de temperatura", "temperatura de color"
    ])
    traditional_socket_context = bool(socket_match) and any(m in raw_blob for m in [
        "bombilla no incluida", "no incluye bombilla", "compatible con bombillas", "casquillo", "portalámparas", "socket", "douille", "fassung", "attacco"
    ])

    # V14.7: 传统灯头优先级最高。只要原始资料明确 E27/GU10/G9 + 不含灯泡/兼容灯泡，
    # 就不能因为图片或旧缓存把产品误判成 LED integrado / CCT。
    if traditional_socket_context:
        socket = socket_match.group(1).upper()
        facts["灯头"] = socket
        facts["是否LED"] = "兼容LED灯泡"
        facts["是否含灯泡"] = "否"
        facts["色温K"] = ""
        facts["光色调节"] = "无"
        facts["亮度调节"] = "未提供"
    else:
        led_markers_raw = [
            "led integrado", "integrated led", "led intégr", "led integr", "内置led", "集成led",
            "módulo led", "modulo led", "chip led", "6w led", "led 6w"
        ]
        cct_markers_raw = ["cct", "3000k", "4000k", "6000k", "selector de temperatura", "temperatura de color", "色温"]
        is_integrated_led = any(m in raw_blob for m in led_markers_raw) or (any(m in raw_blob for m in cct_markers_raw) and not socket_match)
        if is_integrated_led:
            facts["是否LED"] = "LED集成"
            facts["灯头"] = "LED integrado"
            facts["是否含灯泡"] = "不适用（LED集成）"

    if any(x in raw_blob for x in ["3000k", "4000k", "6000k", "cct", "色温", "temperatura de color"]):
        facts.setdefault("色温K", "3000K/4000K/6000K")
        if not facts.get("光色调节") or facts.get("光色调节") in {"无", ""}:
            facts["光色调节"] = "三档CCT 3000K/4000K/6000K"
        if not re.search(r"dimmable|regulable en intensidad|调亮度|调光|brightness", raw_blob):
            facts["亮度调节"] = "未提供"
    elif facts.get("光色调节") and "CCT" in str(facts.get("光色调节")):
        facts["光色调节"] = "无"
        facts["色温K"] = ""

    if "360" in full_blob or "360°" in full_blob or "360º" in full_blob:
        facts["方向调节"] = "高自由度多角度调节"
        facts["调节能力"] = "高自由度多角度调节"
    elif "350" in full_blob or "350°" in full_blob or "350º" in full_blob:
        facts["方向调节"] = "350°旋转"
        facts["调节能力"] = "可定向调节"
    elif any(x in full_blob for x in ["orientable", "rotatable", "schwenk", "orientável", "可调", "可旋转"]):
        facts.setdefault("方向调节", "可定向调节")
        facts.setdefault("调节能力", "可定向调节")

    if any(x in raw_blob for x in ["foco de cine", "cinematográfico", "estilo cinema", "retro cinema", "trípode", "tripode", "filmspot", "电影", "三脚架"]):
        facts["风格"] = ["Vintage", "Retro Cinema", "工业"]
        facts["禁用风格词"] = "现代、极简、moderno、minimalista"

    if any(x in raw_blob for x in ["usb-c", "usb c", "type-c", "type c", "usb y usb-c", "usb和usb-c"]):
        tags = normalize_to_list(facts.get("用途标签"))
        for t in ["USB充电", "床头阅读", "功能型壁灯"]:
            if t not in tags:
                tags.append(t)
        facts["用途标签"] = "、".join(tags)

    if any(x in raw_blob for x in ["bandeja", "tray", "plateau", "ablage", "hylla", "托盘", "置物", "28cm", "28 cm"]):
        tags = normalize_to_list(facts.get("用途标签"))
        if "收纳托盘" not in tags:
            tags.append("收纳托盘")
        facts["用途标签"] = "、".join(tags)

    styles = normalize_to_list(facts.get("风格"))
    if "现代" in styles and "极简" in normalize_to_list(facts.get("禁用风格词")):
        styles = [x for x in styles if x != "极简"]
    if styles:
        facts["风格"] = styles

    return facts


def apply_pending_facts() -> None:
    pending = st.session_state.pop("pending_apply_facts", None)
    if not pending:
        return
    pending = postprocess_facts(pending)
    st.session_state["fact_suggestions"] = pending
    for label in CORE_FACT_FIELDS:
        if label in pending and pending[label]:
            set_pick_value(label, pending[label])
    for label in COLOR_PART_FIELDS + EXTRA_FACT_FIELDS:
        if label in pending and pending[label] is not None:
            st.session_state[f"fact::{label}"] = normalize_field_display(pending[label])


def get_client():
    key = st.session_state.get("openai_api_key", "").strip()
    if not key:
        return None
    if OpenAI is None:
        raise RuntimeError("缺少 openai 依赖，请先 pip install -r requirements.txt")
    return OpenAI(api_key=key)


def _response_text(resp: Any) -> str:
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



# ------------------------ Token / cost tracking ------------------------
# These are estimated API prices used only for an internal cost dashboard.
# If OpenAI changes pricing, adjust here; the UI labels this as an estimate.
MODEL_PRICES_USD_PER_1M = {
    "gpt-5.5": {"input": 5.00, "output": 30.00},
    "gpt-5.4": {"input": 2.50, "output": 15.00},
    "gpt-5.4-mini": {"input": 0.75, "output": 4.50},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
}

def _get_usage_tokens(resp: Any) -> Tuple[int, int]:
    usage = getattr(resp, "usage", None)
    if usage is None and isinstance(resp, dict):
        usage = resp.get("usage")
    if usage is None:
        return 0, 0
    def pick(obj, *names):
        for n in names:
            if isinstance(obj, dict) and n in obj:
                return obj.get(n) or 0
            if hasattr(obj, n):
                return getattr(obj, n) or 0
        return 0
    inp = pick(usage, "input_tokens", "prompt_tokens")
    out = pick(usage, "output_tokens", "completion_tokens")
    return int(inp or 0), int(out or 0)

def estimate_text_tokens(text: str) -> int:
    # conservative mixed Chinese/Latin estimate; only used when API usage is unavailable
    text = text or ""
    return max(1, int(len(text) / 3.2)) if text else 0

def record_api_usage(label: str, model: str, resp: Any = None, input_hint: str = "", output_hint: str = "", image_count: int = 0) -> None:
    inp, out = _get_usage_tokens(resp) if resp is not None else (0, 0)
    estimated = False
    if not inp and not out:
        inp = estimate_text_tokens(input_hint) + image_count * 1200
        out = estimate_text_tokens(output_hint)
        estimated = True
    base = model if model in MODEL_PRICES_USD_PER_1M else str(model).split(":")[0]
    price = MODEL_PRICES_USD_PER_1M.get(base, MODEL_PRICES_USD_PER_1M.get("gpt-5.4"))
    cost = (inp / 1_000_000) * price["input"] + (out / 1_000_000) * price["output"]
    st.session_state.setdefault("api_usage_log", []).append({
        "label": label, "model": model, "input_tokens": inp, "output_tokens": out,
        "cost": cost, "estimated": estimated, "image_count": image_count,
    })

def usage_totals() -> Dict[str, Any]:
    logs = st.session_state.get("api_usage_log", []) or []
    return {
        "calls": len(logs),
        "input_tokens": sum(int(x.get("input_tokens", 0)) for x in logs),
        "output_tokens": sum(int(x.get("output_tokens", 0)) for x in logs),
        "cost": sum(float(x.get("cost", 0)) for x in logs),
    }

def render_usage_dashboard() -> None:
    totals = usage_totals()
    st.markdown("### Token / 费用仪表盘")
    st.caption("估算值：优先读取 API 返回的 usage；若未返回则按文本长度粗估。用于判断哪里烧钱，不作为最终账单。")
    c1, c2 = st.columns(2)
    c1.metric("本轮调用", totals["calls"])
    c2.metric("估算费用", f"${totals['cost']:.3f}")
    st.caption(f"输入 {totals['input_tokens']:,} tokens / 输出 {totals['output_tokens']:,} tokens")
    logs = st.session_state.get("api_usage_log", [])[-8:]
    if logs:
        with st.expander("查看最近调用明细", expanded=False):
            for x in reversed(logs):
                mark = "估" if x.get("estimated") else "实"
                st.write(f"{mark} · {x.get('label')} · {x.get('model')} · in {x.get('input_tokens'):,} / out {x.get('output_tokens'):,} · ${x.get('cost',0):.3f}")
    if st.button("清空费用统计"):
        st.session_state["api_usage_log"] = []
        st.rerun()

def cheap_title_zh(title: str) -> str:
    if not title.strip():
        return ""
    prompt = f"""请把下面的 Amazon 西班牙标题翻译成简体中文，用一句话解释给中国运营同事看。
要求：只翻译标题事实，不新增卖点，不要解释规则。
标题：{title}
"""
    return llm(prompt, system="You translate marketplace titles into concise Simplified Chinese for internal review.", model_override="gpt-5.4-mini", reasoning_effort_override="medium").strip()

def llm(prompt: str, system: str = "You are a senior Amazon marketplace SEO copywriter for lighting products.", temperature: float = 0.35, model_override: str = None, reasoning_effort_override: str = None) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("请先在左侧输入 OpenAI API Key")
    model = model_override or st.session_state.get("model", "gpt-5.4")
    if str(model).startswith("gpt-5"):
        kwargs = {
            "model": model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
            ],
        }
        effort = reasoning_effort_override or st.session_state.get("reasoning_effort", "high")
        if effort:
            kwargs["reasoning"] = {"effort": effort}
        try:
            resp = client.responses.create(**kwargs)
            out_text = _response_text(resp)
            record_api_usage("文本生成", model, resp, input_hint=system + "\n" + prompt, output_hint=out_text)
            return out_text
        except TypeError:
            kwargs.pop("reasoning", None)
            resp = client.responses.create(**kwargs)
            out_text = _response_text(resp)
            record_api_usage("文本生成", model, resp, input_hint=system + "\n" + prompt, output_hint=out_text)
            return out_text
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    )
    out_text = resp.choices[0].message.content.strip()
    record_api_usage("文本生成", model, resp, input_hint=system + "\n" + prompt, output_hint=out_text)
    return out_text


def llm_multimodal(prompt: str, files: List[Any], system: str = "You identify lighting product facts from text and images.") -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("请先在左侧输入 OpenAI API Key")
    model = st.session_state.get("model", "gpt-5.4")
    if str(model).startswith("gpt-5"):
        content = [{"type": "input_text", "text": prompt}]
        for f in files[:image_analysis_limit()]:
            try:
                data = f.getvalue()
                mime = f.type or "image/jpeg"
                b64 = base64.b64encode(data).decode("utf-8")
                content.append({"type": "input_image", "image_url": f"data:{mime};base64,{b64}"})
            except Exception:
                continue
        kwargs = {
            "model": model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": content},
            ],
            "reasoning": {"effort": st.session_state.get("reasoning_effort", "high")},
        }
        used_images = min(len(files or []), image_analysis_limit())
        try:
            resp = client.responses.create(**kwargs)
        except TypeError:
            kwargs.pop("reasoning", None)
            resp = client.responses.create(**kwargs)
        out_text = _response_text(resp)
        record_api_usage("图片/事实识别", model, resp, input_hint=system + "\n" + prompt, output_hint=out_text, image_count=used_images)
        return out_text
    content = [{"type": "text", "text": prompt}]
    for f in files[:image_analysis_limit()]:
        try:
            data = f.getvalue()
            mime = f.type or "image/jpeg"
            b64 = base64.b64encode(data).decode("utf-8")
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
        except Exception:
            continue
    resp = client.chat.completions.create(
        model=model,
        temperature=0.15,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
    )
    out_text = resp.choices[0].message.content.strip()
    record_api_usage("图片/事实识别", model, resp, input_hint=system + "\n" + prompt, output_hint=out_text, image_count=min(len(files or []), image_analysis_limit()))
    return out_text



def notify_done(message: str = "生成完成") -> None:
    """Browser-side beep + toast after long generation. Autoplay may depend on browser settings, but click-triggered Streamlit actions usually allow it."""
    try:
        st.toast(message)
    except Exception:
        pass
    if not st.session_state.get("sound_notify", True):
        return
    components.html(
        """
        <script>
        (function(){
          try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            const ctx = new AudioContext();
            const o = ctx.createOscillator();
            const g = ctx.createGain();
            o.type = 'sine';
            o.frequency.setValueAtTime(880, ctx.currentTime);
            g.gain.setValueAtTime(0.001, ctx.currentTime);
            g.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + 0.02);
            g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.28);
            o.connect(g); g.connect(ctx.destination);
            o.start(); o.stop(ctx.currentTime + 0.30);
          } catch(e) {}
        })();
        </script>
        """,
        height=0,
        width=0,
    )

def safe_json(raw: str, fallback):
    txt = str(raw or "").strip()
    txt = re.sub(r"^```json|^```|```$", "", txt, flags=re.M).strip()
    try:
        return json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return fallback
        return fallback


def pick_value(label: str, key_prefix: str, help_text: str = "") -> str:
    mode_key = f"{key_prefix}__mode"
    val_key = f"{key_prefix}__val"
    custom_key = f"{key_prefix}__custom"
    options = FIELD_OPTIONS[label]
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "预设"
    mode = st.radio(label, ["预设", "自定义"], horizontal=True, key=mode_key, help=help_text)
    if label in FIELD_MULTI:
        # 多选字段：材质、风格、适用空间。适合复杂产品事实。
        if mode == "预设":
            current = st.session_state.get(val_key, [])
            if isinstance(current, str):
                current = normalize_to_list(current)
            value_list = st.multiselect(f"{label}选项（可多选）", options, default=[x for x in current if x in options], key=val_key)
            value = "、".join(value_list)
        else:
            value = st.text_input(f"{label}自定义（多个用顿号/逗号分隔）", key=custom_key)
    else:
        if mode == "预设":
            value = st.selectbox(f"{label}选项", options, key=val_key)
        else:
            value = st.text_input(f"{label}自定义", key=custom_key)
    st.session_state[key_prefix] = value
    return value


def map_value(field: str, value: Any, lang: str) -> str:
    # CCT 字段不能用 “/” 或逗号简单切开，否则会丢失 3000K。
    raw_text = str(value or "").strip()
    if field == "光色调节":
        if not raw_text:
            return ""
        normalized = raw_text.replace("，", ",").replace("、", ",")
        if "3000" in normalized and "4000" in normalized and "6000" in normalized:
            cct_map = {
                "ES": "CCT 3000K/4000K/6000K",
                "FR": "CCT 3000K/4000K/6000K",
                "DE": "CCT 3000K/4000K/6000K",
                "IT": "CCT 3000K/4000K/6000K",
                "NL": "CCT 3000K/4000K/6000K",
                "PL": "CCT 3000K/4000K/6000K",
                "PT": "CCT 3000K/4000K/6000K",
                "SE": "CCT 3000K/4000K/6000K",
                "EN": "CCT 3000K/4000K/6000K",
            }
            return cct_map.get(lang, "CCT 3000K/4000K/6000K")
        if field in VALUE_MAP and raw_text in VALUE_MAP[field]:
            return VALUE_MAP[field][raw_text].get(lang, raw_text)

    vals = normalize_to_list(value)
    if not vals:
        return ""
    mapped = []
    for v in vals:
        raw_v = str(v).strip()
        if not raw_v:
            continue
        if field in VALUE_MAP and raw_v in VALUE_MAP[field]:
            mv = VALUE_MAP[field][raw_v].get(lang, raw_v)
        else:
            # 非中文自定义值允许保留；中文自定义值如果没有字典映射，不允许进入目标语言标题/字段。
            mv = "" if (lang != "ZH" and has_cjk(raw_v)) else raw_v
        if mv and mv not in mapped:
            mapped.append(mv)
    return ", ".join(mapped)


def get_field(label: str) -> str:
    return st.session_state.get(f"data::{label}", "")


def get_fact(label: str) -> str:
    if label == "系列名":
        return st.session_state.get("manual_series_name", "") or st.session_state.get("fact::系列名", "")
    return st.session_state.get(f"fact::{label}", "")


def get_series_name() -> str:
    return str(st.session_state.get("manual_series_name", "") or st.session_state.get("fact::系列名", "") or "").strip()


def title_should_include_series() -> bool:
    return bool(st.session_state.get("title_include_series", False))


def strip_series_from_title(title: str) -> str:
    """Amazon标题默认不占用系列名位置；系列名保留在字段卡/后台资料。"""
    t = str(title or "")
    if title_should_include_series():
        return t
    series = get_series_name()
    if not series:
        return t
    # 支持 TOURS / Mini Gala 等多词系列名，大小写不敏感。
    # V16.6: do not break descriptive words that happen to equal a series name.
    # Example: series SUNSET should be removed as a standalone model name, but not from
    # "Sunset-Effect Glass Globe", otherwise the title becomes "with -Effect Glass Globe".
    patterns = [re.escape(series)]
    if " " in series:
        patterns.append(re.escape(series.replace(" ", "")))
    series_low = series.strip().lower()
    for pat in patterns:
        if series_low == "sunset":
            t = re.sub(rf"(?i)(?<![A-Za-z0-9]){pat}(?!\s*[- ]?\s*effect)(?![A-Za-z0-9])", "", t)
        else:
            t = re.sub(rf"(?i)(?<![A-Za-z0-9]){pat}(?![A-Za-z0-9])", "", t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r",\s*,", ",", t)
    return t.strip(" ,;-–—")


def has_bare_cm(title: str) -> bool:
    t = str(title or "")
    for m in re.finditer(r"\bcm\b", t, flags=re.I):
        before = t[:m.start()].rstrip()
        if not before or not re.search(r"\d$", before):
            return True
    return False


def remove_bare_cm(title: str) -> str:
    t = str(title or "")
    # 清理 “Ajustable Cm / Adjustable Cm / Regulable Cm” 这种没有具体数字的残片。
    t = re.sub(r"(?i)\b(Ajustable|Regulable|Orientable|Adjustable|Regolabile|Réglable|Verstellbar)\s+cm\b", r"\1", t)
    # 仍然裸露的 cm 直接删除，但保留 94-140 cm / 28 cm 这种合法单位。
    out = []
    last = 0
    for m in re.finditer(r"\bcm\b", t, flags=re.I):
        before = t[:m.start()].rstrip()
        if before and re.search(r"\d$", before):
            continue
        out.append(t[last:m.start()])
        last = m.end()
    if out:
        out.append(t[last:])
        t = "".join(out)
    return re.sub(r"\s+", " ", t).strip(" ,;-–—")


def field_card_lines() -> List[str]:
    rows = []
    fields = ["产品类型", "材质", "颜色", "灯头", "风格", "适用空间", "安装方式", "室内/室外", "是否含灯泡", "是否LED", "方向调节", "光色调节", "亮度调节", "控制方式", "用途标签"]
    for field in fields:
        value = get_field(field) if field in CORE_FACT_FIELDS else get_fact(field)
        if not value:
            continue
        rows.append(f"【{field}】中文：{value}")
        for lang in ["ES", "FR", "DE", "IT", "NL", "PL", "PT", "SE", "EN"]:
            rows.append(f"{lang}：{map_value(field, value, lang)}")
        rows.append("")
    for field in COLOR_PART_FIELDS + [f for f in EXTRA_FACT_FIELDS if f not in ADJUSTMENT_EXTRA_FIELDS]:
        value = get_fact(field)
        if value:
            rows.append(f"【{field}】{value}")
    return rows


def image_exclude_key(file_obj: Any, idx: int) -> str:
    """Return a unique Streamlit widget key for an uploaded image.

    Streamlit file_uploader allows multiple files with the same filename, for example
    image.jpg, image.jpg. Using only file.name as widget key causes
    StreamlitDuplicateElementKey. Include the index and file size to keep keys unique.
    """
    name = getattr(file_obj, "name", f"image_{idx}") or f"image_{idx}"
    size = getattr(file_obj, "size", "")
    return f"exclude_img::{idx}::{name}::{size}"


def image_is_excluded(file_obj: Any, idx: int) -> bool:
    # V16.2 uses unique keys. Keep backward compatibility with old name-only keys
    # for users who already checked exclusions before updating.
    unique_key = image_exclude_key(file_obj, idx)
    legacy_key = f"exclude_img::{getattr(file_obj, 'name', '')}"
    return bool(st.session_state.get(unique_key, st.session_state.get(legacy_key, False)))


def image_names_for_prompt() -> str:
    files = st.session_state.get("uploaded_images", []) or []
    if not files:
        return ""
    excluded = []
    used = []
    for idx, f in enumerate(files):
        name = getattr(f, "name", f"image_{idx}")
        if image_is_excluded(f, idx):
            excluded.append(name)
        else:
            used.append(name)
    out = []
    if used:
        out.append("Used images: " + ", ".join(used))
    if excluded:
        out.append("Excluded images: " + ", ".join(excluded))
    return "\n".join(out)


def image_analysis_limit() -> int:
    mode = st.session_state.get("image_analysis_mode", "标准：分析前3张图（推荐）")
    if str(mode).startswith("快速"):
        return 0
    if str(mode).startswith("完整"):
        return 6
    return 3

def images_for_analysis() -> List[Any]:
    files = st.session_state.get("uploaded_images", []) or []
    return [f for idx, f in enumerate(files) if not image_is_excluded(f, idx)]


def facts_for_prompt(lang: str = "ES") -> str:
    facts = {
        "Brand": st.session_state.get("brand", "Alpinaluz") or "Alpinaluz",
        "SKU": st.session_state.get("sku", ""),
        "EAN": st.session_state.get("ean", ""),
        "Product type": map_value("产品类型", get_field("产品类型"), lang),
        "Material": map_value("材质", get_field("材质"), lang),
        "Main variant color": map_value("颜色", get_field("颜色"), lang),
        "Socket / light source": map_value("灯头", get_field("灯头"), lang),
        "Style": map_value("风格", get_field("风格"), lang),
        "Use space": map_value("适用空间", get_field("适用空间"), lang),
        "Mounting": map_value("安装方式", get_field("安装方式"), lang),
        "Indoor/Outdoor": map_value("室内/室外", get_field("室内/室外"), lang),
        "Bulb included": map_value("是否含灯泡", get_field("是否含灯泡"), lang),
        "LED status": map_value("是否LED", get_field("是否LED"), lang) or get_field("是否LED"),
        "Physical direction adjustment": map_value("方向调节", get_fact("方向调节"), lang) or get_field("调节能力"),
        "CCT / colour temperature adjustment": map_value("光色调节", get_fact("光色调节"), lang),
        "Brightness dimming": map_value("亮度调节", get_fact("亮度调节"), lang),
        "Control method": map_value("控制方式", get_fact("控制方式"), lang),
        "Use tags": map_value("用途标签", get_fact("用途标签"), lang) or get_fact("用途标签"),
        "Variant scope": st.session_state.get("variant_scope", ""),
        "Variant terms": st.session_state.get("variant_terms", ""),
        "Source text": st.session_state.get("source_text", ""),
        "Manual title": st.session_state.get("manual_title", ""),
        "Manual description": st.session_state.get("manual_description", ""),
        "SEO keywords": st.session_state.get("keywords", ""),
        "Technical notes": st.session_state.get("tech_notes", ""),
        "Image notes": image_names_for_prompt(),
    }
    for f in COLOR_PART_FIELDS + [x for x in EXTRA_FACT_FIELDS if x not in ADJUSTMENT_EXTRA_FIELDS]:
        value = get_fact(f)
        if value:
            if f == "最大功率W":
                facts[f] = clean_power_value(value)
            elif f in {"宽度", "高度", "直径"}:
                facts[f] = clean_size_value(value) or value
            else:
                facts[f] = value
    return "\n".join(f"- {k}: {v}" for k, v in facts.items() if str(v).strip())





def title_context_for_prompt(lang: str = "ES") -> str:
    """Compact, high-signal context used ONLY for title generation.
    V16.2: the title generator must behave like the chat workflow that works well:
    one clear original title + one image/fact summary, not the whole long listing.
    Do not feed long descriptions, A+ style prose, cable micro-specs or bulb-exclusion text into title prompts.
    """
    def short(v, n=260):
        v = re.sub(r"\s+", " ", str(v or "")).strip()
        return v[:n]

    # Only one visible commercial size should influence the title.
    main_size = size_phrase_for_title(lang) or clean_size_value(get_fact("直径") or get_fact("尺寸") or get_fact("高度") or "")
    if main_size:
        # Prefer diameter or one compact size; avoid secondary dimensions such as cable/base/wall distance.
        m = re.search(r"Ø?\s*\d+(?:[.,]\d+)?\s*cm", str(main_size), flags=re.I)
        main_size = normalize_title_units(m.group(0)) if m else normalize_title_units(str(main_size))

    title_allowed = {
        "Brand": st.session_state.get("brand", "Alpinaluz") or "Alpinaluz",
        "Original title to improve": short(st.session_state.get("manual_title", ""), 320),
        "Product type": map_value("产品类型", get_field("产品类型"), lang),
        "Main visible material": map_value("材质", get_field("材质"), lang),
        "Main visible color / finish": map_value("颜色", get_field("颜色"), lang),
        "Shade / body color": short(", ".join([x for x in [get_fact("灯罩颜色"), get_fact("灯体颜色"), get_fact("底座颜色")] if x]), 160),
        "Main visible size for title": main_size,
        "Socket or integrated light": map_value("灯头", get_field("灯头"), lang),
        "Max wattage only if useful": clean_power_value(get_fact("最大功率W")),
        "Recommended bulb shape only if useful": short(get_fact("推荐灯泡"), 80),
        "Core style": map_value("风格", get_field("风格"), lang),
        "Main rooms": map_value("适用空间", get_field("适用空间"), lang),
        "High-value SEO keywords from user": short(st.session_state.get("keywords", ""), 220),
        "Confirmed must-title keywords": short(", ".join(st.session_state.get("title_must_keywords", []) or []), 220),
        "Forbidden title keywords": short(", ".join(st.session_state.get("title_banned_keywords", []) or []), 220),
    }
    allowed_lines = [f"- {k}: {v}" for k, v in title_allowed.items() if str(v).strip()]

    # Explicit negative instructions: these details are useful, but for bullets/description, not title.
    do_not_use = [
        "bombilla no incluida / sin bombilla / no incluye bombilla",
        "compatible / compatible con bombillas / compatible con LED",
        "ideal para / perfecto para / bonito / precioso",
        "longitud de cable y cable 2.4 m; interruptor en cable/de pie solo si NO es un atributo comercial principal",
        "base Ø, distancia a pared, brazo, altura total, pared-separación, medidas secundarias",
        "instalación sencilla, incluye accesorios, montaje fácil",
        "series name unless explicitly allowed",
    ]
    return "\n".join(allowed_lines) + "\n\nDo NOT use in the TITLE:\n- " + "\n- ".join(do_not_use)

def original_copy_policy_prompt() -> str:
    mode = st.session_state.get("source_quality_mode", "优质原文保留增强（推荐）")
    manual_title = st.session_state.get("manual_title", "").strip()
    manual_desc = st.session_state.get("manual_description", "").strip()
    source = st.session_state.get("source_text", "").strip()
    if mode.startswith("优质"):
        return f"""
ORIGINAL-COPY PRESERVATION MODE IS ACTIVE.
The user may have pasted a high-quality existing Amazon/title/bullets/description. Your task is NOT to summarize it. Your task is to preserve and upgrade it.
- Preserve all concrete facts and selling points from Manual title, Manual description and Source text.
- Do not delete specifics such as dimensions, material, finish, socket, recommended bulb type, max wattage, mounting, cable length, distance from wall, room uses, style, IP rating, CCT, USB, switch, etc.
- If original bullets are complete, convert them into Amazon bullet format with stronger labels, but keep their content.
- Improve SEO, grammar, ordering, capitalization and Amazon readability. Do not make the copy poorer or shorter.
- Title: keep the useful structure of the original title, expand only with missing high-value SEO facts, and remove low-value filler.
- Title must NOT waste space with: bombilla no incluida, sin bombilla, compatible, ideal para, perfecto para. Put bulb exclusion in bullets/description only.
- If a fact appears in original text but not fact card, treat original text as high-priority evidence unless it conflicts with technical notes.

Manual title:
{manual_title or '(empty)'}

Manual description / original bullets:
{manual_desc or '(empty)'}

Source text:
{source[:4000] or '(empty)'}
"""
    if mode.startswith("原文一般"):
        return "Original copy may be incomplete. Preserve confirmed facts, but rewrite for stronger Amazon conversion and SEO. Do not summarize away concrete parameters."
    return "Source is sparse. Generate high-quality Amazon copy from confirmed facts and images, but never invent specs."


def product_type_hint_es() -> str:
    socket = get_field("灯头")
    max_w = get_fact("最大功率W")
    led_status = get_field("是否LED")
    if led_status in {"LED集成", "是"} or socket == "LED integrado":
        cct = get_fact("色温K") or get_fact("光色调节")
        power = get_fact("最大功率W")
        extra = []
        if power:
            extra.append(f"potencia {power}")
        if cct:
            extra.append(f"CCT/color {cct}")
        return "Producto con LED integrado: no escribir Bombilla no incluida ni compatible con bombillas reemplazables. " + "; ".join(extra)
    if socket in {"E27", "E14", "GU10", "G9", "G4", "GX53"} and get_field("是否含灯泡") == "否":
        if max_w:
            return f"Compatible con bombillas LED {socket} de hasta {max_w}W. Bombilla no incluida."
        return f"Compatible con bombillas LED {socket}. Bombilla no incluida."
    return ""


def apply_product_defaults(pt: str) -> None:
    defaults = PRODUCT_DEFAULTS.get(pt, {})
    for k, v in defaults.items():
        if k in FIELD_OPTIONS:
            set_pick_value(k, v)


def analyze_product_facts() -> Dict[str, Any]:
    allowed = {k: FIELD_OPTIONS[k] for k in CORE_FACT_FIELDS + ADJUSTMENT_EXTRA_FIELDS if k in FIELD_OPTIONS}
    prompt = f"""
你是 Alpinaluz 灯具产品上架助理。请根据用户粘贴的网站资料、技术备注、图片文件名和图片内容，识别产品事实。

目标：先锁定事实，不要写营销文案。

规则：
- 不确定就写空字符串或在“不确定项”里说明，不要瞎猜。
- 复杂颜色必须分部件：主色、灯罩颜色、底座颜色、电线颜色、顶盘颜色、变体主颜色。
- 材质、风格、适用空间可以输出多个值，例如 ["钢","铝"]、["现代","功能型"]。
- 如果图片里出现灯泡，只能说明“图片出现灯泡”，不能判断为包含灯泡；除非文字明确写含灯泡。
- 如果是普通 E27/E14/GU10/G9 灯具，默认灯泡不包含。
- 如果出现 LED integrado / LED集成 / integrated LED / 6W LED / CCT / 3000K/4000K/6000K / selector de temperatura：
  1) 是否LED = LED集成
  2) 灯头 = LED integrado
  3) 是否含灯泡 = 不适用（LED集成）
  4) 不要识别为 E27/GU10 等传统可换灯泡，除非明确写 compatible con bombilla GU10/E27。
- CCT 色温能力不是亮度调光：如果只是 3000K/4000K/6000K，光色调节=三档CCT 3000K/4000K/6000K，亮度调节=未提供。
- 如果出现 350°/350º/350 grados，方向调节=350°旋转，调节能力=可定向调节。
- 如果看到复古电影灯/三脚架探照灯，风格优先识别为 Retro Cinema / Vintage，不要写现代极简。
- 如果尺寸有 D29 / D38 / Ø29 / Ø38，要明确记录，不要混淆。
- 输出 JSON，不要解释。

可选字段枚举：
{json.dumps(allowed, ensure_ascii=False)}

当前输入：
{facts_for_prompt('ES')}

请输出 JSON，字段包含：
{json.dumps(CORE_FACT_FIELDS + COLOR_PART_FIELDS + EXTRA_FACT_FIELDS + ['不确定项', '建议排除图片', '图片策略建议'], ensure_ascii=False)}
"""
    files = images_for_analysis()
    raw = llm_multimodal(prompt, files) if files and image_analysis_limit() > 0 else llm(prompt, system="You extract product facts and output JSON only.", temperature=0.1)
    fallback = {k: "" for k in CORE_FACT_FIELDS + COLOR_PART_FIELDS + EXTRA_FACT_FIELDS + ["不确定项", "建议排除图片", "图片策略建议"]}
    result = safe_json(raw, fallback)
    if not isinstance(result, dict):
        result = fallback
    return postprocess_facts(result)


def collect_variant_terms() -> Dict[str, List[str]]:
    terms = {lang: [] for lang in LANGS}
    raw = st.session_state.get("variant_terms", "")
    extra = [x.strip().lower() for x in raw.split(",") if x.strip()]
    for t in extra:
        for lang in terms:
            terms[lang].append(t)
    if "颜色" in st.session_state.get("variant_fields", []):
        color = get_field("颜色")
        if color in VALUE_MAP.get("颜色", {}):
            for lang, val in VALUE_MAP["颜色"][color].items():
                terms[lang].append(val.lower())
    return {k: sorted(set(v), key=v.index) for k, v in terms.items()}


def clean_variants(text: str, lang: str, section: str) -> str:
    scope = st.session_state.get("variant_scope", "标题+Search terms")
    keep = set()
    if scope == "仅标题":
        keep = {"TITLE"}
    elif scope == "标题+Search terms":
        keep = {"TITLE", "SEARCH TERMS"}
    elif scope == "全文":
        keep = {"TITLE", "BULLETS", "DESCRIPTION", "SEARCH TERMS", "A+"}
    elif scope == "完全中性":
        keep = set()
    if section in keep:
        return text
    out = text
    for term in collect_variant_terms().get(lang, []):
        if term:
            out = re.sub(rf"(?i)\b{re.escape(term)}\b", "", out)
    out = re.sub(r"\s+", " ", out)
    out = re.sub(r"\s+([,.;:])", r"\1", out)
    out = re.sub(r",\s*,", ",", out)
    return out.strip(" ,;-–—")


def clean_title_candidate(title: str) -> str:
    t = str(title or "")
    t = re.sub(r"(?i)^(title|titulo|título|titel|titol|titre)\s*[:：]\s*", "", t).strip()
    t = remove_model_codes(t)
    t = strip_series_from_title(t)
    t = remove_bare_cm(t)
    t = re.sub(r"[\"“”'`]+", "", t)
    t = re.sub(r"\s+", " ", t).strip(" ,-–—")
    return t


def spanish_title_case(title: str) -> str:
    small = {"de", "del", "la", "el", "las", "los", "y", "e", "o", "u", "en", "con", "sin", "para", "por", "a", "al", "hasta", "desde"}
    keep_upper = {"E27", "E14", "GU10", "G9", "G4", "GX53", "LED", "IP44", "IP65", "USB", "CCT"}
    words = re.split(r"(\s+|-|–|,)", title)
    out = []
    word_index = 0
    for w in words:
        if not w or re.match(r"\s+|-|–|,", w):
            out.append(w)
            continue
        raw = w.strip()
        stripped = raw.strip("()[]")
        upper = stripped.upper().strip(".,;:")
        low = stripped.lower().strip(".,;:")
        if upper in keep_upper or re.match(r"^\d+[WK]?$", upper):
            new = raw.upper()
        elif low in small and word_index != 0:
            new = raw.lower()
        elif raw.lower() == "alpinaluz":
            new = "Alpinaluz"
        else:
            new = raw[:1].upper() + raw[1:].lower()
        out.append(new)
        word_index += 1
    return "".join(out).replace("Led", "LED").replace("Gu10", "GU10").replace("E27", "E27").replace("E14", "E14")




def title_case_en_like(title: str) -> str:
    small = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "with", "without"}
    keep = {"LED", "USB", "CCT", "GU10", "E27", "E14", "G9", "IP20", "IP44", "IP65", "USB-C", "USB-A", "SION"}
    parts = re.split(r"(\s+|-|–|,|/)", title)
    out, idx = [], 0
    for p in parts:
        if not p or re.match(r"\s+|-|–|,|/", p):
            out.append(p); continue
        core = p.strip("()[]:;,.!")
        up = core.upper()
        low = core.lower()
        if up in keep or re.match(r"^\d+[A-Z]*$", up):
            new = p.upper()
        elif low in small and idx != 0:
            new = p.lower()
        elif low == "alpinaluz":
            new = "Alpinaluz"
        else:
            new = p[:1].upper() + p[1:].lower()
        out.append(new); idx += 1
    return "".join(out).replace("Usb", "USB").replace("Led", "LED").replace("Cct", "CCT")


def fix_foreign_title_residuals(title: str, lang: str) -> str:
    """Clean common Spanish/English residuals from localized titles without changing product facts."""
    t = str(title or "")
    # V16.9 deterministic grammar fixes for common local title artifacts.
    if lang == "IT":
        t = re.sub(r"(?i)\bstile\s+moderna\b", "stile moderno", t)
        t = re.sub(r"(?i)\bsunset\b", "tramonto", t)
    if lang == "NL":
        t = re.sub(r"(?i)\bmodern\s+stijl\b", "moderne stijl", t)
    if lang == "PT":
        t = re.sub(r"(?i)\bsunset\b", "pôr do sol", t)
    if lang == "FR":
        t = re.sub(r"(?i)\beffet\s+sunset\b", "effet coucher de soleil", t)
    if lang == "PL":
        t = re.sub(r"(?i)\bsunset(?:em)?\b", "zachodu słońca", t)
    if lang == "SE":
        t = re.sub(r"(?i)\bsunset[- ]?", "solnedgångs", t)
    if lang == "ES":
        return t
    triple = {
        "EN": "triple shade", "FR": "triple abat-jour", "DE": "dreifacher Lampenschirm",
        "IT": "triplo paralume", "NL": "drievoudige kap", "PL": "potrójny klosz",
        "PT": "tripla cúpula", "SE": "trippel skärm",
    }.get(lang, "triple shade")
    repls = [
        (r"(?i)\btriple\s+pantalla\b", triple),
        (r"(?i)\bl[aá]mpara\s+colgante\b", {"EN":"pendant light","FR":"lampe suspendue","DE":"Pendelleuchte","IT":"lampada a sospensione","NL":"hanglamp","PL":"lampa wisząca","PT":"candeeiro suspenso","SE":"pendellampa"}.get(lang, "pendant light")),
        (r"(?i)\blampada\s+colgante\b", "lampada a sospensione" if lang == "IT" else "pendant light"),
        (r"(?i)\blâmpada\s+colgante\b", "candeeiro suspenso" if lang == "PT" else "pendant light"),
        (r"(?i)\blampe\s+colgante\b", "lampe suspendue" if lang == "FR" else "pendant light"),
        (r"(?i)\bRat[aá]n\b", {"EN":"rattan","FR":"rotin","DE":"Rattan","IT":"rattan","NL":"rotan","PL":"rattan","PT":"rattan","SE":"rotting"}.get(lang, "rattan")),
        (r"(?i)\bmimbre\b", {"EN":"wicker","FR":"osier","DE":"Weide","IT":"vimini","NL":"wilgentenen","PL":"wiklina","PT":"vime","SE":"pil"}.get(lang, "wicker")),
        (r"(?i)\bCasquillo\b", {"EN":"socket","FR":"douille","DE":"Fassung","IT":"attacco","NL":"fitting","PL":"oprawka","PT":"casquilho","SE":"sockel"}.get(lang, "socket")),
        (r"(?i)\bSal[oó]n\b", {"EN":"living room","FR":"salon","DE":"Wohnzimmer","IT":"soggiorno","NL":"woonkamer","PL":"salon","PT":"sala","SE":"vardagsrum"}.get(lang, "living room")),
        (r"(?i)\bComedor\b", {"EN":"dining room","FR":"salle à manger","DE":"Esszimmer","IT":"sala da pranzo","NL":"eetkamer","PL":"jadalnia","PT":"sala de jantar","SE":"matsal"}.get(lang, "dining room")),
    ]
    for pat, rep in repls:
        t = re.sub(pat, rep, t)
    return re.sub(r"\s+", " ", t).strip(" ,;-–—")


def normalize_title_style(title: str, lang: str) -> str:
    title = commercial_title_clean(remove_title_low_value_phrases(normalize_title_units(clean_title_candidate(title))))
    title = fix_foreign_title_residuals(title, lang)
    title = fix_broken_title_fragments(title, lang)
    if lang == "ES":
        return normalize_title_units(spanish_title_case(title))
    if lang == "EN":
        return normalize_title_units(title_case_en_like(title))
    # 其他欧洲语言不要强行全词首大写，交给模型；只修正常见缩写和单位。
    return normalize_title_units(title)



def fix_broken_title_fragments(title: str, lang: str = "") -> str:
    """V16.6: hard guard against broken localized title fragments like 'with -Effect' or 'mit -Leuchtmitteln'."""
    t = str(title or "")
    if not t:
        return t
    # Common broken fragments from batch localization.
    t = re.sub(r"(?i)\bwith\s+-\s*effect\b", "with sunset-effect", t)
    t = re.sub(r"(?i)\bwith\s+-effect\b", "with sunset-effect", t)
    t = re.sub(r"(?i)\bmit\s+-\s*leuchtmitteln\b", "mit G9-LED-Leuchtmitteln", t)
    t = re.sub(r"(?i)\bmit\s+-leuchtmitteln\b", "mit G9-LED-Leuchtmitteln", t)
    t = re.sub(r"(?i)\bcompatibel\s+mit\s+-\s*leuchtmitteln\b", "kompatibel mit G9-LED-Leuchtmitteln", t)
    t = re.sub(r"(?i)\bcompatible\s+with\s+-\s*bulbs\b", "compatible with G9 LED bulbs", t)
    t = re.sub(r"\s+", " ", t).strip(" ,;-–—")
    return t


def extract_es_title_skeleton(es_title: str) -> Dict[str, Any]:
    """Parse the final ES title into a compact semantic skeleton.
    V16.6 uses this for foreign titles instead of free-generation or tri-state keyword tables.
    """
    t = normalize_title_units(str(es_title or ""))
    # V16.9: parse the locked title FIRST, but enrich the semantic skeleton from the locked ES master
    # and trusted manual/source text. In V16.6, foreign titles often lost high-value concepts when
    # the final ES title was intentionally shorter, e.g. sunset effect / yellow-orange-red glass / gold base.
    context_text = "\n".join([
        t,
        str(st.session_state.get("es_text", "")),
        str(st.session_state.get("manual_title", "")),
        str(st.session_state.get("source_text", "")),
        str(st.session_state.get("manual_description", "")),
        str(st.session_state.get("technical_notes", "")),
        str(get_field("核心卖点1") or ""),
        str(get_field("核心卖点2") or ""),
        str(get_field("核心卖点3") or ""),
    ])
    low = context_text.lower()
    title_low = t.lower()
    brand = st.session_state.get("brand", "Alpinaluz") or "Alpinaluz"

    # Product type from the locked ES title, with fact-card fallback.
    if re.search(r"aplique|l[aá]mpara\s+mural|wall\s+light", low):
        product_key = "wall_light"
    elif re.search(r"l[aá]mpara\s+colgante|colgante|suspensi[oó]n", low):
        product_key = "pendant_light"
    elif re.search(r"l[aá]mpara\s+de\s+mesa|sobremesa", low):
        product_key = "table_lamp"
    elif re.search(r"l[aá]mpara\s+de\s+pie|pie\b", low):
        product_key = "floor_lamp"
    elif re.search(r"plaf[oó]n|techo", low):
        product_key = "ceiling_light"
    else:
        f = str(get_field("产品类型") or "")
        if "壁" in f or "aplique" in f.lower(): product_key = "wall_light"
        elif "吊" in f or "colg" in f.lower(): product_key = "pendant_light"
        elif "桌" in f or "mesa" in f.lower(): product_key = "table_lamp"
        elif "落地" in f or "pie" in f.lower(): product_key = "floor_lamp"
        elif "吸顶" in f or "techo" in f.lower(): product_key = "ceiling_light"
        else: product_key = "light"

    size = ""
    m = re.search(r"Ø\s*\d+(?:[.,]\d+)?\s*cm(?:\s*[x×]\s*\d+(?:[.,]\d+)?\s*cm)?", t, flags=re.I)
    if not m:
        m = re.search(r"\b\d+(?:[.,]\d+)?\s*(?:x|×)\s*\d+(?:[.,]\d+)?\s*cm\b", t, flags=re.I)
    if not m:
        m = re.search(r"Ø\s*\d+(?:[.,]\d+)?\s*cm", context_text, flags=re.I)
    if m:
        size = normalize_title_units(m.group(0))

    material_key = ""
    if re.search(r"vidrio\s+multicolor|cristal\s+multicolor|glass\s+multicol", low):
        material_key = "multicolor_glass"
    elif re.search(r"cristal\s+opal|vidrio\s+opal|opalino|opaco", low):
        material_key = "opal_glass"
    elif re.search(r"rat[aá]n", low):
        material_key = "rattan"
    elif re.search(r"mimbre", low):
        material_key = "wicker"
    elif re.search(r"bamb[uú]", low):
        material_key = "bamboo"
    elif re.search(r"madera", low):
        material_key = "wood"
    elif re.search(r"metal|acero|hierro", low):
        material_key = "metal"

    effect_key = ""
    if re.search(r"atardecer|sunset|puesta\s+de\s+sol", low):
        effect_key = "sunset_effect"
    elif re.search(r"efecto\s+m[aá]rmol|marmol", low):
        effect_key = "marble_effect"
    elif re.search(r"efecto\s+sombra|sombras", low):
        effect_key = "shadow_effect"

    finish_key = ""
    if re.search(r"dorado|oro|gold", low):
        finish_key = "gold_metal_base" if re.search(r"base|soporte|metal", low) else "gold_finish"
    elif re.search(r"negro|black", low):
        finish_key = "black_finish"
    elif re.search(r"blanco|white", low):
        finish_key = "white_finish"

    socket = ""
    ms = re.search(r"\b(E27|G9|GU10|E14|G45)\b", context_text, flags=re.I)
    if ms:
        socket = ms.group(1).upper()
    elif re.search(r"led\s+integrado|LED integrado", context_text, flags=re.I):
        socket = "LED integrado"

    style_keys = []
    for key, pats in {
        "modern": [r"moderno", r"moderna"],
        "nordic": [r"n[oó]rdic"],
        "vintage": [r"vintage", r"retro"],
        "rustic": [r"r[uú]stic"],
        "industrial": [r"industrial"],
        "boho": [r"boho", r"bohem"],
    }.items():
        if any(re.search(p, low) for p in pats):
            style_keys.append(key)
    style_keys = style_keys[:2]

    room_keys = []
    room_patterns = [
        ("living", [r"sal[oó]n", r"living"]),
        ("bedroom", [r"dormitorio", r"habitaci[oó]n", r"chambre", r"bedroom"]),
        ("dining", [r"comedor", r"jantar", r"dining"]),
        ("hallway", [r"pasillo", r"corredor", r"recibidor", r"entrada", r"hall"]),
        ("kitchen", [r"cocina", r"kitchen"]),
        ("office", [r"oficina", r"estudio"]),
    ]
    for key, pats in room_patterns:
        if any(re.search(p, low) for p in pats):
            room_keys.append(key)
    if not room_keys:
        froom = str(get_field("适用空间") or "")
        if "客厅" in froom or "sal" in froom.lower(): room_keys.append("living")
        if "卧" in froom or "dorm" in froom.lower(): room_keys.append("bedroom")
        if "餐" in froom or "com" in froom.lower(): room_keys.append("dining")
        if "走" in froom or "pas" in froom.lower(): room_keys.append("hallway")
    room_keys = room_keys[:3]

    return {
        "brand": brand,
        "product_key": product_key,
        "size": size,
        "material_key": material_key,
        "effect_key": effect_key,
        "finish_key": finish_key,
        "socket": socket,
        "style_keys": style_keys,
        "room_keys": room_keys,
    }


PRODUCT_TERMS = {
    "wall_light": {"EN":"Wall Light", "FR":"applique murale", "DE":"Wandleuchte", "IT":"applique da parete", "NL":"wandlamp", "PL":"kinkiet", "PT":"aplique de parede", "SE":"vägglampa"},
    "pendant_light": {"EN":"Pendant Light", "FR":"suspension", "DE":"Pendelleuchte", "IT":"lampada a sospensione", "NL":"hanglamp", "PL":"lampa wisząca", "PT":"candeeiro suspenso", "SE":"pendellampa"},
    "table_lamp": {"EN":"Table Lamp", "FR":"lampe de table", "DE":"Tischleuchte", "IT":"lampada da tavolo", "NL":"tafellamp", "PL":"lampa stołowa", "PT":"candeeiro de mesa", "SE":"bordslampa"},
    "floor_lamp": {"EN":"Floor Lamp", "FR":"lampadaire", "DE":"Stehleuchte", "IT":"lampada da terra", "NL":"vloerlamp", "PL":"lampa podłogowa", "PT":"candeeiro de pé", "SE":"golvlampa"},
    "ceiling_light": {"EN":"Ceiling Light", "FR":"plafonnier", "DE":"Deckenleuchte", "IT":"plafoniera", "NL":"plafondlamp", "PL":"lampa sufitowa", "PT":"candeeiro de teto", "SE":"taklampa"},
    "light": {"EN":"Light", "FR":"luminaire", "DE":"Leuchte", "IT":"lampada", "NL":"lamp", "PL":"lampa", "PT":"candeeiro", "SE":"lampa"},
}

MATERIAL_TERMS = {
    "multicolor_glass": {"EN":"multicolour glass", "FR":"verre multicolore", "DE":"mehrfarbigem Glas", "IT":"vetro multicolore", "NL":"meerkleurig glas", "PL":"wielokolorowego szkła", "PT":"vidro multicolor", "SE":"flerfärgat glas"},
    "opal_glass": {"EN":"opal white glass", "FR":"verre opalin blanc", "DE":"opalweißem Glas", "IT":"vetro bianco opalino", "NL":"opaalwit glas", "PL":"białego szkła opalowego", "PT":"vidro branco opalino", "SE":"opalvitt glas"},
    "rattan": {"EN":"natural rattan", "FR":"rotin naturel", "DE":"natürlichem Rattan", "IT":"rattan naturale", "NL":"natuurlijk rotan", "PL":"naturalnego rattanu", "PT":"rattan natural", "SE":"naturrotting"},
    "wicker": {"EN":"natural wicker", "FR":"osier naturel", "DE":"natürlichem Weidengeflecht", "IT":"vimini naturale", "NL":"natuurlijk riet", "PL":"naturalnej wikliny", "PT":"vime natural", "SE":"naturlig pil"},
    "bamboo": {"EN":"natural bamboo", "FR":"bambou naturel", "DE":"natürlichem Bambus", "IT":"bambù naturale", "NL":"natuurlijk bamboe", "PL":"naturalnego bambusa", "PT":"bambu natural", "SE":"naturbambu"},
    "wood": {"EN":"wood", "FR":"bois", "DE":"Holz", "IT":"legno", "NL":"hout", "PL":"drewna", "PT":"madeira", "SE":"trä"},
    "metal": {"EN":"metal", "FR":"métal", "DE":"Metall", "IT":"metallo", "NL":"metaal", "PL":"metalu", "PT":"metal", "SE":"metall"},
}

EFFECT_TERMS = {
    "sunset_effect": {"EN":"Sunset-Effect Glass Globe", "FR":"globe en verre effet coucher de soleil", "DE":"Glaskugel im Sonnenuntergangseffekt", "IT":"globo in vetro effetto tramonto", "NL":"glazen bol met zonsondergangeffect", "PL":"szklana kula z efektem zachodu słońca", "PT":"globo de vidro efeito pôr do sol", "SE":"glasklot med solnedgångseffekt"},
    "marble_effect": {"EN":"marble-effect finish", "FR":"effet marbre", "DE":"Marmoroptik", "IT":"effetto marmo", "NL":"marmerlook", "PL":"efekt marmuru", "PT":"efeito mármore", "SE":"marmoreffekt"},
    "shadow_effect": {"EN":"decorative shadow effect", "FR":"effet d’ombres décoratif", "DE":"dekorativem Schattenspiel", "IT":"effetto ombra decorativo", "NL":"decoratief schaduweffect", "PL":"dekoracyjny efekt cieni", "PT":"efeito de sombras decorativo", "SE":"dekorativ skuggeffekt"},
}

FINISH_TERMS = {
    "gold_metal_base": {"EN":"gold-tone metal base", "FR":"base en métal doré", "DE":"goldfarbener Metallbasis", "IT":"base in metallo dorato", "NL":"goudkleurige metalen basis", "PL":"złota metalowa podstawa", "PT":"base metálica dourada", "SE":"guldfärgad metallbas"},
    "gold_finish": {"EN":"gold-tone finish", "FR":"finition dorée", "DE":"goldfarbener Oberfläche", "IT":"finitura dorata", "NL":"goudkleurige afwerking", "PL":"złote wykończenie", "PT":"acabamento dourado", "SE":"guldfärgad finish"},
    "black_finish": {"EN":"black finish", "FR":"finition noire", "DE":"schwarzer Oberfläche", "IT":"finitura nera", "NL":"zwarte afwerking", "PL":"czarne wykończenie", "PT":"acabamento preto", "SE":"svart finish"},
    "white_finish": {"EN":"white finish", "FR":"finition blanche", "DE":"weißer Oberfläche", "IT":"finitura bianca", "NL":"witte afwerking", "PL":"białe wykończenie", "PT":"acabamento branco", "SE":"vit finish"},
}

# V16.9: Shorter title-specific phrases. Full EFFECT_TERMS/FINISH_TERMS are good for bullets,
# but too long for marketplace titles and caused important concepts to be dropped.
TITLE_EFFECT_TERMS = {
    "sunset_effect": {"EN":"sunset-effect glass globe", "FR":"globe effet coucher de soleil", "DE":"Glaskugel mit Sonnenuntergangseffekt", "IT":"globo effetto tramonto", "NL":"glazen bol met zonsondergangeffect", "PL":"kula z efektem zachodu słońca", "PT":"globo efeito pôr do sol", "SE":"glasklot med solnedgångseffekt"},
    "marble_effect": {"EN":"marble-effect finish", "FR":"effet marbre", "DE":"Marmoroptik", "IT":"effetto marmo", "NL":"marmerlook", "PL":"efekt marmuru", "PT":"efeito mármore", "SE":"marmoreffekt"},
    "shadow_effect": {"EN":"decorative shadow effect", "FR":"effet d’ombres", "DE":"Schattenspiel", "IT":"effetto ombra", "NL":"schaduweffect", "PL":"efekt cieni", "PT":"efeito de sombras", "SE":"skuggeffekt"},
}
TITLE_FINISH_TERMS = {
    "gold_metal_base": {"EN":"gold metal base", "FR":"base métal doré", "DE":"goldfarbene Metallbasis", "IT":"base metallo dorato", "NL":"gouden metalen basis", "PL":"złota metalowa podstawa", "PT":"base metálica dourada", "SE":"guldfärgad metallbas"},
    "gold_finish": {"EN":"gold finish", "FR":"finition dorée", "DE":"goldfarbene Oberfläche", "IT":"finitura dorata", "NL":"gouden afwerking", "PL":"złote wykończenie", "PT":"acabamento dourado", "SE":"guldfärgad finish"},
    "black_finish": {"EN":"black finish", "FR":"finition noire", "DE":"schwarze Oberfläche", "IT":"finitura nera", "NL":"zwarte afwerking", "PL":"czarne wykończenie", "PT":"acabamento preto", "SE":"svart finish"},
    "white_finish": {"EN":"white finish", "FR":"finition blanche", "DE":"weiße Oberfläche", "IT":"finitura bianca", "NL":"witte afwerking", "PL":"białe wykończenie", "PT":"acabamento branco", "SE":"vit finish"},
}

STYLE_TERMS = {
    "modern": {"EN":"modern", "FR":"moderne", "DE":"modern", "IT":"moderna", "NL":"modern", "PL":"nowoczesny", "PT":"moderno", "SE":"modern"},
    "nordic": {"EN":"Nordic", "FR":"nordique", "DE":"nordisch", "IT":"nordico", "NL":"Scandinavisch", "PL":"skandynawski", "PT":"nórdico", "SE":"nordisk"},
    "vintage": {"EN":"vintage", "FR":"vintage", "DE":"Vintage", "IT":"vintage", "NL":"vintage", "PL":"vintage", "PT":"vintage", "SE":"vintage"},
    "rustic": {"EN":"rustic", "FR":"rustique", "DE":"rustikal", "IT":"rustico", "NL":"rustiek", "PL":"rustykalny", "PT":"rústico", "SE":"rustik"},
    "industrial": {"EN":"industrial", "FR":"industriel", "DE":"industriell", "IT":"industriale", "NL":"industrieel", "PL":"industrialny", "PT":"industrial", "SE":"industriell"},
    "boho": {"EN":"boho", "FR":"bohème", "DE":"Boho", "IT":"boho", "NL":"boho", "PL":"boho", "PT":"boho", "SE":"boho"},
}

ROOM_TERMS = {
    "living": {"EN":"Living Room", "FR":"salon", "DE":"Wohnzimmer", "IT":"soggiorno", "NL":"woonkamer", "PL":"salonu", "PT":"sala", "SE":"vardagsrum"},
    "bedroom": {"EN":"Bedroom", "FR":"chambre", "DE":"Schlafzimmer", "IT":"camera da letto", "NL":"slaapkamer", "PL":"sypialni", "PT":"quarto", "SE":"sovrum"},
    "dining": {"EN":"Dining Room", "FR":"salle à manger", "DE":"Esszimmer", "IT":"sala da pranzo", "NL":"eetkamer", "PL":"jadalni", "PT":"sala de jantar", "SE":"matsal"},
    "hallway": {"EN":"Hallway", "FR":"couloir", "DE":"Flur", "IT":"corridoio", "NL":"hal", "PL":"korytarza", "PT":"corredor", "SE":"hall"},
    "kitchen": {"EN":"Kitchen", "FR":"cuisine", "DE":"Küche", "IT":"cucina", "NL":"keuken", "PL":"kuchni", "PT":"cozinha", "SE":"kök"},
    "office": {"EN":"Office", "FR":"bureau", "DE":"Arbeitszimmer", "IT":"ufficio", "NL":"kantoor", "PL":"biura", "PT":"escritório", "SE":"arbetsrum"},
}


def local_join_terms(values: List[str], lang: str) -> str:
    return join_native([v for v in values if v], lang, 3)


def title_from_semantic_skeleton(lang: str, es_title: str) -> str:
    """Fast deterministic local title from final ES title semantic skeleton.
    This prevents expensive/free LLM localization from adding/breaking facts.
    """
    if lang == "ES":
        return normalize_title_style(es_title, "ES")
    sk = extract_es_title_skeleton(es_title)
    brand = sk["brand"]
    product = PRODUCT_TERMS.get(sk["product_key"], PRODUCT_TERMS["light"]).get(lang, PRODUCT_TERMS["light"]["EN"])
    material = MATERIAL_TERMS.get(sk["material_key"], {}).get(lang, "")
    effect = TITLE_EFFECT_TERMS.get(sk["effect_key"], {}).get(lang, "")
    finish = TITLE_FINISH_TERMS.get(sk["finish_key"], {}).get(lang, "")
    socket = sk.get("socket", "")
    style = local_join_terms([STYLE_TERMS.get(k, {}).get(lang, "") for k in sk.get("style_keys", [])], lang)
    rooms = local_join_terms([ROOM_TERMS.get(k, {}).get(lang, "") for k in sk.get("room_keys", [])], lang)
    size = sk.get("size", "")

    if lang == "EN":
        parts = [f"{brand} {material.title() + ' ' if material else ''}{product}"]
        if size: parts[0] += f" {size}"
        if effect: parts.append(f"with {effect}")
        if finish: parts.append(finish.title())
        if socket: parts.append(f"{socket} Fitting")
        if style: parts.append(f"{style} Style")
        if rooms: parts.append(f"for {rooms}")
    elif lang == "DE":
        parts = [f"{brand} {product}"]
        if material: parts[0] += f" aus {material}"
        if size: parts[0] += f" {size}"
        if effect: parts.append(f"mit {effect}")
        if finish: parts.append(finish)
        if socket: parts.append(f"{socket}-Fassung")
        if style: parts.append(f"{style}er Stil")
        if rooms: parts.append(f"für {rooms}")
    elif lang == "FR":
        parts = [f"{brand} {product}"]
        if material: parts[0] += f" en {material}"
        if size: parts[0] += f" {size}"
        if effect: parts.append(f"avec {effect}")
        if finish: parts.append(finish)
        if socket: parts.append(f"douille {socket}")
        if style: parts.append(f"style {style}")
        if rooms: parts.append(f"pour {rooms}")
    elif lang == "IT":
        parts = [f"{brand} {product}"]
        if material: parts[0] += f" in {material}"
        if size: parts[0] += f" {size}"
        if effect: parts.append(f"con {effect}")
        if finish: parts.append(finish)
        if socket: parts.append(f"attacco {socket}")
        if style: parts.append(f"stile {style}")
        if rooms: parts.append(f"per {rooms}")
    elif lang == "NL":
        parts = [f"{brand} {product}"]
        if material: parts[0] += f" van {material}"
        if size: parts[0] += f" {size}"
        if effect: parts.append(f"met {effect}")
        if finish: parts.append(finish)
        if socket: parts.append(f"{socket}-fitting")
        if style: parts.append(f"{style} stijl")
        if rooms: parts.append(f"voor {rooms}")
    elif lang == "PL":
        parts = [f"{brand} {product}"]
        if material: parts[0] += f" z {material}"
        if size: parts[0] += f" {size}"
        if effect: parts.append(effect)
        if finish: parts.append(finish)
        if socket: parts.append(f"oprawka {socket}")
        if style: parts.append(f"styl {style}")
        if rooms: parts.append(f"do {rooms}")
    elif lang == "PT":
        parts = [f"{brand} {product}"]
        if material: parts[0] += f" em {material}"
        if size: parts[0] += f" {size}"
        if effect: parts.append(f"com {effect}")
        if finish: parts.append(finish)
        if socket: parts.append(f"casquilho {socket}")
        if style: parts.append(f"estilo {style}")
        if rooms: parts.append(f"para {rooms}")
    elif lang == "SE":
        parts = [f"{brand} {product}"]
        if material: parts[0] += f" i {material}"
        if size: parts[0] += f" {size}"
        if effect: parts.append(f"med {effect}")
        if finish: parts.append(finish)
        if socket: parts.append(f"{socket}-sockel")
        if style: parts.append(f"{style} stil")
        if rooms: parts.append(f"för {rooms}")
    else:
        parts = [f"{brand} {product}"]

    title = ", ".join([p for p in parts if p])
    title = fix_broken_title_fragments(localize_foreign_leftovers(title, lang), lang)
    title = normalize_title_style(fix_broken_title_fragments(title, lang), lang)
    max_len = int(st.session_state.get("max_title", 200))
    if len(title) > max_len:
        # Drop low-priority tail pieces before truncating.
        for drop in range(1, 5):
            shorter = ", ".join([p for p in parts[:-drop] if p])
            shorter = normalize_title_style(fix_broken_title_fragments(localize_foreign_leftovers(shorter, lang), lang), lang)
            if shorter and len(shorter) <= max_len and len(shorter) >= 95:
                title = shorter
                break
    if len(title) > max_len:
        title = title[:max_len].rsplit(" ", 1)[0].strip(" ,;-–—")
    if not title.lower().startswith(brand.lower()):
        title = f"{brand} {title}"
    return normalize_title_style(fix_broken_title_fragments(title, lang), lang)


def title_cn_from_skeleton(lang: str, title: str) -> str:
    """Cheap deterministic title explanation for Chinese colleagues.
    Prevents batch model artifacts like “此标题按要求原样保留” and stays synced with the final title.
    """
    sk = extract_es_title_skeleton(st.session_state.get("locked_es_title") or st.session_state.get("selected_es_title") or title)
    pieces = ["Alpinaluz"]
    product_cn = {
        "wall_light": "壁灯", "pendant_light": "吊灯", "table_lamp": "台灯",
        "floor_lamp": "落地灯", "ceiling_light": "吸顶灯", "light": "灯具"
    }.get(sk.get("product_key"), "灯具")
    pieces.append(product_cn)
    material_cn = {
        "multicolor_glass": "多色玻璃", "opal_glass": "乳白/蛋白玻璃", "rattan": "藤编",
        "wicker": "藤/柳编", "bamboo": "竹", "wood": "木质", "metal": "金属"
    }.get(sk.get("material_key"), "")
    if material_cn: pieces.append(material_cn)
    if sk.get("size"): pieces.append(sk.get("size"))
    effect_cn = {"sunset_effect": "日落/晚霞效果", "marble_effect": "大理石效果", "shadow_effect": "装饰光影效果"}.get(sk.get("effect_key"), "")
    if effect_cn: pieces.append(effect_cn)
    finish_cn = {"gold_metal_base": "金色金属底座", "gold_finish": "金色表面", "black_finish": "黑色表面", "white_finish": "白色表面"}.get(sk.get("finish_key"), "")
    if finish_cn: pieces.append(finish_cn)
    if sk.get("socket"): pieces.append(f"{sk.get('socket')}灯头/光源")
    room_map = {"living": "客厅", "bedroom": "卧室", "dining": "餐厅", "hallway": "走廊/玄关", "kitchen": "厨房", "office": "办公室/书房"}
    rooms = [room_map.get(x, x) for x in sk.get("room_keys", [])]
    if rooms: pieces.append("适用于" + "、".join(rooms))
    return "，".join([p for p in pieces if p]) + "。"

def remove_water_phrases(title: str) -> str:
    t = title
    for phrase in WATER_TITLE_PHRASES:
        t = re.sub(rf"(?i)\b{re.escape(phrase)}\b", "", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    return t.strip(" ,;-–—")


def remove_title_low_value_phrases(title: str) -> str:
    """Keep safety wording for bullets, but remove low-value phrases from Amazon titles.
    V16.2: title is for SEO/conversion, not compliance details or installation fiche.
    """
    t = str(title or "")
    # Title should say E27/G45/40W when useful, but not waste space with bulb exclusion, compatibility prose, cable length or installation details.
    t = re.sub(r"(?i)[,;\s–—-]*(bombillas?\s+no\s+incluidas?|no\s+incluye\s+bombillas?|sin\s+bombillas?|l[aá]mpara\s+sin\s+bombilla)\b", "", t)
    t = re.sub(r"(?i)[,;\s–—-]*con\s+cable\s+de\s+\d+(?:[.,]\d+)?\s*m(?:etros?)?\b", "", t)
    t = re.sub(r"(?i)[,;\s–—-]*(cable|cord[oó]n)\s*(?:de|hasta|aprox\.?|:)\s*\d+(?:[.,]\d+)?\s*m(?:etros?)?\b", "", t)
    t = re.sub(r"(?i)[,;\s–—-]*(interruptor\s+(?:en\s+el\s+cable|de\s+pie|integrado)|incluye\s+accesorios|instalaci[oó]n\s+sencilla|montaje\s+f[aá]cil)\b", "", t)
    # Remove isolated cable lengths even if the word cable was omitted.
    t = re.sub(r"(?i)[,;\s–—-]*\b\d+(?:[.,]\d+)?\s*m\b(?=\s*(?:de\s+cable|cable|,|;|$))", "", t)
    t = re.sub(r"(?i)\bcompatible\s+con\s+bombillas?\s+LED\s+de\s+hasta\s+(\d+\s*W)\b", r"hasta \1", t)
    t = re.sub(r"(?i)\bcompatible\s+con\s+bombilla\s+G45\b", "G45", t)
    t = re.sub(r"(?i)\bcompatible\s+con\s+bombillas?\s+LED\b", "", t)
    t = re.sub(r"(?i)\bcompatible\s+con\s+bombillas?\b", "", t)
    t = re.sub(r"(?i)\bcompatible\s+LED\b", "", t)
    t = re.sub(r"(?i)\bcompatible\b", "", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r"[,;:][,;:]+", ",", t)
    return t.strip(" ,;-–—")



def commercial_title_clean(title: str) -> str:
    """V15.7: make titles commercial, not a technical fiche.
    Keep primary customer-facing size (e.g. Ø18 cm / Ø45 cm), socket, material, style and main room.
    Move micro specs like wall distance/base/cable length/secondary height to bullets/description.
    """
    t = str(title or "")
    if not t:
        return t
    # Keep only the main visible diameter/size if a title has Ø18 x 66 cm / Ø45 cm x 38 cm.
    t = re.sub(r"(Ø\s*\d+(?:[.,]\d+)?\s*cm)\s*[x×]\s*\d+(?:[.,]\d+)?\s*cm\b", r"\1", t, flags=re.I)
    # Remove low-SEO micro-measurements from the title; they remain useful in bullets/description.
    micro_words = [
        "distancia desde la pared", "distancia a la pared", "distancia pared", "base de pared", "base montaje", "base",
        "cable máximo", "longitud máxima", "longitud del cable", "cable ajustable", "cable de suspensión", "cable decorativo",
        "altura total", "alto total", "profundidad", "fondo", "ancho", "largo"
    ]
    for w in micro_words:
        # segment like ', base de pared 12 cm' or ' – cable máximo de 20 cm'
        t = re.sub(rf"(?i)\s*[,;–—-]?\s*{re.escape(w)}\s*(?:de|hasta|máxima|aprox\.?|:)?\s*\d+(?:[.,]\d+)?\s*cm\b", "", t)
    # Keep the feature words but remove low-value numeric micro details.
    t = re.sub(r"(?i)\b(Altura Ajustable|Cable Ajustable|Cable de Suspensión|Distancia a la Pared|Base de Pared)\s*(?:de|hasta|máxima|aprox\.?|:)?\s*\d+(?:[.,]\d+)?\s*cm\b", r"\1", t)
    # Title should not spend space on bulb exclusion/safety wording.
    t = remove_title_low_value_phrases(t)
    t = re.sub(r"(?i)\b(bombilla\s+no\s+incluida|sin\s+bombilla|no\s+incluye\s+bombilla)\b", "", t)
    # Clean punctuation left by removed segments.
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r"[,;:](\s*[,;:])+", ",", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" ,;-–—")
    return t

def normalize_title_units(title: str) -> str:
    t = strip_series_from_title(str(title or ""))
    # Kelvin and watt must be upper-case, metric units usually lower-case.
    t = re.sub(r"(\d+)\s*k\b", r"\1K", t, flags=re.I)
    t = re.sub(r"(\d+)\s*w\b", r"\1W", t, flags=re.I)
    t = re.sub(r"(\d+)\s*cm\b", r"\1 cm", t, flags=re.I)
    t = re.sub(r"(\d+)\s*mm\b", r"\1 mm", t, flags=re.I)
    # Tech tokens: preserve normal Amazon spelling.
    t = re.sub(r"\bUSB\s*[- ]?\s*A\b", "USB-A", t, flags=re.I)
    t = re.sub(r"\bUSB\s*[- ]?\s*C\b", "USB-C", t, flags=re.I)
    t = re.sub(r"\btype\s*[- ]?\s*A\b", "Type A", t, flags=re.I)
    t = re.sub(r"\btype\s*[- ]?\s*C\b", "Type C", t, flags=re.I)
    t = re.sub(r"\bLed\b", "LED", t, flags=re.I)
    t = re.sub(r"\bCct\b", "CCT", t, flags=re.I)
    # Remove common duplication caused by title generation.
    t = re.sub(r"(?i)\b(Foco\s+Orientable)\s+\1\b", r"\1", t)
    t = re.sub(r"(?i)\b(spot\s+orientable)\s+\1\b", r"\1", t)
    t = re.sub(r"(?i)\b(orientable)\s+\1\b", r"\1", t)
    # Remove bare unit fragments such as “Ajustable Cm” after title casing.
    t = remove_bare_cm(t)
    # Language-specific grammar/typo hotfixes from repeated tests.
    t = t.replace("mit integrierte LED", "mit integrierter LED")
    t = t.replace("draaibaare", "draaibare")
    t = t.replace("USB-a", "USB-A").replace("USB-c", "USB-C")
    # Unit casing after any title-case step.
    t = re.sub(r"(Ø?\d+(?:[.,]\d+)?)\s*Cm\b", lambda m: m.group(1).replace(",", ".") + " cm", t)
    t = re.sub(r"(Ø?\d+(?:[.,]\d+)?)\s*Mm\b", lambda m: m.group(1).replace(",", ".") + " mm", t)
    t = re.sub(r"\bCm\b", "cm", t)
    t = re.sub(r"\bMm\b", "mm", t)
    # Remove dangling labels created during refinement.
    t = re.sub(r"(?i)\b(Ajustable|Regulable|Orientable)\s+cm\b", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip(" ,;-–—")
    return t

ALLOWED_HYPHEN_CODES = {"USB-C", "USB-A", "TYPE-C", "TYPE-A", "WI-FI"}

def find_model_codes(text: str) -> List[str]:
    codes = []
    for m in re.finditer(r"\b[A-Z0-9]{2,}-[A-Z0-9]{1,}(?:-[A-Z0-9]{1,})*\b", str(text or "")):
        code = m.group(0).upper()
        if code not in ALLOWED_HYPHEN_CODES:
            codes.append(m.group(0))
    return codes

def remove_model_codes(text: str) -> str:
    def repl(m):
        code = m.group(0).upper()
        return m.group(0) if code in ALLOWED_HYPHEN_CODES else ""
    return re.sub(r"\b[A-Z0-9]{2,}-[A-Z0-9]{1,}(?:-[A-Z0-9]{1,})*\b", repl, str(text or ""))

def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", str(text or "")))


def language_forbidden_patterns(lang: str) -> List[str]:
    common = [r"\[[^\]]+\]"]  # 未替换占位符
    spanish_residual = [
        r"\bAplique\s+de\s+Pared\b", r"\bFoco\s+Orientable\b", r"\bPuertos?\b", r"\bBandeja\b",
        r"\bEstructura\s+de\s+Acero\b", r"\bL[aá]mpara\b", r"\bDormitorio\b", r"\bSal[oó]n\b",
        r"\bL[aá]mpara\s+Colgante\b", r"\bRat[aá]n\b", r"\bCasquillo\b", r"\bComedor\b", r"\bPantalla\b", r"\bTriple\s+Pantalla\b"
    ]
    extra = {
        "IT": [r"\bcolgante\b", r"\bmimbre\b", r"\brat[aá]n\b"],
        "PT": [r"\bcolgante\b", r"\brat[aá]n\b", r"\bsoporte\b"],
        "FR": [r"\bmimbre\b", r"\brat[aá]n\b", r"\bcolgante\b", r"\bFoco\s+Orientable\b", r"\bAplique\s+de\s+Pared\b"],
        "PL": [r"\bmimbre\b", r"\brat[aá]n\b", r"\bcolgante\b"],
        "NL": [r"\bmimbre\b", r"\brat[aá]n\b", r"\bcolgante\b"],
        "SE": [r"\bmimbre\b", r"\brat[aá]n\b", r"\bcolgante\b"],
        "DE": [r"\bmimbre\b", r"\brat[aá]n\b", r"\bcolgante\b"],
        "EN": [r"\bmimbre\b", r"\brat[aá]n\b", r"\bcolgante\b"],
    }
    if lang != "ES":
        return common + spanish_residual + extra.get(lang, [])
    return common


def title_is_valid(title: str, lang: str = "ES") -> bool:
    max_len = int(st.session_state.get("max_title", 200))
    min_len = int(st.session_state.get("min_title", 140))
    if lang != "ES":
        # 多语言标题宁可短而自然，也不要为了凑长度生成中文/占位符/错误语言。
        min_len = min(min_len, 80)
    t = clean_title_candidate(title)
    if not t or len(t) > max_len or len(t) < min_len:
        return False
    if has_cjk(t):
        return False
    if t.split()[-1].lower().strip(".,;:;–-—") in TRAILING_BAD:
        return False
    if re.search(r"[,;:\-–—]\s*$", t):
        return False
    if re.search(r"(?i)\b(and|with|for|of|to|in|para|con|de|del|pour|avec|un|une|et|per|e|di|voor|met|och|med|do|dla|z|w)\s*$", t):
        return False
    if find_model_codes(t):
        return False
    for pat in language_forbidden_patterns(lang):
        if re.search(pat, t, flags=re.I):
            return False
    if lang == "ES" and not t.lower().startswith("alpinaluz"):
        return False
    if lang == "ES" and any(re.search(rf"(?i)\b{re.escape(p)}\b", t) for p in WATER_TITLE_PHRASES):
        return False
    return True


def compact_join(parts: List[str], sep: str = " ") -> str:
    cleaned = [re.sub(r"\s+", " ", str(p or "")).strip(" ,;-–—") for p in parts if str(p or "").strip() and not has_cjk(str(p or ""))]
    out = sep.join(cleaned)
    out = re.sub(r"\s+", " ", out).strip(" ,;-–—")
    return out


def clean_power_value(value: str) -> str:
    txt = str(value or "").strip()
    if not txt:
        return ""
    m = re.search(r"(\d+(?:[.,]\d+)?)", txt)
    if not m:
        return "" if has_cjk(txt) else txt
    return m.group(1).replace(",", ".") + "W"

def clean_size_value(value: str) -> str:
    txt = str(value or "").strip()
    if not txt:
        return ""
    if re.search(r"28\s?cm|280\s?mm", txt, flags=re.I):
        return "28 cm"
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(cm|mm)", txt, flags=re.I)
    if m:
        return m.group(1).replace(",", ".") + " " + m.group(2).lower()
    return "" if has_cjk(txt) else txt

def title_has_structured_format(title: str) -> bool:
    t = str(title or "")
    return ("–" in t or " - " in t) and (":" in t)

def title_looks_like_fragments(title: str) -> bool:
    t = str(title or "")
    if has_cjk(t):
        return True
    if len(t) > 110 and not title_has_structured_format(t):
        return True
    # Many comma-separated bare nouns without labels are hard to read.
    if len(t) > 130 and t.count(",") >= 3 and ":" not in t:
        return True
    if re.search(r"\b(3000K[,/ ]+4000K|4000K[,/ ]+6000K)\b", t) and "3000K/4000K/6000K" not in t:
        return True
    return False

def structured_title_parts(lang: str) -> Dict[str, str]:
    brand = st.session_state.get("brand", "Alpinaluz") or "Alpinaluz"
    series = get_series_name() if (title_should_include_series() and not has_cjk(get_series_name())) else ""
    product = map_value("产品类型", get_field("产品类型"), lang) or {
        "ES":"aplique de pared", "FR":"applique murale", "DE":"Wandleuchte", "IT":"applique da parete", "NL":"wandlamp", "PL":"kinkiet", "PT":"aplique de parede", "SE":"vägglampa", "EN":"wall light"
    }.get(lang, "wall light")
    light = map_value("灯头", get_field("灯头"), lang) or map_value("是否LED", get_field("是否LED"), lang)
    power = clean_power_value(get_fact("最大功率W"))
    cct = map_value("光色调节", get_fact("光色调节"), lang) or ("CCT " + "/".join([x + "K" for x in normalize_to_list(get_fact("色温K")) if x.isdigit()]) if normalize_to_list(get_fact("色温K")) else "")
    if "3000" in str(get_fact("色温K")) and "4000" in str(get_fact("色温K")) and "6000" in str(get_fact("色温K")):
        cct = "CCT 3000K/4000K/6000K"
    # 传统灯头产品默认不把 CCT 写入标题，除非产品事实明确是集成LED。
    if str(get_field("灯头")).upper() in {"E27", "E14", "GU10", "G9", "G4", "GX53"} and str(get_field("是否LED")) != "LED集成":
        cct = ""
    adjust = map_value("方向调节", get_fact("方向调节"), lang)
    material = map_value("材质", get_field("材质"), lang)
    color = map_value("颜色", get_field("颜色"), lang)
    tray = clean_size_value(get_fact("宽度") or get_fact("尺寸"))
    has_usb = "USB" in facts_for_prompt(lang).upper()
    room = map_value("适用空间", get_field("适用空间"), lang)
    return {"brand":brand, "series":series, "product":product, "light":light, "power":power, "cct":cct, "adjust":adjust, "material":material, "color":color, "tray":tray, "has_usb":str(has_usb), "room":room}


def build_natural_title(lang: str, style: str = "自然") -> str:
    """Readable Amazon-style titles, not raw keyword fragments."""
    p = structured_title_parts(lang)
    brand_series = compact_join([p["brand"], p["series"]])
    cct = p.get("cct", "").replace("CCT ", "").strip()
    adjust = p.get("adjust", "")
    tray = p.get("tray", "")
    color = p.get("color", "")
    power = p.get("power", "")
    room = p.get("room", "")
    has_usb = p.get("has_usb") == "True"

    if lang == "ES":
        base = compact_join([brand_series, p["product"], p["light"], power])
        feats = []
        if cct: feats.append(f"con CCT {cct}")
        if adjust: feats.append(f"foco orientable {adjust}")
        if has_usb: feats.append("puertos USB-A y USB-C")
        if tray: feats.append(f"bandeja de acero {tray}")
        tail = compact_join([color, f"para {room}" if room and style == "SEO" else ""], ", ")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + tail if tail else "")
    elif lang == "EN":
        base = compact_join([brand_series, p["light"], p["product"], power])
        feats=[]
        if cct: feats.append(f"with {cct} CCT")
        if adjust: feats.append(f"{adjust} spotlight")
        if has_usb: feats.append("USB-A and USB-C charging ports")
        if tray: feats.append(f"{tray} steel tray")
        tail = compact_join([color, f"for {room}" if room and style == "SEO" else ""], ", ")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + tail if tail else "")
    elif lang == "DE":
        base = compact_join([brand_series, p["product"], "mit", p["light"], power])
        feats=[]
        if cct: feats.append(f"CCT {cct}")
        if adjust: feats.append(f"{adjust}er Spot")
        if has_usb: feats.append("USB-A und USB-C Ladeanschlüsse")
        if tray: feats.append(f"{tray} Ablage")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + color if color else "")
    elif lang == "IT":
        base = compact_join([brand_series, p["product"], p["light"], power])
        feats=[]
        if cct: feats.append(f"con CCT {cct}")
        if adjust: feats.append(f"faretto {adjust}")
        if has_usb: feats.append("porte USB-A e USB-C")
        if tray: feats.append(f"vassoio in acciaio {tray}")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + color if color else "")
    elif lang == "FR":
        base = compact_join([brand_series, p["product"], p["light"], power])
        feats=[]
        if cct: feats.append(f"avec CCT {cct}")
        if adjust: feats.append(f"spot {adjust}")
        if has_usb: feats.append("ports USB-A et USB-C")
        if tray: feats.append(f"plateau en acier {tray}")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + color if color else "")
    elif lang == "PT":
        base = compact_join([brand_series, p["product"], p["light"], power])
        feats=[]
        if cct: feats.append(f"com CCT {cct}")
        if adjust: feats.append(f"foco {adjust}")
        if has_usb: feats.append("portas USB-A e USB-C")
        if tray: feats.append(f"bandeja de aço {tray}")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + color if color else "")
    elif lang == "NL":
        base = compact_join([brand_series, p["light"], p["product"], power])
        feats=[]
        if cct: feats.append(f"met CCT {cct}")
        if adjust: feats.append(f"{adjust}e spot")
        if has_usb: feats.append("USB-A en USB-C laadpoorten")
        if tray: feats.append(f"stalen plateau {tray}")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + color if color else "")
    elif lang == "PL":
        base = compact_join([brand_series, p["product"], p["light"], power])
        feats=[]
        if cct: feats.append(f"CCT {cct}")
        if adjust: feats.append(f"reflektor {adjust}")
        if has_usb: feats.append("porty USB-A i USB-C")
        if tray: feats.append(f"stalowa półka {tray}")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + color if color else "")
    elif lang == "SE":
        base = compact_join([brand_series, p["product"], p["light"], power])
        feats=[]
        if cct: feats.append(f"med CCT {cct}")
        if adjust: feats.append(f"{adjust} spotlight")
        if has_usb: feats.append("USB-A och USB-C laddningsportar")
        if tray: feats.append(f"stålhylla {tray}")
        title = base + (" " + ", ".join(feats) if feats else "") + (", " + color if color else "")
    else:
        title = compact_join([brand_series, p["product"], p["light"], power])
    return normalize_title_style(title, lang)


def build_concise_title(lang: str) -> str:
    p = structured_title_parts(lang)
    brand_series = compact_join([p["brand"], p["series"]])
    cct = p.get("cct", "").replace("CCT ", "").strip()
    usb = "USB-C" if p.get("has_usb") == "True" else ""
    if lang == "ES":
        title = compact_join([brand_series, p["product"], p["light"], p["power"], f"CCT {cct}" if cct else "", usb, p.get("color", "")])
    elif lang == "EN":
        title = compact_join([brand_series, p["light"], p["product"], p["power"], f"CCT {cct}" if cct else "", usb, p.get("color", "")])
    elif lang == "DE":
        title = compact_join([brand_series, p["product"], "mit", p["light"], p["power"], f"CCT {cct}" if cct else "", usb, p.get("color", "")])
    else:
        title = compact_join([brand_series, p["product"], p["light"], p["power"], f"CCT {cct}" if cct else "", usb, p.get("color", "")])
    return normalize_title_style(title, lang)

def build_structured_title(lang: str, compact: bool = False) -> str:
    p = structured_title_parts(lang)
    brand_series = compact_join([p["brand"], p["series"]])
    # Marketplace-readable titles: product first, then feature labels.
    if lang == "ES":
        start = compact_join([brand_series, p["product"], p["light"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"Luz CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Foco Orientable: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Carga: USB-A y USB-C")
        if p["tray"]: bits.append(f"Bandeja: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    elif lang == "EN":
        start = compact_join([brand_series, p["light"], p["product"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Spot: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Charging: USB-A and USB-C")
        if p["tray"]: bits.append(f"Tray: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    elif lang == "DE":
        start = compact_join([brand_series, p["product"], "mit", p["light"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Spot: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Laden: USB-A und USB-C")
        if p["tray"]: bits.append(f"Ablage: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    elif lang == "IT":
        start = compact_join([brand_series, p["product"], p["light"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Faretto: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Ricarica: USB-A e USB-C")
        if p["tray"]: bits.append(f"Vassoio: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    elif lang == "FR":
        start = compact_join([brand_series, p["product"], p["light"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Spot: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Charge: USB-A et USB-C")
        if p["tray"]: bits.append(f"Plateau: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    elif lang == "PT":
        start = compact_join([brand_series, p["product"], p["light"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Foco: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Carga: USB-A e USB-C")
        if p["tray"]: bits.append(f"Bandeja: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    elif lang == "NL":
        start = compact_join([brand_series, p["light"], p["product"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Spot: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Opladen: USB-A en USB-C")
        if p["tray"]: bits.append(f"Plateau: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    elif lang == "PL":
        start = compact_join([p["brand"], p["series"], p["product"], p["light"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Regulacja: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Ładowanie: USB-A i USB-C")
        if p["tray"]: bits.append(f"Półka: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    elif lang == "SE":
        start = compact_join([brand_series, p["product"], p["light"], p["power"]])
        bits = []
        if p["cct"]: bits.append(f"CCT: {p['cct'].replace('CCT ', '')}")
        if p["adjust"]: bits.append(f"Spot: {p['adjust']}")
        if p["has_usb"] == "True": bits.append("Laddning: USB-A och USB-C")
        if p["tray"]: bits.append(f"Hylla: {p['tray']}")
        if p["color"]: bits.append(p["color"])
        title = start + " – " + ", ".join(bits) if bits else start
    else:
        title = compact_join([p["brand"], p["product"], p["light"]])
    return normalize_title_style(title, lang)

def build_safe_title(lang: str) -> str:
    """Deterministic readable fallback title based on selected style."""
    max_len = int(st.session_state.get("max_title", 200))
    mode = st.session_state.get("title_format_mode", "自然亚马逊标题（推荐）")
    if mode.startswith("结构化"):
        cand = build_structured_title(lang)
    elif mode.startswith("SEO"):
        cand = build_natural_title(lang, style="SEO")
    elif mode.startswith("简洁"):
        cand = build_concise_title(lang)
    else:
        cand = build_natural_title(lang, style="自然")
    cand = normalize_title_style(cand, lang)
    if len(cand) <= max_len and title_is_valid(cand, lang):
        return cand
    for alt in [build_natural_title(lang, "自然"), build_concise_title(lang), build_structured_title(lang)]:
        alt = normalize_title_style(alt, lang)
        if len(alt) <= max_len and title_is_valid(alt, lang):
            return alt
    p = structured_title_parts(lang)
    # 最后兜底也不能硬塞 CCT/USB-C，避免 E27 普通灯具被误写成CCT产品。
    fallback = compact_join([p["brand"], p["product"], p["light"], p["power"], p.get("color", "")])
    return normalize_title_style(fallback, lang)

def ensure_title(title: str, lang: str, facts: str) -> str:
    max_len = int(st.session_state.get("max_title", 200))
    min_len = int(st.session_state.get("min_title", 140))
    title = remove_water_phrases(clean_title_candidate(title))
    if lang == "ES" and not title.lower().startswith("alpinaluz"):
        title = f"Alpinaluz {re.sub(r'(?i)^alpinaluz\s*', '', title).strip()}"
    title = normalize_title_style(title, lang)
    title = clean_variants(title, lang, "TITLE")
    # V14.4: if the title looks like a raw list of fragments, rewrite to a readable Amazon style.
    if title_is_valid(title, lang):
        if st.session_state.get("title_format_mode", "自然亚马逊标题（推荐）").startswith(("结构化", "自然", "SEO", "简洁")) and title_looks_like_fragments(title):
            structured = build_safe_title(lang)
            if title_is_valid(structured, lang):
                return structured
        return title
    last = title
    candidates = [title] if title else []
    for _ in range(5):
        prompt = f"""
Rewrite this Amazon {lang} title from scratch in native {LANGS.get(lang, {}).get('name', lang)}.

Hard rules:
- Output ONE complete title only, no explanation.
- Must be <= {max_len} characters.
- Aim for {min_len}-{max_len} characters, but a shorter complete title is better than a cut sentence.
- Do NOT truncate. Do NOT end with a connector or preposition.
- Do NOT include SKU/model code.
- Do NOT include product series name unless explicitly allowed. Current series: {get_series_name() or "(empty)"}.
- Never output bare "cm" without a number immediately before it. Use "94-140 cm" or remove the unit.
- For Spanish: title MUST start with Alpinaluz; use Spanish Amazon title case; do not use filler phrases such as ideal para/perfecto para.
- For non-Spanish languages: do NOT use Spanish phrases such as Aplique de Pared, Foco Orientable, Dormitorio, Salón, Bandeja, Puertos. Translate the title fully into the target language.
- Title capitalization: EN uses Amazon Title Case; ES uses Spanish Title Case; DE uses natural German capitalization; FR/IT/PT/NL/PL/SE use native marketplace style, not Spanish capitalization.
- Do not output Chinese characters or placeholder brackets like [壁灯].
- Keep only useful words: brand, product type, style if locked, socket/LED, material/color if relevant, key use/room.
- Use a readable Amazon title format with separators when useful, e.g. “Product – Feature: detail, Feature: detail”. Do not output a raw list of disconnected keywords.

Compact title facts:
{title_context_for_prompt(lang)}

Bad title to rewrite:
{last}
"""
        new_title = clean_title_candidate(llm(prompt, temperature=0.15).splitlines()[0])
        new_title = remove_water_phrases(new_title)
        if lang == "ES" and not new_title.lower().startswith("alpinaluz"):
            new_title = "Alpinaluz " + re.sub(r"(?i)^alpinaluz\s*", "", new_title).strip()
        new_title = normalize_title_style(new_title, lang)
        new_title = clean_variants(new_title, lang, "TITLE")
        candidates.append(new_title)
        if title_is_valid(new_title, lang):
            return new_title
        if 40 <= len(new_title) <= max_len and title_is_valid(new_title, lang):
            return new_title
        last = new_title or last
    under = [c for c in candidates if c and len(c) <= max_len and not has_cjk(c) and c.split()[-1].lower().strip(".,;:-") not in TRAILING_BAD and not any(re.search(pat, c, flags=re.I) for pat in language_forbidden_patterns(lang))]
    if under:
        return max(under, key=len)
    return build_safe_title(lang)


def trim_search_terms(text: str) -> str:
    max_len = int(st.session_state.get("max_search_terms", 250))
    text = re.sub(r"\s+", " ", str(text or "")).strip(" ,")
    parts = [p.strip() for p in re.split(r",|\n", text) if p.strip()]
    out, seen = [], set()
    for p in parts:
        if p.lower() in seen:
            continue
        cand = ", ".join(out + [p])
        if len(cand) > max_len:
            break
        out.append(p)
        seen.add(p.lower())
    return ", ".join(out)


def remove_safety_bad_phrases(text: str) -> str:
    out = str(text or "")
    replacements = {
        r"(?i)incluyendo\s+LED,?\s*Edison\s+o\s+tradicionales": "compatible con bombillas LED",
        r"(?i)incluyendo\s+LED": "compatible con bombillas LED",
        r"(?i)incluye\s+bombilla[s]?(\s+LED)?": "bombilla no incluida",
        r"(?i)bombilla[s]?\s+incluida[s]?(\s+LED)?": "bombilla no incluida",
    }
    for pat, rep in replacements.items():
        out = re.sub(pat, rep, out)
    return out


def safety_warnings(text: str) -> List[str]:
    warnings = []
    lower = str(text or "").lower()
    for p in DANGEROUS_PHRASES:
        if p.lower() in lower:
            warnings.append(f"高风险短语：{p}")
    if find_model_codes(text):
        warnings.append("可能包含 SKU / 型号代码")
    for p in WATER_TITLE_PHRASES:
        if re.search(rf"(?i)\b{re.escape(p)}\b", text):
            warnings.append(f"标题水词/低价值词：{p}")
    return warnings


def extract_section(text: str, tag: str) -> str:
    m = re.search(rf"\[{re.escape(tag)}\]\s*(.*?)(?=\n\[[^\n]+\]|\Z)", str(text or ""), re.S)
    return m.group(1).strip() if m else ""


def source_es_title(es_master: str) -> str:
    title_block = extract_section(es_master, "TITLE")
    return title_block.splitlines()[0].strip() if title_block else ""


def localize_foreign_leftovers(title: str, lang: str) -> str:
    """Fix common Spanish leftovers that slipped into foreign titles before validation/output."""
    t = str(title or "")
    if lang == "ES":
        return t
    repl = {
        "EN": {"triple pantalla": "triple shade", "pantalla triple": "triple shade", "lámpara colgante": "pendant light", "ratán": "rattan", "mimbre": "wicker", "casquillo": "socket", "salón": "living room", "comedor": "dining room"},
        "FR": {"triple pantalla": "triple abat-jour", "pantalla triple": "triple abat-jour", "lámpara colgante": "suspension", "ratán": "rotin", "mimbre": "osier", "casquillo": "douille", "salón": "salon", "comedor": "salle à manger"},
        "DE": {"triple pantalla": "dreifacher Lampenschirm", "pantalla triple": "dreifacher Lampenschirm", "lámpara colgante": "Pendelleuchte", "ratán": "Rattan", "mimbre": "Weidengeflecht", "casquillo": "Fassung", "salón": "Wohnzimmer", "comedor": "Esszimmer"},
        "IT": {"triple pantalla": "triplo paralume", "pantalla triple": "triplo paralume", "lámpara colgante": "lampada a sospensione", "ratán": "rattan", "mimbre": "vimini", "casquillo": "attacco", "salón": "soggiorno", "comedor": "sala da pranzo"},
        "NL": {"triple pantalla": "drievoudige kap", "pantalla triple": "drievoudige kap", "lámpara colgante": "hanglamp", "ratán": "rotan", "mimbre": "riet", "casquillo": "fitting", "salón": "woonkamer", "comedor": "eetkamer"},
        "PL": {"triple pantalla": "potrójny klosz", "pantalla triple": "potrójny klosz", "lámpara colgante": "lampa wisząca", "ratán": "rattan", "mimbre": "wiklina", "casquillo": "oprawka", "salón": "salon", "comedor": "jadalnia"},
        "PT": {"triple pantalla": "abajur triplo", "pantalla triple": "abajur triplo", "lámpara colgante": "candeeiro suspenso", "ratán": "rattan", "mimbre": "vime", "casquillo": "casquilho", "salón": "sala", "comedor": "sala de jantar"},
        "SE": {"triple pantalla": "trippel skärm", "pantalla triple": "trippel skärm", "lámpara colgante": "pendellampa", "ratán": "rotting", "mimbre": "pil", "casquillo": "sockel", "salón": "vardagsrum", "comedor": "matsal"},
    }.get(lang, {})
    for a, b in repl.items():
        t = re.sub(re.escape(a), b, t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" ,;-–—")
    return t

def foreign_title_is_usable(title: str, lang: str, es_title: str) -> bool:
    """Reject machine/fragment/extra-spec foreign titles before they enter the final listing."""
    t = localize_foreign_leftovers(normalize_title_style(clean_title_candidate(title), lang), lang)
    if not t or has_cjk(t):
        return False
    max_len = int(st.session_state.get("max_title", 200))
    if len(t) > max_len:
        return False
    if len(t) < 75 and lang in {"DE", "FR", "IT", "NL", "PL", "PT", "SE", "EN"}:
        return False
    words = re.findall(r"[\wÀ-ÿ]+", t)
    if len(words) < 10:
        return False
    if t.split()[-1].lower().strip(".,;:;–-—") in TRAILING_BAD:
        return False
    if find_model_codes(t):
        return False
    for pat in language_forbidden_patterns(lang):
        if re.search(pat, t, flags=re.I):
            return False
    if title_has_extra_specs_vs_es(t, es_title):
        return False
    e = str(es_title or "").lower()
    bad_if_absent = {
        "IT": ["vassoio", "faretto non orientabile"],
        "PL": ["półka", "reflektor bez regulacji"],
        "PT": ["bandeja", "foco não orientável"],
        "SE": ["hylla", "ej justerbar spot"],
        "DE": ["ablage", "nicht verstellbarer spot"],
        "FR": ["plateau", "spot non orientable"],
        "NL": ["plateau", "niet verstelbare spot"],
        "EN": ["tray", "non adjustable spotlight"],
    }
    for bad in bad_if_absent.get(lang, []):
        if bad in t.lower() and not any(x in e for x in ["bandeja", "soporte", "plateau", "ablage", "hylla", "półka", "vassoio", "tray"]):
            return False
    return True




def join_native(items: List[str], lang: str, max_items: int = 3) -> str:
    vals = []
    for x in items:
        x = str(x or "").strip()
        if x and x not in vals:
            vals.append(x)
    vals = vals[:max_items]
    if not vals:
        return ""
    if len(vals) == 1:
        return vals[0]
    conj = {
        "ES":" y ", "EN":" and ", "FR":" et ", "DE":" und ", "IT":" e ",
        "NL":" en ", "PL":" i ", "PT":" e ", "SE":" och ",
    }.get(lang, " and ")
    if len(vals) == 2:
        return conj.join(vals)
    return ", ".join(vals[:-1]) + conj + vals[-1]


def local_values(field: str, value: Any, lang: str) -> List[str]:
    vals = normalize_to_list(value)
    out = []
    for v in vals:
        mv = map_value(field, v, lang)
        if mv:
            # map_value can return comma-separated values for multi fields. Keep useful pieces.
            for part in [x.strip() for x in re.split(r",", mv) if x.strip()]:
                if part and part not in out:
                    out.append(part)
    return out


def size_phrase_for_title(lang: str = "ES") -> str:
    diam = clean_size_value(get_fact("直径")) or ""
    height = clean_size_value(get_fact("高度")) or ""
    size = clean_size_value(get_fact("尺寸")) or ""
    # Prefer explicit Ø + height when both are reliable.
    if diam and height and re.search(r"\d", diam) and re.search(r"\d", height):
        d = diam if "Ø" in diam else f"Ø{diam}"
        return normalize_title_units(f"{d} x {height}")
    if diam and re.search(r"\d", diam):
        return normalize_title_units(diam if "Ø" in diam else f"Ø{diam}")
    if size and re.search(r"\d", size):
        return normalize_title_units(size)
    return ""


def localized_material_phrase(lang: str) -> str:
    mats_cn = normalize_to_list(get_field("材质"))
    has_rattan = any(x in mats_cn for x in ["藤编", "竹"])
    has_wood = "木" in mats_cn
    support_color = get_fact("底座颜色") or get_fact("顶盘颜色") or get_field("颜色")
    support_color_local = map_value("颜色", support_color, lang)
    blackish = any(x in str(support_color).lower() for x in ["黑", "negro", "black"])
    # Frequent Alpinaluz natural/rattan pendant structure. Use native, commercial phrase and avoid wrong tray/shelf/spot words.
    if has_rattan and has_wood:
        table = {
            "ES": "ratán natural con soporte de madera negra" if blackish else "ratán natural con soporte de madera",
            "EN": "natural rattan with black wood support" if blackish else "natural rattan with wood support",
            "FR": "rotin naturel avec support en bois noir" if blackish else "rotin naturel avec support en bois",
            "DE": "natürlichem Rattan mit schwarzem Holzgestell" if blackish else "natürlichem Rattan mit Holzgestell",
            "IT": "rattan naturale con supporto in legno nero" if blackish else "rattan naturale con supporto in legno",
            "NL": "natuurlijk rotan met zwarte houten steun" if blackish else "natuurlijk rotan met houten steun",
            "PL": "naturalnego rattanu z czarnym drewnianym wspornikiem" if blackish else "naturalnego rattanu z drewnianym wspornikiem",
            "PT": "rattan natural com suporte em madeira preta" if blackish else "rattan natural com suporte em madeira",
            "SE": "naturrotting med svart trästöd" if blackish else "naturrotting med trästöd",
        }
        return table.get(lang, table["EN"])
    mats = local_values("材质", get_field("材质"), lang)
    if not mats:
        return ""
    return join_native(mats, lang, 3)


def localized_style_phrase(lang: str) -> str:
    styles_cn = normalize_to_list(get_field("风格"))
    # Keep only 1-2 high-value style terms to avoid title stuffing.
    if not styles_cn:
        return ""
    # Prefer product-marketable styles by order.
    priority = ["Retro Cinema", "Vintage", "复古", "北欧", "自然", "波西米亚", "工业", "现代", "经典", "Wabi-sabi", "地中海"]
    ordered = [s for s in priority if s in styles_cn] + [s for s in styles_cn if s not in priority]
    local = []
    for s0 in ordered[:2]:
        mv = map_value("风格", s0, lang)
        if mv:
            for part in [x.strip() for x in mv.split(",") if x.strip()]:
                if part not in local:
                    local.append(part)
    if not local:
        return ""
    if lang == "ES": return "estilo " + join_native(local, lang, 2)
    if lang == "EN": return join_native(local, lang, 2) + " style"
    if lang == "FR": return "style " + join_native(local, lang, 2)
    if lang == "DE": return join_native(local, lang, 2) + "er Stil"
    if lang == "IT": return "stile " + join_native(local, lang, 2)
    if lang == "NL": return join_native(local, lang, 2) + " stijl"
    if lang == "PL": return "styl " + join_native(local, lang, 2)
    if lang == "PT": return "estilo " + join_native(local, lang, 2)
    if lang == "SE": return join_native(local, lang, 2) + " stil"
    return join_native(local, lang, 2)


def localized_socket_phrase(lang: str) -> str:
    socket = map_value("灯头", get_field("灯头"), lang) or get_field("灯头")
    led = map_value("是否LED", get_field("是否LED"), lang) or get_field("是否LED")
    maxw = clean_power_value(get_fact("最大功率W"))
    if not socket:
        return ""
    integrated = str(socket).lower() in {"led integrado", "integrated led"} or "LED集成" in str(get_field("是否LED"))
    if integrated:
        return {
            "ES":"LED integrado", "EN":"integrated LED", "FR":"LED intégré", "DE":"integrierte LED",
            "IT":"LED integrato", "NL":"geïntegreerde LED", "PL":"zintegrowany LED", "PT":"LED integrado", "SE":"integrerad LED",
        }.get(lang, "integrated LED")
    # For replaceable sockets, use short title-safe wording; bulb-not-included belongs in bullets/description more than title.
    if lang == "ES": return f"casquillo {socket} compatible con LED" + (f" hasta {maxw}" if maxw else "")
    if lang == "EN": return f"{socket} LED compatible" + (f" up to {maxw}" if maxw else "")
    if lang == "FR": return f"douille {socket} compatible LED" + (f" jusqu’à {maxw}" if maxw else "")
    if lang == "DE": return f"{socket}-Fassung LED-kompatibel" + (f" bis {maxw}" if maxw else "")
    if lang == "IT": return f"attacco {socket} compatibile LED" + (f" fino a {maxw}" if maxw else "")
    if lang == "NL": return f"{socket}-fitting geschikt voor LED" + (f" tot {maxw}" if maxw else "")
    if lang == "PL": return f"gwint {socket} kompatybilny z LED" + (f" do {maxw}" if maxw else "")
    if lang == "PT": return f"casquilho {socket} compatível LED" + (f" até {maxw}" if maxw else "")
    if lang == "SE": return f"{socket}-sockel LED-kompatibel" + (f" upp till {maxw}" if maxw else "")
    return socket


def localized_room_phrase(lang: str) -> str:
    rooms = local_values("适用空间", get_field("适用空间"), lang)
    # Remove less useful generic/hotel spaces for title length; keep top 3.
    rooms = [r for r in rooms if r]
    if not rooms:
        return ""
    joined = join_native(rooms, lang, 3)
    if lang == "ES": return f"para {joined}"
    if lang == "EN": return f"for {joined}"
    if lang == "FR": return f"pour {joined}"
    if lang == "DE": return f"für {joined}"
    if lang == "IT": return f"per {joined}"
    if lang == "NL": return f"voor {joined}"
    if lang == "PL": return f"do {joined}"
    if lang == "PT": return f"para {joined}"
    if lang == "SE": return f"för {joined}"
    return joined


def localized_title_from_facts(lang: str, es_title: str = "") -> str:
    """Deterministic native title, brand-first. Prevents foreign titles from drifting into wrong products."""
    brand = st.session_state.get("brand", "Alpinaluz") or "Alpinaluz"
    product = map_value("产品类型", get_field("产品类型"), lang) or map_value("产品类型", get_field("产品类型"), "EN") or "light"
    mat = localized_material_phrase(lang)
    size = size_phrase_for_title(lang)
    style = localized_style_phrase(lang)
    socket = localized_socket_phrase(lang)
    rooms = localized_room_phrase(lang)

    # Make product term natural and brand first. Do not include series name unless explicitly allowed.
    if lang == "ES":
        pieces = [f"{brand} {product}"]
        if mat: pieces[-1] += f" de {mat}"
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"luz ambiental {rooms}")
    elif lang == "EN":
        pieces = [f"{brand} {mat} {product}" if mat else f"{brand} {product}"]
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"ambient lighting {rooms}")
    elif lang == "FR":
        pieces = [f"{brand} {product}"]
        if mat: pieces[-1] += f" en {mat}"
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"lumière d’ambiance {rooms}")
    elif lang == "DE":
        pieces = [f"{brand} {product}"]
        if mat: pieces[-1] += f" aus {mat}"
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"Stimmungslicht {rooms}")
    elif lang == "IT":
        pieces = [f"{brand} {product}"]
        if mat: pieces[-1] += f" in {mat}"
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"luce ambiente {rooms}")
    elif lang == "NL":
        pieces = [f"{brand} {product}"]
        if mat: pieces[-1] += f" van {mat}"
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"sfeerverlichting {rooms}")
    elif lang == "PL":
        pieces = [f"{brand} {product}"]
        if mat: pieces[-1] += f" z {mat}"
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"oświetlenie nastrojowe {rooms}")
    elif lang == "PT":
        pieces = [f"{brand} {product}"]
        if mat: pieces[-1] += f" em {mat}"
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"luz ambiente {rooms}")
    elif lang == "SE":
        pieces = [f"{brand} {product}"]
        if mat: pieces[-1] += f" i {mat}"
        if size: pieces.append(size)
        if style: pieces.append(style)
        if socket: pieces.append(socket)
        if rooms: pieces.append(f"stämningsbelysning {rooms}")
    else:
        pieces = [f"{brand} {product}"]

    title = ", ".join([p for p in pieces if p])
    title = normalize_title_style(title, lang)
    title = clean_title_candidate(title)
    # Re-add brand if cleaning removed it by mistake.
    if not title.lower().startswith(brand.lower()):
        title = f"{brand} {title}".strip()
    # Keep under max by dropping less critical pieces from the end.
    max_len = int(st.session_state.get("max_title", 200))
    if len(title) > max_len:
        for drop_count in range(1, 4):
            shorter = ", ".join([p for p in pieces[:-drop_count] if p])
            shorter = normalize_title_style(shorter, lang)
            if shorter and len(shorter) <= max_len:
                title = shorter
                break
    # Final sanity: no series unless allowed, no wrong table/tray/spot terms.
    title = strip_series_from_title(title)
    title = re.sub(r"(?i)\b(tray|plateau|vassoio|półka|hylla|Ablage|bandeja|reflektor bez regulacji|faretto non orientabile)\b", "", title)
    title = re.sub(r"\s+,", ",", re.sub(r"\s{2,}", " ", title)).strip(" ,;-–—")
    if not title.lower().startswith(brand.lower()):
        title = f"{brand} {title}"
    return normalize_title_style(title, lang)

def foreign_title_from_es(lang: str, es_title: str) -> str:
    """Native local title based on the locked ES title; never use fact-card title as fallback."""
    es_title = clean_title_candidate(es_title)
    if not es_title:
        return localized_title_from_facts(lang, es_title)
    # V15: deterministic brand-first local title is the default, because previous LLM localization sometimes drifted into wrong products or dropped Alpinaluz.
    deterministic = localized_title_from_facts(lang, es_title)
    if deterministic and foreign_title_is_usable(deterministic, lang, es_title):
        return deterministic
    cache = st.session_state.setdefault("title_translation_cache", {})
    cache_key = f"{lang}::{es_title}::{st.session_state.get('max_title', 200)}::{st.session_state.get('foreign_title_mode', '本地SEO润色（推荐）')}::v150"
    if cache_key in cache:
        return cache[cache_key]
    max_len = int(st.session_state.get("max_title", 200))
    mode = st.session_state.get("foreign_title_mode", "本地SEO润色（推荐）")
    if mode.startswith("严格"):
        localize_instruction = "Translate accurately and keep the ES title order, but make grammar natural in the target marketplace."
        temp = 0.08
    else:
        localize_instruction = "Create a native Amazon marketplace title based on the ES title. Preserve all facts, but reorder naturally for local SEO and readability. Do not sound like a word-by-word translation."
        temp = 0.18

    prompt = f"""
Localize this LOCKED Amazon.es title into native {LANGS[lang]['name']} for {LANGS[lang]['market']}.

ES title source:
{es_title}

Mode:
{localize_instruction}

Hard rules:
- Keep the SAME facts as the ES title. Do not add facts from the fact card if they are not in the ES title.
- Do NOT add series name if not present in ES title.
- Do NOT add CCT/USB/tray/shelf/spot/degree/power/dimensions if not present in ES title.
- Preserve important commercial meaning: product type, material/style, socket/LED compatibility, key size, rooms/use.
- Native local SEO: use the natural local product term and room terms customers search for.
- No Chinese. No placeholder brackets. No Spanish leftovers except universal codes E27, LED, USB-C, IP20.
- No SKU/model code.
- Aim for 120-{max_len} characters. Do not output a very short keyword fragment.
- Do not output raw keyword fragments; write a readable Amazon title.
- Fix units and tech tokens: USB-A, USB-C, 3000K, Ø45 cm, 28 cm.
- Capitalization must follow the target language, not Spanish title case.

Return ONLY the final title, one line.
"""
    candidates = []
    for i, temperature in enumerate([temp, 0.10, 0.14, 0.06]):
        extra = "" if i == 0 else "\nCRITICAL RETRY: previous title was invalid. Keep exactly the ES facts, remove added specs such as shelf/tray/non-adjustable spotlight if absent in ES, no Spanish leftovers, no Chinese, no short keyword fragments."
        raw = llm(prompt + extra, system="Native Amazon title localizer for lighting products. Return one line only.", temperature=temperature)
        title = localize_foreign_leftovers(normalize_title_style(clean_variants(clean_title_candidate(raw.splitlines()[0]), lang, "TITLE"), lang), lang)
        if title and title not in candidates:
            candidates.append(title)
        if foreign_title_is_usable(title, lang, es_title):
            cache[cache_key] = title
            return title
    valid = [c for c in candidates if foreign_title_is_usable(c, lang, es_title)]
    if valid:
        title = max(valid, key=len)
    else:
        raw = llm(prompt + "\nFINAL RETRY: translate/localize the ES title only. No extra facts. No very short title.", system="Strict native title translator. One line only.", temperature=0.02)
        title = localize_foreign_leftovers(normalize_title_style(clean_variants(clean_title_candidate(raw.splitlines()[0]), lang, "TITLE"), lang), lang)
        if not title or has_cjk(title) or len(title) > max_len or find_model_codes(title):
            title = normalize_title_style(es_title, "ES")
    cache[cache_key] = title
    return title

def title_has_extra_specs_vs_es(title: str, es_title: str) -> bool:
    """Avoid foreign titles adding wrong specs due to fact-card errors."""
    t = str(title or "").lower()
    e = str(es_title or "").lower()
    spec_groups = [
        ["cct", "3000k", "4000k", "6000k"],
        ["usb", "usb-a", "usb-c", "type-c"],
        ["bandeja", "tray", "plateau", "ablage", "hylla", "półka", "vassoio"],
        ["350°", "350"],
        ["360°", "360"],
    ]
    for group in spec_groups:
        if any(g in t for g in group) and not any(g in e for g in group):
            return True
    return False


def parse_numbered_lines(block: str) -> List[str]:
    block = str(block or "")
    lines = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^\d+[\).：:.\-]\s*", "", line).strip()
        if line:
            lines.append(line)
    if len(lines) <= 1:
        chunks = re.split(r"\s*(?=\d+[\).：:.\-]\s*)", block.strip())
        lines = []
        for c in chunks:
            c = re.sub(r"^\d+[\).：:.\-]\s*", "", c).strip()
            if c:
                lines.append(c)
    return lines


def parse_inline_aplus(block: str) -> List[Tuple[str, str, str]]:
    compact = re.sub(r"[\r\n]+", " ", str(block or ""))
    compact = re.sub(r"\s+", " ", compact).strip()
    pattern = re.compile(
        r"模块\s*(\d+)\s*标题[:：]\s*(.*?)\s*模块\s*\1\s*正文[:：]\s*(.*?)\s*模块\s*\1\s*中文配图提示[:：]\s*(.*?)(?=\s*模块\s*\d+\s*标题[:：]|$)",
        re.S,
    )
    modules = []
    for m in pattern.finditer(compact):
        title = re.sub(r"\s*模块\s*\d+\s*$", "", m.group(2).strip())
        body = re.sub(r"\s*模块\s*\d+\s*$", "", m.group(3).strip())
        hint = re.sub(r"\s*模块\s*\d+\s*$", "", m.group(4).strip())
        modules.append((title, body, hint))
    return modules


def parse_aplus_block(block: str) -> List[Tuple[str, str, str]]:
    modules = []
    pattern = re.compile(
        r"模块\s*(\d+)\s*标题[:：]\s*(.*?)\n模块\s*\1\s*正文[:：]\s*(.*?)\n模块\s*\1\s*中文配图提示[:：]\s*(.*?)(?=\n\s*模块\s*\d+\s*标题[:：]|\Z)",
        re.S,
    )
    for m in pattern.finditer(str(block or "")):
        modules.append((m.group(2).strip(), m.group(3).strip(), m.group(4).strip()))
    return modules


def ensure_chinese_tip(tip: str, idx: int) -> str:
    tip = str(tip or "").strip()
    if has_cjk(tip):
        return tip
    defaults = {
        1: "卧室/客厅场景图，展示产品安装后的整体氛围",
        2: "核心特性细节图，突出产品第一卖点",
        3: "核心特性细节图，突出产品第二卖点",
        4: "核心特性细节图，突出产品第三卖点",
        5: "酒店/卧室/休息区场景图，展示另一种空间应用效果",
    }
    return defaults.get(idx, "产品细节或应用场景图")


def normalize_aplus_text(block: str) -> str:
    modules = parse_aplus_block(block)
    if not modules:
        modules = parse_inline_aplus(block)
    if not modules:
        cleaned = re.sub(r"\s*(模块\s*\d+\s*标题[:：])", r"\n\1", str(block or ""))
        cleaned = re.sub(r"\s*(模块\s*\d+\s*正文[:：])", r"\n\1", cleaned)
        cleaned = re.sub(r"\s*(模块\s*\d+\s*中文配图提示[:：])", r"\n\1", cleaned)
        modules = parse_inline_aplus(cleaned) or parse_aplus_block(cleaned)
        if not modules:
            return cleaned.strip()
    out = []
    for idx, (title, body, hint) in enumerate(modules[:5], start=1):
        title = re.sub(r"\s*模块\s*\d+\s*$", "", str(title).strip())
        body = re.sub(r"\s*模块\s*\d+\s*$", "", str(body).strip())
        hint = ensure_chinese_tip(re.sub(r"\s*模块\s*\d+\s*$", "", str(hint).strip()), idx)
        out.extend([f"模块{idx} 标题：{title}", f"模块{idx} 正文：{body}", f"模块{idx} 中文配图提示：{hint}", ""])
    return "\n".join(out).strip()


def render_stats(listing_text: str, prefix: str = "") -> None:
    title = extract_section(listing_text, "TITLE")
    bullets = parse_numbered_lines(extract_section(listing_text, "BULLETS"))
    description = extract_section(listing_text, "DESCRIPTION")
    search_terms = extract_section(listing_text, "SEARCH TERMS")
    min_title = int(st.session_state.get("min_title", 140))
    max_title = int(st.session_state.get("max_title", 200))
    min_bullet = int(st.session_state.get("min_bullet", 150))
    max_bullet = int(st.session_state.get("max_bullet", 250))
    min_desc = int(st.session_state.get("min_description", 700))
    max_st = int(st.session_state.get("max_search_terms", 250))
    st.markdown(f"**{prefix}字数检测**")

    def row(label: str, value: int, ok: bool, extra: str = "") -> None:
        klass = "stat-ok" if ok else "stat-bad"
        st.markdown(f"<div class='{klass}'>{label}: {value} 字符 {extra}</div>", unsafe_allow_html=True)

    row("标题", len(title), min_title <= len(title) <= max_title, f"/ 建议 {min_title}-{max_title}")
    for i in range(5):
        val = len(bullets[i]) if i < len(bullets) else 0
        row(f"五点{i+1}", val, min_bullet <= val <= max_bullet, f"/ 建议 {min_bullet}-{max_bullet}")
    row("长描述", len(description), len(description) >= min_desc, f"/ 建议≥{min_desc}")
    row("Search terms", len(search_terms), len(search_terms) <= max_st, f"/ 建议≤{max_st}")
    warns = safety_warnings(title + "\n" + extract_section(listing_text, "DESCRIPTION") + "\n" + extract_section(listing_text, "BULLETS"))
    if warns:
        st.warning("；".join(sorted(set(warns))))


def title_contains_any(title: str, values: List[str]) -> bool:
    t = str(title or "").lower()
    return any(str(v or "").lower() in t for v in values if str(v or "").strip())


def score_title_es(title: str) -> Dict[str, Any]:
    """More discriminating score: 100 should mean a genuinely publishable title, not merely valid."""
    t = clean_title_candidate(title)
    max_len = int(st.session_state.get("max_title", 200))
    min_len = int(st.session_state.get("min_title", 140))
    checks = []
    score = 100

    def check(ok: bool, msg: str, penalty: int) -> None:
        nonlocal score
        checks.append(("通过" if ok else "注意", msg))
        if not ok:
            score -= penalty

    words = len(re.findall(r"\w+", t))
    check(bool(t) and t.lower().startswith("alpinaluz"), "品牌 Alpinaluz 第一位", 25)
    check(min_len <= len(t) <= max_len, f"长度 {len(t)} / {min_len}-{max_len}", 16)
    check(not find_model_codes(t), "无 SKU / 型号代码", 20)
    check(t.split()[-1].lower().strip(".,;:-–—") not in TRAILING_BAD if t.split() else False, "不是介词/连接词结尾", 20)
    check(not any(re.search(rf"(?i)\b{re.escape(p)}\b", t) for p in WATER_TITLE_PHRASES), "无 ideal para / perfecto para 等水词", 14)
    check(not re.search(r"(?i)\b(compatible|bombillas?\s+no\s+incluidas?|sin\s+bombilla|no\s+incluye\s+bombilla)\b", t), "标题不写 compatible / 不含灯泡等低价值安全词", 18)
    check(not re.search(r"(?i)\b(cable\s+de\s+\d|\d+(?:[.,]\d+)?\s*m\b|interruptor\s+(?:en\s+el\s+cable|de\s+pie)|instalaci[oó]n\s+sencilla|incluye\s+accesorios)\b", t), "标题不塞低SEO技术细节：电线长度/开关/安装/配件", 16)
    check(not has_bare_cm(t), "无裸 cm（cm 前必须有具体数字，例如 94-140 cm）", 22)
    check(not re.search(r"\bCm\b|\bMm\b", t), "单位格式正确：cm/mm 小写", 8)
    if get_series_name() and not title_should_include_series():
        check(not re.search(rf"(?i)(?<![A-Za-z0-9]){re.escape(get_series_name())}(?![A-Za-z0-9])", t), "未占用标题位置写系列名", 18)
    check(not re.search(r"(?i)\b(\w+)\s+\1\b", t), "无连续重复词", 10)
    check(words >= 10, "不是过短关键词标题", 12)

    product_es = map_value("产品类型", get_field("产品类型"), "ES")
    if product_es:
        check(any(tok in t.lower() for tok in product_es.lower().split()), f"包含产品类型：{product_es}", 12)
    socket = map_value("灯头", get_field("灯头"), "ES")
    if socket and socket not in {"sin portalámparas"}:
        check(socket.lower() in t.lower(), f"包含灯头/光源：{socket}", 10)

    # Important product-specific SEO signals from the fact card.
    material_es = map_value("材质", get_field("材质"), "ES")
    material_tokens = [x.strip().lower() for x in re.split(r",|/", material_es) if x.strip()]
    if material_tokens:
        check(any(tok in t.lower() for tok in material_tokens[:3]), "包含至少一个核心材质关键词", 10)
    style_es = map_value("风格", get_field("风格"), "ES")
    style_tokens = [x.strip().lower() for x in re.split(r",|/", style_es) if x.strip()]
    if style_tokens:
        check(any(tok in t.lower() for tok in style_tokens[:3]), "包含至少一个核心风格关键词", 8)
    diam = get_fact("直径") or get_fact("尺寸")
    if diam and re.search(r"\d", str(diam)):
        # Need at least one useful size number, not necessarily the exact full dimension string.
        nums = re.findall(r"\d+(?:[.,]\d+)?", str(diam))
        if nums:
            check(any(n.replace(",", ".") in t.replace(",", ".") for n in nums[:2]), "包含关键尺寸数字", 8)
    bulb_state = get_field("是否含灯泡")
    if str(get_field("灯头")).upper() in {"E27", "E14", "GU10", "G9", "G4", "GX53"}:
        # In title this is useful but not mandatory; lower penalty.
        check(("no incluida" in t.lower()) or ("compatible" in t.lower()) or ("E27" in t), "传统灯头表达安全", 6)
    banned = [x.strip().lower() for x in get_fact("禁用风格词").replace("，", ",").split(",") if x.strip()]
    if banned:
        check(not any(b in t.lower() for b in banned), "未出现禁用风格词", 20)
    return {"score": max(score, 0), "checks": checks, "len": len(t)}


def auto_title_repair_feedback(title: str) -> str:
    """把评分问题变成可执行的西语改进指令，避免新手反复手工猜怎么改。"""
    t = clean_title_candidate(title)
    notes = []
    if get_series_name() and not title_should_include_series() and re.search(rf"(?i)(?<![A-Za-z0-9]){re.escape(get_series_name())}(?![A-Za-z0-9])", t):
        notes.append(f"Quitar el nombre de serie '{get_series_name()}' del título y usar ese espacio para keywords reales del producto.")
    if has_bare_cm(t):
        notes.append("No escribir 'cm' sin número concreto. Si se menciona una medida, usar el dato exacto disponible, por ejemplo '94-140 cm', '53-62 cm' o '28 cm'. Si no hay medida fiable, eliminar 'cm'.")
    if re.search(r"(?i)\b(\w+)\s+\1\b", t):
        notes.append("Eliminar palabras repetidas consecutivas, por ejemplo 'Orientable Orientable'.")
    if any(re.search(rf"(?i)\b{re.escape(p)}\b", t) for p in WATER_TITLE_PHRASES):
        notes.append("Eliminar frases de relleno como 'ideal para' o 'perfecto para'.")
    if not t.lower().startswith("alpinaluz"):
        notes.append("Mantener Alpinaluz como primera palabra del título.")
    if find_model_codes(t):
        notes.append("Eliminar SKU o códigos internos del título.")
    if re.search(r"\bCm\b|\bMm\b", t):
        notes.append("Corregir unidades: usar 'cm' y 'mm' en minúscula, por ejemplo 'Ø45 cm'.")
    if len(t) > int(st.session_state.get("max_title", 200)):
        notes.append("Reducir el título sin cortar frases y conservando producto, estilo, casquillo/LED, material/color y uso principal.")
    if not title_contains_any(t, [map_value("材质", get_field("材质"), "ES")]):
        notes.append("Añadir un material importante si cabe, por ejemplo mimbre/ratán/madera/acero según la ficha.")
    if not title_contains_any(t, [map_value("风格", get_field("风格"), "ES")]):
        notes.append("Añadir un estilo importante si cabe, por ejemplo nórdico, natural, vintage o industrial según la ficha.")
    if t.split() and t.split()[-1].lower().strip(".,;:-–—") in TRAILING_BAD:
        notes.append("Reescribir para que el título termine con una palabra significativa, no con preposición o conector.")
    if not notes:
        notes.append("Mejorar el título haciéndolo más natural y comercial para Amazon.es, manteniendo los mismos hechos y sin añadir especificaciones nuevas.")
    return "\n".join(f"- {n}" for n in notes)


def generate_title_candidate_details(candidates: List[str]) -> List[Dict[str, Any]]:
    if not st.session_state.get("ai_title_explanations", False):
        out = []
        usages = ["自然亚马逊版", "SEO平衡版", "设计卖点版", "简洁安全版"]
        for i, title in enumerate(candidates):
            sc = score_title_es(title)
            failed = [msg for status, msg in sc.get("checks", []) if status != "通过"]
            pros = []
            if str(title).lower().startswith("alpinaluz"):
                pros.append("品牌第一位")
            if len(title) >= int(st.session_state.get("min_title", 160)):
                pros.append("长度接近目标")
            if any(x in title.lower() for x in ["e27", "gu10", "g9", "led"]):
                pros.append("包含光源/灯头信息")
            if any(x in title.lower() for x in ["salón", "dormitorio", "comedor", "baño", "pasillo", "cocina"]):
                pros.append("包含使用场景")
            out.append({
                "title": title,
                "cn": "自动解释：该标题主要描述产品类型、核心材质/颜色、主要尺寸或灯头，以及适用空间。请重点检查事实是否准确。",
                "pros": "、".join(pros) if pros else "结构基本完整",
                "risks": "；".join(failed[:4]) if failed else "暂无明显硬伤",
                "usage": usages[i] if i < len(usages) else "标题候选",
                "score": sc.get("score", 0),
                "len": sc.get("len", len(title)),
                "checks": sc.get("checks", []),
            })
        return out
    prompt = f"""
请用中文解释以下 Amazon.es 标题候选，帮助新手选择。
每个标题必须给出：
- 中文解释：标题在说什么
- 优点：SEO/转化/安全性优点
- 风险：是否可能太长、是否信息太满、是否缺少某个关键点
- 建议用途：SEO平衡版 / 功能强化版 / 保守安全版 之一

产品事实：
{facts_for_prompt('ES')}

标题候选：
{json.dumps(candidates, ensure_ascii=False)}

输出 JSON：
{{"items":[{{"cn":"...","pros":"...","risks":"...","usage":"..."}}, ...]}}
"""
    try:
        raw = llm(prompt, system="You output strict JSON only.", temperature=0.15)
        data = safe_json(raw, {"items": []})
        items = data.get("items", []) if isinstance(data, dict) else []
    except Exception:
        items = []
    out = []
    for i, title in enumerate(candidates):
        sc = score_title_es(title)
        item = items[i] if i < len(items) and isinstance(items[i], dict) else {}
        out.append({
            "title": title,
            "cn": item.get("cn", ""),
            "pros": item.get("pros", ""),
            "risks": item.get("risks", ""),
            "usage": item.get("usage", ["自然亚马逊版", "SEO平衡版", "技术结构版", "简洁安全版"][i] if i < 4 else "标题候选"),
            "score": sc.get("score", 0),
            "len": sc.get("len", len(title)),
            "checks": sc.get("checks", []),
        })
    return out


def format_title_candidate_details(details: List[Dict[str, Any]]) -> str:
    blocks = []
    for i, d in enumerate(details, start=1):
        lines = [
            f"候选{i}：{d.get('usage','')}",
            f"西语标题：{d.get('title','')}",
            f"中文解释：{d.get('cn','')}",
            f"优点：{d.get('pros','')}",
            f"风险：{d.get('risks','')}",
            f"评分：{d.get('score',0)}分 / {d.get('len',0)}字符",
        ]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def generate_es_title_candidates() -> List[str]:
    min_len = int(st.session_state.get("min_title", 140))
    max_len = int(st.session_state.get("max_title", 200))
    prompt = f"""
Genera 4 títulos candidatos para Amazon.es con estilos diferentes.

Estrategia: {st.session_state.get('title_strategy')}

CONTEXTO COMPACTO PARA TÍTULO (usar esto como fuente principal; NO arrastrar detalles largos de bullets/description al título):
{title_context_for_prompt('ES')}

Si hay título original/manual y está bien, mejóralo sin destruir su estructura. El objetivo NO es meter todos los parámetros: el título debe vender y posicionar, no parecer ficha técnica.

Reglas duras:
- Los 4 títulos deben empezar EXACTAMENTE por Alpinaluz.
- Longitud objetivo: {min_len}-{max_len} caracteres. Mejor corto y correcto que largo con relleno.
- No usar frases de relleno: ideal para, perfecto para, bonito, precioso, para todo tipo de espacios.
- No incluir SKU/modelo.
- No incluir el nombre de serie salvo que el usuario haya activado explícitamente "incluir serie en título". Serie actual: {get_series_name() or "(vacía)"}.
- No terminar con preposición/conector.
- Nunca escribir "cm" sin número concreto delante. Correcto: "94-140 cm"; incorrecto: "Ajustable cm".
- Usar Title Case español: palabras importantes con inicial mayúscula; de, del, para, con, sin, y, en en minúscula.
- Crear 4 estilos de alta calidad desde la primera ronda:
- Título orientado a venta y SEO, no ficha técnica: incluir como máximo 1 dimensión principal visible (por ejemplo Ø18 cm o Ø45 cm). No poner medidas secundarias como distancia a pared, base, brazo, longitud de cable, altura total o 65 cm salvo que sean el atributo comercial principal del producto.
- No prohibas palabras sueltas por defecto: "interruptor" puede ser keyword útil si es táctil, integrado, USB o función visible; solo evita frases de bajo valor como "interruptor en cable" cuando no sea el principal argumento de venta.
  1) Natural Amazon: fluido, legible, pensado para conversión, sin parecer ficha técnica.
  2) SEO equilibrado: incluye keywords fuertes pero en lenguaje natural.
  3) Diseño/artesanal: enfatiza material, fabricación, estilo y efecto decorativo si son reales.
  4) Corto seguro: breve, claro y estable.
- No crear una lista mecánica de palabras sueltas ni títulos de 40-80 caracteres.
- Leer con cuidado los detalles de producto, imágenes y parámetros confirmados antes de titular.
- Respetar estilo bloqueado. Si el estilo es Retro/Vintage/Cinema, NO escribir moderno/minimalista salvo que el usuario lo permita.
- Resolver colores complejos sin confundir partes: cable, pantalla, base y cuerpo.
- Si el producto usa E27/E14/GU10/G9, en el TÍTULO escribe Casquillo E27/GU10/G9 o E27 G45 si aplica, pero NO escribir en título: compatible, bombilla no incluida, sin bombilla.
- No usar en título palabras vacías: compatible, ideal, perfecto.

Title facts only:
{title_context_for_prompt('ES')}

Política de serie para título: {"INCLUIR serie" if title_should_include_series() else "NO incluir serie en título"}.

Devuelve JSON:
{{"candidates": ["natural...", "seo...", "tecnico...", "corto..."]}}
"""
    raw = llm(prompt, system="You are a strict Amazon.es title specialist. Output JSON only.", temperature=0.35)
    data = safe_json(raw, {"candidates": []})
    cands = data.get("candidates", []) if isinstance(data, dict) else []
    out = []
    # V15.7: AI high-quality candidates first. Deterministic title is only fallback, otherwise it can feel too mechanical.
    det0 = localized_title_from_facts("ES", "")
    for c in cands[:6]:
        c = ensure_title(str(c), "ES", facts_for_prompt("ES"))
        c = spanish_title_case(remove_water_phrases(c))
        if c and c not in out:
            out.append(c)
    if det0 and det0 not in out:
        out.append(det0)
    while len(out) < 4:
        fallback = build_safe_title("ES")
        if fallback not in out:
            out.append(fallback)
        else:
            break
    return out[:4]


def generate_next_title_round(previous_titles: List[str], round_feedback: str = "") -> List[str]:
    """Generate a fresh batch of improved ES titles from the current batch and their detected issues."""
    min_len = int(st.session_state.get("min_title", 140))
    max_len = int(st.session_state.get("max_title", 200))
    diagnostics = []
    for i, t in enumerate(previous_titles, 1):
        sc = score_title_es(t)
        issues = [msg for status, msg in sc.get("checks", []) if status != "通过"]
        diagnostics.append({"candidate": i, "title": t, "score": sc.get("score"), "issues": issues, "auto_fix": auto_title_repair_feedback(t)})
    prompt = f"""
Genera una NUEVA ronda de 4 títulos mejorados para Amazon.es.

Objetivo:
- No repitas literalmente los títulos anteriores.
- Corrige los problemas detectados por el sistema.
- Mantén solo hechos confirmados del producto.
- Haz títulos naturales, comerciales y útiles para SEO, no listas mecánicas.

Reglas duras:
- Todos empiezan por Alpinaluz.
- Longitud objetivo {min_len}-{max_len} caracteres.
- No incluir SKU/modelo.
- No incluir serie salvo que esté activado. Serie actual: {get_series_name() or '(vacía)'}; política: {"INCLUIR" if title_should_include_series() else "NO incluir"}.
- No usar ideal para/perfecto para/bonito/precioso.
- No escribir cm sin número, ni Cm en mayúscula; usar Ø45 cm, 94-140 cm, 28 cm.
- No inventar CCT, USB, bandeja, potencia, material ni dimensiones.
- Si el producto es E27/GU10/G9, el TÍTULO debe usar Casquillo E27/GU10/G9 y potencia/tipo G45 si aporta valor; NO escribir compatible, bombilla no incluida ni sin bombilla en el título.
- Devuelve 4 estilos: natural Amazon, SEO equilibrado, diseño/emoción, corto seguro.

Feedback adicional del usuario:
{round_feedback or '(sin feedback adicional)'}

Títulos anteriores y problemas:
{json.dumps(diagnostics, ensure_ascii=False, indent=2)}

Ficha compacta para título:
{title_context_for_prompt('ES')}

Devuelve JSON:
{{"candidates":["...","...","...","..."]}}
"""
    raw = llm(prompt, system="Especialista senior en títulos Amazon.es para iluminación. Output JSON only.", temperature=0.32)
    data = safe_json(raw, {"candidates": []})
    out = []
    for c in (data.get("candidates", []) if isinstance(data, dict) else [])[:6]:
        c = normalize_title_style(remove_water_phrases(str(c)), "ES")
        c = ensure_title(c, "ES", facts_for_prompt("ES"))
        c = normalize_title_style(c, "ES")
        if c and c not in out:
            out.append(c)
    while len(out) < 4:
        fallback = refine_es_title_with_feedback(previous_titles[0] if previous_titles else build_safe_title("ES"), "Mejorar de forma natural y corregir todos los problemas de puntuación.")
        if fallback not in out:
            out.append(fallback)
        else:
            break
    return out[:4]








def split_keyword_input(raw: str) -> List[str]:
    """Split user custom keywords while preserving useful phrases like Ø45 cm and E27."""
    out = []
    for k in re.split(r"[,，;；\n]+", str(raw or "")):
        k = normalize_title_units(k.strip())
        k = re.sub(r"\s+", " ", k).strip(" ,;，；")
        if k and k.lower() not in [x.lower() for x in out]:
            out.append(k)
    return out


def keyword_key(value: str) -> str:
    """Canonical key for comparing keyword status across reruns and editor rows."""
    v = normalize_title_units(str(value or "")).strip().lower()
    v = re.sub(r"\s+", " ", v)
    return v


def editor_rows_to_records(edited_rows: Any) -> List[Dict[str, Any]]:
    """st.data_editor may return a list of dicts or a dataframe depending on Streamlit/Pandas availability."""
    if edited_rows is None:
        return []
    if hasattr(edited_rows, "to_dict"):
        try:
            return edited_rows.to_dict("records")
        except Exception:
            pass
    try:
        return list(edited_rows)
    except Exception:
        return []


def translate_keyword_concepts(words: List[str], lang: str) -> List[str]:
    """Small deterministic dictionary for the title keyword strategy. LLM still localizes grammar."""
    maps = {
        "lámpara colgante": {"EN":"pendant light", "FR":"suspension", "DE":"Pendelleuchte", "IT":"lampada a sospensione", "NL":"hanglamp", "PL":"lampa wisząca", "PT":"candeeiro suspenso", "SE":"pendellampa"},
        "lámpara de techo": {"EN":"ceiling light", "FR":"lampe de plafond", "DE":"Deckenleuchte", "IT":"lampada da soffitto", "NL":"plafondlamp", "PL":"lampa sufitowa", "PT":"candeeiro de teto", "SE":"taklampa"},
        "ratán natural": {"EN":"natural rattan", "FR":"rotin naturel", "DE":"natürliches Rattan", "IT":"rattan naturale", "NL":"natuurlijk rotan", "PL":"naturalny rattan", "PT":"rattan natural", "SE":"naturrotting"},
        "mimbre natural": {"EN":"natural wicker", "FR":"osier naturel", "DE":"natürliches Weidengeflecht", "IT":"vimini naturale", "NL":"natuurlijk riet", "PL":"naturalna wiklina", "PT":"vime natural", "SE":"naturlig pil"},
        "mimbre": {"EN":"wicker", "FR":"osier", "DE":"Weidengeflecht", "IT":"vimini", "NL":"riet", "PL":"wiklina", "PT":"vime", "SE":"pil"},
        "bambú": {"EN":"bamboo", "FR":"bambou", "DE":"Bambus", "IT":"bambù", "NL":"bamboe", "PL":"bambus", "PT":"bambu", "SE":"bambu"},
        "soporte de madera": {"EN":"wooden support", "FR":"support en bois", "DE":"Holzgestell", "IT":"supporto in legno", "NL":"houten steun", "PL":"drewniany wspornik", "PT":"suporte em madeira", "SE":"trästöd"},
        "madera negra": {"EN":"black wood", "FR":"bois noir", "DE":"schwarzes Holz", "IT":"legno nero", "NL":"zwart hout", "PL":"czarne drewno", "PT":"madeira preta", "SE":"svart trä"},
        "acero negro": {"EN":"black steel", "FR":"acier noir", "DE":"schwarzer Stahl", "IT":"acciaio nero", "NL":"zwart staal", "PL":"czarna stal", "PT":"aço preto", "SE":"svart stål"},
        "diseño artesanal": {"EN":"handcrafted design", "FR":"design artisanal", "DE":"handwerkliches Design", "IT":"design artigianale", "NL":"ambachtelijk ontwerp", "PL":"ręczne wykonanie", "PT":"design artesanal", "SE":"hantverksdesign"},
        "tejida a mano": {"EN":"handwoven", "FR":"tissé à la main", "DE":"handgewebt", "IT":"intrecciato a mano", "NL":"handgeweven", "PL":"ręcznie pleciony", "PT":"tecido à mão", "SE":"handvävd"},
        "moderno nórdico": {"EN":"modern Nordic", "FR":"moderne nordique", "DE":"modern nordisch", "IT":"moderno nordico", "NL":"modern Scandinavisch", "PL":"nowoczesny skandynawski", "PT":"moderno nórdico", "SE":"modern nordisk"},
        "nórdico": {"EN":"Nordic", "FR":"nordique", "DE":"nordisch", "IT":"nordico", "NL":"Scandinavisch", "PL":"skandynawski", "PT":"nórdico", "SE":"nordisk"},
        "rústico": {"EN":"rustic", "FR":"rustique", "DE":"rustikal", "IT":"rustico", "NL":"rustiek", "PL":"rustykalny", "PT":"rústico", "SE":"rustik"},
        "bohemio": {"EN":"bohemian", "FR":"bohème", "DE":"boho", "IT":"bohemien", "NL":"bohemien", "PL":"boho", "PT":"boémio", "SE":"bohemisk"},
        "luz ambiental": {"EN":"ambient lighting", "FR":"lumière d’ambiance", "DE":"Stimmungslicht", "IT":"luce ambiente", "NL":"sfeerverlichting", "PL":"oświetlenie nastrojowe", "PT":"luz ambiente", "SE":"stämningsbelysning"},
        "efecto de sombras": {"EN":"shadow effect", "FR":"effet d’ombres", "DE":"Schattenspiel", "IT":"effetto ombre", "NL":"schaduweffect", "PL":"gra cieni", "PT":"efeito de sombras", "SE":"skuggeffekt"},
        "pantalla de ratán": {"EN":"rattan shade", "FR":"abat-jour en rotin", "DE":"Rattan-Schirm", "IT":"paralume in rattan", "NL":"rotan kap", "PL":"klosz z rattanu", "PT":"cúpula em rattan", "SE":"rottingskärm"},
        "triple pantalla": {"EN":"triple shade", "FR":"triple abat-jour", "DE":"dreifacher Lampenschirm", "IT":"triplo paralume", "NL":"drievoudige kap", "PL":"potrójny klosz", "PT":"abajur triplo", "SE":"trippel skärm"},
        "pantalla triple": {"EN":"triple shade", "FR":"triple abat-jour", "DE":"dreifacher Lampenschirm", "IT":"triplo paralume", "NL":"drievoudige kap", "PL":"potrójny klosz", "PT":"abajur triplo", "SE":"trippel skärm"},
        "triple pantalla Ø45 cm": {"EN":"triple Ø45 cm shade", "FR":"triple abat-jour Ø45 cm", "DE":"dreifacher Lampenschirm Ø45 cm", "IT":"triplo paralume Ø45 cm", "NL":"drievoudige kap Ø45 cm", "PL":"potrójny klosz Ø45 cm", "PT":"abajur triplo Ø45 cm", "SE":"trippel skärm Ø45 cm"},
        "salón": {"EN":"living room", "FR":"salon", "DE":"Wohnzimmer", "IT":"soggiorno", "NL":"woonkamer", "PL":"salon", "PT":"sala", "SE":"vardagsrum"},
        "comedor": {"EN":"dining room", "FR":"salle à manger", "DE":"Esszimmer", "IT":"sala da pranzo", "NL":"eetkamer", "PL":"jadalnia", "PT":"sala de jantar", "SE":"matsal"},
        "dormitorio": {"EN":"bedroom", "FR":"chambre", "DE":"Schlafzimmer", "IT":"camera da letto", "NL":"slaapkamer", "PL":"sypialnia", "PT":"quarto", "SE":"sovrum"},
        "interior": {"EN":"indoor", "FR":"intérieur", "DE":"Innenbereich", "IT":"interno", "NL":"binnen", "PL":"wewnętrzne", "PT":"interior", "SE":"inomhus"},
        "compatible con bombillas LED": {"EN":"LED bulb compatible", "FR":"compatible ampoules LED", "DE":"LED-kompatibel", "IT":"compatibile LED", "NL":"geschikt voor LED", "PL":"kompatybilny z LED", "PT":"compatível LED", "SE":"LED-kompatibel"},
        "bombilla no incluida": {"EN":"bulb not included", "FR":"ampoule non incluse", "DE":"Leuchtmittel nicht enthalten", "IT":"lampadina non inclusa", "NL":"lamp niet inbegrepen", "PL":"żarówka nie jest dołączona", "PT":"lâmpada não incluída", "SE":"lampa ingår ej"},
    }
    out = []
    for w in words or []:
        w_norm = normalize_title_units(str(w).strip())
        if not w_norm:
            continue
        lw = w_norm.lower()
        val = None
        for k, mp in maps.items():
            if lw == k or lw in k or k in lw:
                val = mp.get(lang)
                break
        if not val:
            # Technical codes and sizes are universal.
            if re.search(r"\b(E27|E14|GU10|G9|GX53|G4|LED|IP\d{2}|\d+W|Ø?\d+(?:[.,]\d+)?\s*cm)\b", w_norm, flags=re.I):
                val = normalize_title_units(w_norm)
            else:
                val = w_norm
        if val and val not in out:
            out.append(val)
    return out


def has_extra_local_concept(title: str, lang: str, es_title: str, must_words: List[str]) -> bool:
    """Reject common local-title additions absent from the final ES title and not selected as must concepts."""
    t = normalize_title_units(str(title or "")).lower()
    e = normalize_title_units(str(es_title or "")).lower()
    must_blob = " ".join([normalize_title_units(str(x)).lower() for x in (must_words or [])])
    concepts = [
        ("dormitorio", {"EN":["bedroom"], "FR":["chambre"], "DE":["schlafzimmer"], "IT":["camera da letto"], "NL":["slaapkamer"], "PL":["sypialnia"], "PT":["quarto"], "SE":["sovrum"]}),
        ("salón", {"EN":["living room"], "FR":["salon"], "DE":["wohnzimmer"], "IT":["soggiorno"], "NL":["woonkamer"], "PL":["salon"], "PT":["sala"], "SE":["vardagsrum"]}),
        ("comedor", {"EN":["dining room"], "FR":["salle à manger"], "DE":["esszimmer"], "IT":["sala da pranzo"], "NL":["eetkamer"], "PL":["jadalnia"], "PT":["sala de jantar"], "SE":["matsal"]}),
        ("mimbre", {"EN":["wicker"], "FR":["osier"], "DE":["weidengeflecht"], "IT":["vimini"], "NL":["riet"], "PL":["wiklina", "mimbre"], "PT":["vime"], "SE":["pil"]}),
        ("bambú", {"EN":["bamboo"], "FR":["bambou"], "DE":["bambus"], "IT":["bambù"], "NL":["bamboe"], "PL":["bambus"], "PT":["bambu"], "SE":["bambu"]}),
        ("60w", {"EN":["60w"], "FR":["60w"], "DE":["60w"], "IT":["60w"], "NL":["60w"], "PL":["60w"], "PT":["60w"], "SE":["60w"]}),
        ("led", {"EN":["led"], "FR":["led"], "DE":["led"], "IT":["led"], "NL":["led"], "PL":["led"], "PT":["led"], "SE":["led"]}),
    ]
    for es_concept, local_map in concepts:
        local_terms = local_map.get(lang, [])
        if not local_terms:
            continue
        appears_local = any(term in t for term in local_terms)
        allowed = (es_concept in e) or (es_concept in must_blob) or any(term in must_blob for term in local_terms)
        if appears_local and not allowed:
            return True
    return False


def add_custom_keywords_to_state(raw: str, as_must: bool = True) -> List[str]:
    """Persist custom keywords so they reappear as selected red chips in the next round."""
    words = split_keyword_input(raw)
    if not words:
        return []
    pool = st.session_state.setdefault("title_custom_keyword_pool", [])
    existing = {str(x.get("phrase", "")).lower(): x for x in pool if isinstance(x, dict)}
    for w in words:
        if w.lower() not in existing:
            pool.append({"phrase": w, "cn": "自定义关键词/由用户补充"})
    st.session_state["title_custom_keyword_pool"] = pool
    if as_must:
        must = list(st.session_state.get("title_must_keywords", []))
        low = {m.lower() for m in must}
        for w in words:
            if w.lower() not in low:
                must.append(w)
                low.add(w.lower())
        st.session_state["title_must_keywords"] = must
    return words


def merge_keyword_pool(pool: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Merge AI/fact keywords with persistent custom/must/banned terms."""
    merged = []
    seen = set()
    def add(phrase: str, cn: str):
        phrase = normalize_title_units(str(phrase or "").strip())
        phrase = re.sub(r"\s+", " ", phrase).strip(" ,;，；")
        if not phrase:
            return
        key = phrase.lower()
        if key in seen:
            return
        merged.append({"phrase": phrase, "cn": cn or "关键词"})
        seen.add(key)
    for x in pool:
        add(x.get("phrase", ""), x.get("cn", ""))
    for x in st.session_state.get("title_custom_keyword_pool", []):
        if isinstance(x, dict):
            add(x.get("phrase", ""), x.get("cn", "自定义关键词"))
    for w in st.session_state.get("title_must_keywords", []):
        add(w, "已选必须关键词")
    for w in st.session_state.get("title_banned_keywords", []):
        add(w, "已设为禁止关键词")
    return merged


def keyword_sort_key(item: Dict[str, str]) -> Tuple[int, int, str]:
    phrase = item.get("phrase", "")
    must = {x.lower() for x in st.session_state.get("title_must_keywords", [])}
    ban = {x.lower() for x in st.session_state.get("title_banned_keywords", [])}
    key = phrase.lower()
    group = 0 if key in must else (2 if key in ban else 1)
    priority_words = ["lámpara", "colgante", "ratán", "mimbre", "bambú", "madera", "acero", "e27", "60w", "ø", "cm", "nórdico", "artesanal", "salón", "comedor", "dormitorio"]
    pri = next((i for i, w in enumerate(priority_words) if w in key), 99)
    return (group, pri, key)


def contains_banned_keyword(title: str, banned: List[str]) -> bool:
    t = normalize_title_units(str(title or "")).lower()
    for b in banned or []:
        b = normalize_title_units(str(b or "").strip()).lower()
        if not b:
            continue
        # Phrase-level containment is intentional: user says forbidden means must not appear.
        if b in t:
            return True
    return False


def add_custom_keywords_as_banned(raw: str) -> List[str]:
    """Persist custom keywords as negative terms and remove them from must terms."""
    words = split_keyword_input(raw)
    if not words:
        return []
    # Keep them visible in the pool as custom terms.
    add_custom_keywords_to_state(raw, as_must=False)
    banned = list(st.session_state.get("title_banned_keywords", []))
    must = list(st.session_state.get("title_must_keywords", []))
    ban_low = {x.lower() for x in banned}
    words_low = {w.lower() for w in words}
    for w in words:
        if w.lower() not in ban_low:
            banned.append(w)
            ban_low.add(w.lower())
    must = [m for m in must if m.lower() not in words_low]
    st.session_state["title_banned_keywords"] = banned
    st.session_state["title_must_keywords"] = must
    return words


def expand_title_keyword_phrase(word: str) -> List[str]:
    """Convert long custom phrases into usable SEO concepts so many must/ban terms do not collapse the title."""
    w = normalize_title_units(str(word or "").strip())
    if not w:
        return []
    low = w.lower()
    # Short, natural phrases are kept as-is.
    if len(w) <= 42 and len(w.split()) <= 6:
        return [w]
    out = []
    def add(x):
        x = normalize_title_units(x)
        if x and keyword_key(x) not in {keyword_key(y) for y in out}:
            out.append(x)
    patterns = [
        (r"l[aá]mpara\s+colgante", "lámpara colgante"), (r"l[aá]mpara\s+de\s+techo", "lámpara de techo"),
        (r"rat[aá]n\s+natural", "ratán natural"), (r"\brat[aá]n\b", "ratán"),
        (r"mimbre\s+natural", "mimbre natural"), (r"\bmimbre\b", "mimbre"),
        (r"\bbamb[uú]\b", "bambú"), (r"soporte\s+de\s+madera", "soporte de madera"),
        (r"acero\s+negro", "acero negro"), (r"dise[nñ]o\s+artesanal", "diseño artesanal"),
        (r"tejid[ao]\s+a\s+mano", "tejida a mano"), (r"moderno\s+n[oó]rdico", "moderno nórdico"),
        (r"\bn[oó]rdico\b", "nórdico"), (r"\br[uú]stico\b", "rústico"), (r"\bbohemio\b", "bohemio"),
        (r"luz\s+ambiental", "luz ambiental"), (r"efecto\s+de\s+sombras", "efecto de sombras"),
        (r"triple\s+pantalla|pantalla\s+triple", "triple pantalla"), (r"pantalla\s+de\s+rat[aá]n", "pantalla de ratán"),
        (r"\bsal[oó]n\b", "salón"), (r"\bcomedor\b", "comedor"), (r"\bdormitorio\b", "dormitorio"),
        (r"\binterior\b", "interior"), (r"bombilla\s+no\s+incluida", "bombilla no incluida"),
        (r"compatible\s+con\s+bombillas?\s+LED|compatible\s+LED|LED\s+compatible", "compatible con bombillas LED"),
    ]
    for pat, val in patterns:
        if re.search(pat, low, flags=re.I):
            add(val)
    for m in re.findall(r"\b(E27|E14|GU10|G9|GX53|G4|IP\d{2}|LED)\b", w, flags=re.I):
        add(m.upper())
    for m in re.findall(r"\b\d{1,3}\s*W\b", w, flags=re.I):
        add(normalize_title_units(m))
    for m in re.findall(r"Ø?\d+(?:[.,]\d+)?\s*cm", w, flags=re.I):
        add(normalize_title_units(m))
    return out or [w[:42].strip()]


def sanitize_title_keywords(words: List[str], banned: List[str] = None, max_items: int = 14) -> List[str]:
    """Reduce noisy long must/ban keyword lists into ordered title concepts."""
    banned_keys = {keyword_key(x) for x in (banned or [])}
    expanded = []
    for w in words or []:
        for x in expand_title_keyword_phrase(w):
            if keyword_key(x) and keyword_key(x) not in banned_keys and keyword_key(x) not in {keyword_key(y) for y in expanded}:
                expanded.append(x)
    def rank(x: str) -> Tuple[int, int]:
        k = keyword_key(x)
        groups = [
            ["lámpara colgante", "lámpara de techo"],
            ["ratán", "mimbre", "bambú", "madera", "acero"],
            ["soporte", "pantalla", "triple"],
            ["ø", " cm", "38 cm", "45 cm"],
            ["nórdico", "artesanal", "rústico", "bohemio", "natural"],
            ["e27", "e14", "gu10", "g9", "60w", "led"],
            ["salón", "comedor", "dormitorio", "interior"],
        ]
        for gi, terms in enumerate(groups):
            if any(t in k for t in terms):
                return (gi, len(k))
        return (8, len(k))
    return sorted(expanded, key=rank)[:max_items]


def sanitize_banned_keywords(words: List[str], max_items: int = 18) -> List[str]:
    """Banned terms should not over-expand into essential specs.
    Example: banning a long phrase about LED compatibility should block that phrase,
    but should not automatically ban E27 or 60W unless the user entered them as separate terms.
    """
    out = []
    def add(x):
        x = normalize_title_units(str(x or "").strip())
        x = re.sub(r"\s+", " ", x).strip(" ,;，；")
        if x and keyword_key(x) not in {keyword_key(y) for y in out}:
            out.append(x)
    for w in words or []:
        w = normalize_title_units(str(w or "").strip())
        if not w:
            continue
        low = w.lower()
        if len(w) <= 42 and len(w.split()) <= 6:
            add(w)
            continue
        # Keep phrase-level intent without banning useful technical tokens such as E27/60W by accident.
        if "compatible" in low and "led" in low:
            add("compatible con bombillas LED")
        if "bombilla incluida" in low or "incluye bombilla" in low:
            add("bombilla incluida")
            add("incluye bombilla")
        # Extract only commonly wrong concepts from long negative text.
        for pat, val in [
            (r"\bbamb[uú]\b", "bambú"), (r"\bindustrial\b", "industrial"), (r"\bmoderno\b", "moderno"),
            (r"\bminimalista\b", "minimalista"), (r"\bbandeja\b", "bandeja"), (r"\bCCT\b", "CCT"),
            (r"\bUSB\b", "USB"), (r"spotlight|foco", "foco"), (r"\bnegro\b", "negro"),
        ]:
            if re.search(pat, w, flags=re.I):
                add(val)
        # Retain the long exact phrase in shortened form as a phrase ban.
        if len(w) <= 90:
            add(w)
    return out[:max_items]

def remove_banned_from_title(title: str, banned: List[str]) -> str:
    t = str(title or "")
    for b in (banned or []):
        b = normalize_title_units(str(b or "").strip())
        if not b:
            continue
        t = re.sub(rf"(?i)\b{re.escape(b)}\b", "", t)
    t = re.sub(r"\s+,", ",", re.sub(r"\s{2,}", " ", t)).strip(" ,;-–—")
    return t


def title_component_allowed(component: str, banned: List[str]) -> bool:
    return bool(component and not contains_banned_keyword(component, banned))


def robust_title_from_keywords(kws: List[str], banned: List[str], variant: int = 0) -> str:
    """Deterministic, complete title when LLM output is over-constrained by many must/ban terms."""
    max_len = int(st.session_state.get("max_title", 200))
    min_len = int(st.session_state.get("min_title", 160))
    brand = get_field("品牌") or "Alpinaluz"
    clean_ban = sanitize_title_keywords(banned, max_items=30)
    keys = sanitize_title_keywords(kws, clean_ban, max_items=18)
    blob = " ".join(keys).lower()

    product = "Lámpara Colgante" if ("colgante" in blob or "吊灯" in get_field("产品类型")) else (map_value("产品类型", get_field("产品类型"), "ES") or "Lámpara")
    material_bits = []
    if "mimbre" in blob: material_bits.append("Mimbre Natural")
    if "ratán" in blob or "ratan" in blob: material_bits.append("Ratán Natural")
    if "bambú" in blob or "bambu" in blob: material_bits.append("Bambú")
    if not material_bits:
        mat = map_value("材质", get_field("材质"), "ES") or ""
        if mat and len(mat) < 40: material_bits.append(mat)
    # Avoid overlong repeated natural materials.
    if "Mimbre Natural" in material_bits and "Ratán Natural" in material_bits:
        mat_phrase = "Ratán y Mimbre Natural"
    else:
        mat_phrase = " y ".join(material_bits[:2])

    support_bits = []
    if "soporte de madera" in blob or "madera" in blob: support_bits.append("Soporte de Madera")
    if "acero negro" in blob: support_bits.append("Acero Negro")
    support_phrase = " con " + " y ".join(support_bits[:2]) if support_bits else ""

    size = ""
    for k in keys:
        if re.search(r"Ø?\d+(?:[.,]\d+)?\s*cm", k, flags=re.I):
            size = normalize_title_units(k)
            break
    if not size:
        size = size_phrase_for_title("ES") or clean_size_value(get_fact("Diámetro") or get_fact("直径"))
    if size and not size.startswith("Ø") and "diámetro" not in size.lower() and re.search(r"\d", size):
        size = "Ø" + size if "x" not in size.lower() else size

    style_bits = []
    if "moderno nórdico" in blob or "nórdico" in blob: style_bits.append("Diseño Moderno Nórdico")
    if "artesanal" in blob or "tejida" in blob: style_bits.append("Diseño Artesanal")
    if "rústico" in blob: style_bits.append("Estilo Rústico")
    if "bohemio" in blob: style_bits.append("Bohemio")
    style_phrase = " ".join(style_bits[:2])

    shade = "Triple Pantalla" if ("triple pantalla" in blob or "pantalla triple" in blob) else ""
    socket = "E27" if "e27" in blob else (map_value("灯头", get_field("灯头"), "ES") or "")
    power = ""
    for k in keys:
        if re.search(r"\b\d+W\b", k, flags=re.I):
            power = normalize_title_units(k)
            break
    rooms = []
    if "salón" in blob: rooms.append("Salón")
    if "comedor" in blob: rooms.append("Comedor")
    if "dormitorio" in blob: rooms.append("Dormitorio")
    if not rooms:
        room = map_value("适用空间", get_field("适用空间"), "ES") or ""
        rooms = [x.strip().title() for x in re.split(r"[,/，、]", room) if x.strip()][:2]
    room_phrase = " para " + " y ".join(rooms[:3]) if rooms else ""

    if variant % 4 == 0:
        parts = [brand, product, "de " + mat_phrase if mat_phrase else "", size, support_phrase.strip(), style_phrase, shade, socket, ("hasta " + power if power and socket else ""), room_phrase.strip()]
    elif variant % 4 == 1:
        parts = [brand, product, mat_phrase, support_phrase.strip(), shade, size, style_phrase, socket, room_phrase.strip()]
    elif variant % 4 == 2:
        parts = [brand, product, style_phrase, "de " + mat_phrase if mat_phrase else "", support_phrase.strip(), size, socket, room_phrase.strip()]
    else:
        parts = [brand, product, mat_phrase, size, socket, style_phrase, room_phrase.strip()]
    title = " ".join([p for p in parts if p]).replace(" con con ", " con ")
    title = remove_banned_from_title(title, clean_ban)
    title = normalize_title_style(spanish_title_case(title), "ES")
    title = re.sub(r"\s+", " ", title).strip(" ,;-–—")
    # If too short, add true generic commercial descriptors rather than collapsing to a keyword fragment.
    additions = ["Iluminación Ambiental Interior", "Decoración Natural", "Compatible con Bombillas LED"]
    for add in additions:
        if len(title) >= min(min_len, 150):
            break
        candidate = f"{title}, {add}"
        if len(candidate) <= max_len and title_component_allowed(add, clean_ban):
            title = candidate
    # If too long, remove low priority tail pieces safely.
    while len(title) > max_len and "," in title:
        title = title.rsplit(",", 1)[0].strip()
    if len(title) > max_len:
        words = title.split()
        while words and len(" ".join(words)) > max_len:
            words.pop()
        title = " ".join(words).strip(" ,;-–—")
    return normalize_title_style(title, "ES")

def replace_listing_title(text: str, new_title: str) -> str:
    """Replace only the [TITLE] body inside a composed listing text."""
    new_title = normalize_title_style(clean_title_candidate(new_title), "ES")
    if not str(text or "").strip() or not new_title:
        return text
    pattern = r"(\[TITLE\]\s*)(.*?)(?=\n\[[^\n]+\]|\Z)"
    return re.sub(pattern, lambda m: m.group(1) + new_title + "\n", text, count=1, flags=re.S)


def keyword_state_signature() -> str:
    must = sorted([normalize_title_units(str(x)).lower() for x in st.session_state.get("title_must_keywords", []) if str(x).strip()])
    ban = sorted([normalize_title_units(str(x)).lower() for x in st.session_state.get("title_banned_keywords", []) if str(x).strip()])
    return json.dumps({"must": must, "ban": ban}, ensure_ascii=False)


def strict_translate_es_title_no_facts(lang: str, es_title: str, must: List[str], ban: List[str]) -> str:
    """Last safe fallback: translate only the locked ES title, no fact-card enrichment."""
    brand = st.session_state.get("brand", "Alpinaluz") or "Alpinaluz"
    max_len = int(st.session_state.get("max_title", 200))
    prompt = f"""
Translate/localize this final locked Amazon.es title into native {LANGS[lang]['name']} for {LANGS[lang]['market']}.

Final ES title:
{es_title}

Must concepts selected by user, localize naturally if present or applicable:
{json.dumps(translate_keyword_concepts(must, lang), ensure_ascii=False)}

Negative concepts, do not use:
{json.dumps(translate_keyword_concepts(ban, lang), ensure_ascii=False)}

Rules:
- Start with exactly: {brand}
- Use ONLY facts from the ES title plus selected must concepts. Do not add other facts from memory.
- No Chinese, no placeholders, no Spanish leftovers.
- Do not include bedroom/Schlafzimmer/sypialnia etc if the ES title does not contain dormitorio and user did not select it.
- Do not include 60W/LED/mimbre/bamboo if the ES title/user must keywords do not contain that concept.
- Natural Amazon title, not a keyword list. Max {max_len} characters.
Return one line only.
"""
    try:
        raw = llm(prompt, system="Strict marketplace title translator. One line only.", temperature=0.05)
        title = localize_foreign_leftovers(normalize_title_style(clean_variants(clean_title_candidate(raw.splitlines()[0]), lang, "TITLE"), lang), lang)
        if title and not title.lower().startswith(brand.lower()):
            title = f"{brand} {re.sub(r'(?i)^alpinaluz\s*', '', title).strip()}"
        return title
    except Exception:
        return localized_title_from_facts(lang, es_title)


def foreign_title_from_keyword_strategy(lang: str, es_title: str) -> str:
    """V16.6: stable foreign title from ES semantic skeleton.
    The old tri-state keyword table is no longer the primary algorithm; it is only an advanced reference.
    This avoids slow/expensive title localization and broken fragments such as with -Effect / mit -Leuchtmitteln.
    """
    es_title = clean_title_candidate(es_title)
    if not es_title:
        return localized_title_from_facts(lang, es_title)
    max_len = int(st.session_state.get("max_title", 200))
    cache = st.session_state.setdefault("title_translation_cache", {})
    cache_key = f"skeleton_v169::{lang}::{es_title}::{max_len}"
    if cache_key in cache:
        return cache[cache_key]
    title = title_from_semantic_skeleton(lang, es_title)
    title = localize_foreign_leftovers(fix_broken_title_fragments(title, lang), lang)
    title = normalize_title_style(fix_broken_title_fragments(clean_variants(clean_title_candidate(title), lang, "TITLE"), lang), lang)
    # If skeleton title is unexpectedly weak, use strict translation as backup, but still pass through hard guards.
    if not foreign_title_is_usable(title, lang, es_title):
        try:
            backup = strict_translate_es_title_no_facts(lang, es_title, [], [])
            backup = normalize_title_style(fix_broken_title_fragments(localize_foreign_leftovers(clean_variants(backup, lang, "TITLE"), lang), lang), lang)
            if foreign_title_is_usable(backup, lang, es_title):
                title = backup
        except Exception:
            pass
    if len(title) > max_len:
        # Do not hard-cut through useful phrases. Drop the lowest-priority tail after the last comma.
        parts = [x.strip() for x in re.split(r",\s*", title) if x.strip()]
        while len(", ".join(parts)) > max_len and len(parts) > 2:
            parts.pop()
        title = ", ".join(parts)
        if len(title) > max_len:
            title = title[:max_len].rsplit(" ", 1)[0].strip(" ,;-–—")
    title = normalize_title_style(fix_broken_title_fragments(title, lang), lang)
    cache[cache_key] = title
    return title


def render_keyword_chips(title: str, words: List[str], css_class: str):
    words = [w for w in words if str(w).strip()]
    if not words:
        return
    chips = "".join(f"<span class='kw-chip {css_class}'>{w}</span>" for w in words[:30])
    st.markdown(f"<div class='kw-chip-row'><b>{title}</b>&nbsp;{chips}</div>", unsafe_allow_html=True)

def title_keyword_pool_es(candidates: List[str]) -> List[Dict[str, str]]:
    """关键词池：给新手点选，不需要懂西语。"""
    text = " \n".join(candidates + [facts_for_prompt("ES"), st.session_state.get("manual_title", ""), st.session_state.get("keywords", "")])
    base = [
        ("lámpara colgante", "吊灯/悬挂灯，产品类型核心词"), ("lámpara de techo", "天花灯/吊顶灯，补充搜索词"),
        ("ratán natural", "天然藤条/藤编材质"), ("mimbre natural", "天然柳条/藤编材质，西班牙常用搜索词"),
        ("bambú", "竹/自然材质，如果产品确实是竹才选"), ("madera negra", "黑色木质支架/底座"),
        ("soporte de madera", "木质支架"), ("acero negro", "黑色钢结构，只有确实有钢材才选"),
        ("diseño artesanal", "手工制作/手工感"), ("tejida a mano", "手工编织"),
        ("moderno nórdico", "现代北欧风格"), ("estilo natural", "自然风格"), ("bohemio", "波西米亚/boho风格"),
        ("rústico", "乡村/自然质朴风格"), ("luz ambiental", "环境光/氛围照明"),
        ("efecto de sombras", "藤编投射光影效果"), ("E27", "E27灯头"),
        ("compatible con bombillas LED", "兼容LED灯泡"), ("bombilla no incluida", "灯泡不含，标题通常可不写但安全"),
        ("hasta 60W", "最高60W"), ("Ø45 cm", "直径45厘米"), ("38 cm", "高度38厘米"),
        ("salón", "客厅"), ("comedor", "餐厅"), ("dormitorio", "卧室"), ("interior", "室内使用"),
        ("decoración sostenible", "可持续/环保装饰方向"), ("pantalla de ratán", "藤编灯罩"),
    ]
    # Include fact-based exact values as selectable options.
    for n in re.findall(r"Ø?\d+(?:[.,]\d+)?\s*cm", text, flags=re.I):
        base.append((normalize_title_units(n), "资料中出现的尺寸关键词"))
    socket = map_value("灯头", get_field("灯头"), "ES")
    if socket:
        base.append((socket, "灯头/光源接口"))
    # Add phrases that actually appear in current candidate titles first, then merge persistent custom/must/banned terms.
    out = []
    seen = set()
    low_text = text.lower()
    for phrase, cn in base:
        if phrase.lower() in low_text or phrase in {"lámpara colgante", socket, "E27"}:
            key = phrase.lower()
            if phrase and key not in seen:
                out.append({"phrase": phrase, "cn": cn})
                seen.add(key)
    out = merge_keyword_pool(out)
    out = sorted(out, key=keyword_sort_key)
    return out[:60]


def generate_next_title_round_from_keywords(selected_keywords: List[str], custom_keywords: str = "", banned_keywords: List[str] = None) -> List[str]:
    min_len = int(st.session_state.get("min_title", 160))
    max_len = int(st.session_state.get("max_title", 200))
    raw_banned = [normalize_title_units(str(x).strip()) for x in (banned_keywords or []) if str(x).strip()]
    raw_kws = [normalize_title_units(k.strip()) for k in selected_keywords if str(k).strip()]
    for k in split_keyword_input(custom_keywords or ""):
        if k and keyword_key(k) not in {keyword_key(x) for x in raw_kws}:
            raw_kws.append(k)
    # Negative list wins in exact conflicts, but long phrases are reduced to concepts for generation.
    banned_concepts = sanitize_banned_keywords(raw_banned, max_items=18)
    kws = sanitize_title_keywords(raw_kws, banned_concepts, max_items=16)
    # Always include basic must-have facts if available.
    baseline = ["lámpara colgante" if "吊灯" in get_field("产品类型") else "", map_value("灯头", get_field("灯头"), "ES"), size_phrase_for_title("ES")]
    for must in baseline:
        if must and keyword_key(must) not in {keyword_key(x) for x in kws} and keyword_key(must) not in {keyword_key(b) for b in banned_concepts}:
            kws.append(must)
    kws = sanitize_title_keywords(kws, banned_concepts, max_items=16)
    deterministic = [robust_title_from_keywords(kws, banned_concepts, i) for i in range(4)]
    prompt = f"""
Genera una nueva ronda de 4 títulos de Amazon.es a partir de las palabras clave elegidas por el usuario.
El usuario es principiante: las keywords elegidas son señales semánticas, NO deben pegarse como una lista mecánica ni obligan a repetir frases largas literalmente.

Keywords importantes seleccionadas por el usuario. Deben aparecer de forma natural si son verdaderas y caben; si hay demasiadas, prioriza producto, material, tamaño, estilo, casquillo y estancia:
{json.dumps(kws, ensure_ascii=False)}

Keywords/frases negativas prohibidas. No deben aparecer ni sus equivalentes obvios:
{json.dumps(banned_concepts, ensure_ascii=False)}

Títulos deterministas seguros que puedes usar como referencia de estructura, pero mejorándolos con lenguaje natural:
{json.dumps(deterministic, ensure_ascii=False)}

Hechos compactos para título:
{title_context_for_prompt('ES')}

Reglas obligatorias:
- Cada título empieza por Alpinaluz.
- Títulos naturales, comerciales y orientados a conversión; no lista de palabras sueltas.
- Longitud objetivo {min_len}-{max_len} caracteres. Prohibido generar títulos de 40-100 caracteres salvo que el usuario haya seleccionado muy pocos datos.
- No incluir serie salvo que esté activado. Serie: {get_series_name() or '(vacía)'}; política: {'INCLUIR' if title_should_include_series() else 'NO incluir'}.
- No SKU/modelo, no 'ideal para'/'perfecto para', no cm sin número.
- Usar cm en minúscula: Ø45 cm x 38 cm.
- En título no escribir compatible, bombilla no incluida ni sin bombilla; usar solo Casquillo E27/GU10/G9, E27 G45 o hasta 40W/60W si es un dato útil y confirmado.
- No inventar bandeja, CCT, USB, spotlight, orientación ni materiales no confirmados.
- No incluir ninguna keyword negativa ni sus variantes obvias; si una keyword negativa aparece en el título, el título es inválido.
- Orden natural recomendado: marca + tipo de producto + material/forma + una dimensión principal visible si aporta SEO + soporte/estructura + estilo + casquillo + estancias. No convertir el título en ficha técnica con base/cable/distancia/altura secundaria.
- Devuelve 4 estilos: natural Amazon, SEO equilibrado, diseño/artesanal, corto seguro pero no fragmento.

Devuelve JSON exacto:
{{"candidates":["...","...","...","..."]}}
"""
    try:
        raw = llm(prompt, system="Senior Amazon.es SEO title editor for lighting products. Output JSON only.", temperature=0.24)
        data = safe_json(raw, {"candidates": []})
        raw_candidates = data.get("candidates", []) if isinstance(data, dict) else []
    except Exception:
        raw_candidates = []
    out = []
    min_accept = max(120, min_len - 25)
    for c in raw_candidates[:8]:
        c = normalize_title_style(remove_water_phrases(str(c)), "ES")
        c = ensure_title(c, "ES", facts_for_prompt("ES"))
        c = normalize_title_style(c, "ES")
        if c and len(c) >= min_accept and not contains_banned_keyword(c, banned_concepts) and c not in out:
            out.append(c)
    # Fill with deterministic complete variants rather than short safe fragments.
    for det in deterministic:
        det = normalize_title_style(det, "ES")
        if det and len(det) >= min_accept and not contains_banned_keyword(det, banned_concepts) and det not in out:
            out.append(det)
    # Last resort: allow deterministic at >=100 chars, never 40-char fragments.
    for det in deterministic:
        if len(out) >= 4:
            break
        det = normalize_title_style(det, "ES")
        if det and len(det) >= 100 and not contains_banned_keyword(det, banned_concepts) and det not in out:
            out.append(det)
    # Absolute fallback if constraints are contradictory: keep product facts and ignore low-priority musts, but still avoid banned terms.
    variant = 0
    while len(out) < 4 and variant < 8:
        fb = robust_title_from_keywords(kws[:8], banned_concepts, variant)
        if fb and len(fb) >= 100 and not contains_banned_keyword(fb, banned_concepts) and fb not in out:
            out.append(fb)
        variant += 1
    return out[:4]


def generate_next_title_round_from_selected(selected_titles: List[str], all_titles: List[str], round_feedback: str = "") -> List[str]:
    """Beginner-friendly title evolution: choose good candidates, then synthesize better titles."""
    min_len = int(st.session_state.get("min_title", 140))
    max_len = int(st.session_state.get("max_title", 200))
    selected_titles = [clean_title_candidate(t) for t in selected_titles if str(t).strip()]
    all_titles = [clean_title_candidate(t) for t in all_titles if str(t).strip()]
    if not selected_titles:
        ranked = sorted(all_titles, key=lambda t: score_title_es(t).get("score", 0), reverse=True)
        selected_titles = ranked[:2] or [build_safe_title("ES")]
    diagnostics = []
    for i, t in enumerate(all_titles, 1):
        sc = score_title_es(t)
        diagnostics.append({"candidate": i, "title": t, "score": sc.get("score"), "issues": [m for stt, m in sc.get("checks", []) if stt != "通过"]})
    selected_diagnostics = []
    for t in selected_titles:
        sc = score_title_es(t)
        selected_diagnostics.append({"title": t, "score": sc.get("score"), "issues": [m for stt, m in sc.get("checks", []) if stt != "通过"]})
    prompt = f"""
You are helping a beginner choose the best Amazon.es title for a lighting product.
The user selected the comparatively best candidates below. Analyze their common strengths, discard their weaknesses, and generate 4 improved titles.

Selected titles the user liked:
{json.dumps(selected_diagnostics, ensure_ascii=False, indent=2)}

All previous candidates and detected issues:
{json.dumps(diagnostics, ensure_ascii=False, indent=2)}

Extra user direction:
{round_feedback or '(none)'}

Compact title facts:
{title_context_for_prompt('ES')}

Hard rules:
- Generate 4 complete, natural Amazon.es titles, not keyword fragments.
- Each title MUST start with Alpinaluz.
- Target length {min_len}-{max_len} characters. Do not produce a very short title unless the facts truly require it.
- Do not include SKU/model.
- Do not include series name unless explicitly allowed. Series: {get_series_name() or '(empty)'}; policy: {'INCLUDE' if title_should_include_series() else 'DO NOT INCLUDE'}.
- Never write bare cm. Correct: Ø45 cm, 53-62 cm, 94-140 cm. Incorrect: Ajustable Cm, Ø45 Cm.
- Use cm/mm lowercase.
- Avoid filler: ideal para, perfecto para, bonito, precioso.
- Keep only true facts; do not invent CCT/USB/bandeja/spot/degree if not in confirmed facts.
- For E27/GU10/G9 products, do NOT put compatible/bulb not included in the title. Use socket type and max wattage only if useful. Bulb exclusion belongs in bullets/description.
- Include high-value SEO facts when true: product type, material, style, size, socket/light type, main rooms.
- Return 4 different styles: Natural Amazon, SEO balance, design/emotional, concise safe.

Return JSON only:
{{"candidates":["...","...","...","..."]}}
"""
    raw = llm(prompt, system="Senior Amazon.es lighting title editor. Output strict JSON only.", temperature=0.28)
    data = safe_json(raw, {"candidates": []})
    out = []
    for c in (data.get("candidates", []) if isinstance(data, dict) else [])[:8]:
        c = normalize_title_style(remove_water_phrases(str(c)), "ES")
        c = ensure_title(c, "ES", facts_for_prompt("ES"))
        c = normalize_title_style(c, "ES")
        if len(c) < max(100, min_len - 35):
            continue
        if c and c not in out:
            out.append(c)
    old_mode = st.session_state.get("title_format_mode", "自然亚马逊标题（推荐）")
    for mode in ["自然亚马逊标题（推荐）", "SEO长标题", "简洁安全标题", "结构化特性标题（技术款）"]:
        if len(out) >= 4:
            break
        st.session_state["title_format_mode"] = mode
        fb = build_safe_title("ES")
        st.session_state["title_format_mode"] = old_mode
        if fb and fb not in out:
            out.append(fb)
    st.session_state["title_format_mode"] = old_mode
    return out[:4]


def refine_es_title_with_feedback(base_title: str, feedback: str) -> str:
    """Rewrite one selected ES title using nearby feedback, not distant technical notes."""
    min_len = int(st.session_state.get("min_title", 140))
    max_len = int(st.session_state.get("max_title", 200))
    prompt = f"""
Reescribe este título de Amazon.es aplicando exactamente las mejoras indicadas por el usuario.

Título base:
{base_title}

Correcciones solicitadas:
{feedback}

Reglas duras:
- Mantener Alpinaluz al inicio.
- No truncar. No terminar con con/de/para/y/en ni con coma.
- No incluir SKU.
- No incluir el nombre de serie salvo que el usuario haya activado explícitamente incluir serie en título. Serie actual: {get_series_name() or "(vacía)"}.
- No usar relleno como ideal para/perfecto para.
- Si el usuario pide una frase concreta, incorpórala corrigiendo unidades y gramática. Ejemplo: "94-140 Cm" debe quedar "94-140 cm".
- Nunca escribir "cm" sin un número concreto delante; si no hay número fiable, elimina "cm".
- Longitud objetivo {min_len}-{max_len} caracteres; si no cabe, prioriza precisión y naturalidad.
- Respetar los hechos del producto, especialmente color, LED integrado/CCT, USB, bandeja, potencia y medidas.
- Usar Title Case español: palabras importantes con inicial mayúscula; de, del, para, con, sin, y, en en minúscula.
- Usar formato legible de Amazon, no una lista de palabras: “Alpinaluz Producto – Característica: detalle, Característica: detalle”.
- Recomendado para productos técnicos: “Luz CCT: 3000K/4000K/6000K”, “Foco Orientable: 350°”, “Carga: USB-A y USB-C”, “Bandeja: 28 cm”.

Hechos del producto:
{facts_for_prompt('ES')}

Devuelve solo el título final, sin explicación.
"""
    title = llm(prompt, system="Especialista en títulos Amazon.es. Devuelve una sola línea.", temperature=0.18).splitlines()[0]
    title = ensure_title(title, "ES", facts_for_prompt("ES"))
    return spanish_title_case(remove_water_phrases(title))



def chat_title_workspace_round(base_title: str, user_message: str, n: int = 3) -> List[str]:
    """V16.6: Chat-like ES title workshop.
    Uses a compact title-only context, like the successful ChatGPT workflow: one current title + one instruction + locked facts.
    It does NOT read full long description/A+ repeatedly, so it is cheaper and less likely to drag low-value specs into the title.
    """
    base_title = normalize_title_style(str(base_title or "").strip() or build_safe_title("ES"), "ES")
    user_message = str(user_message or "").strip()
    min_len = int(st.session_state.get("min_title", 150))
    max_len = int(st.session_state.get("max_title", 200))
    must = st.session_state.get("title_must_keywords", []) or []
    banned = st.session_state.get("title_banned_keywords", []) or []
    history = st.session_state.get("title_chat_history", [])[-6:]
    prompt = f"""
Actúa como un editor senior de títulos Amazon.es para iluminación. Este es un TALLER DE TÍTULO, no generación de listing completo.

Objetivo: mejorar el título actual con el menor cambio necesario para hacerlo más vendible, natural y SEO, como si el usuario te diera instrucciones en un chat.

Título actual seleccionado:
{base_title}

Instrucción del usuario para esta ronda:
{user_message or '(sin instrucción específica; mejora de forma natural sin cambiar hechos)'}

Contexto compacto permitido para título:
{title_context_for_prompt('ES')}

Keywords que deben respetarse si encajan naturalmente:
{json.dumps(must, ensure_ascii=False)}

Keywords/frases prohibidas:
{json.dumps(banned, ensure_ascii=False)}

Historial breve de iteración:
{json.dumps(history, ensure_ascii=False, indent=2)}

Reglas duras:
- Devuelve JSON válido con exactamente {n} títulos candidatos.
- Todos empiezan por Alpinaluz.
- Longitud objetivo {min_len}-{max_len} caracteres; no rellenes con frases vacías.
- No SKU/modelo. No serie salvo que esté activado. Serie: {get_series_name() or '(vacía)'}; política: {'INCLUIR' if title_should_include_series() else 'NO incluir'}.
- No inventar hechos ni cambiar E27/G9/GU10/LED integrado, colores, materiales o dimensiones confirmadas.
- No usar: ideal para, perfecto para, bonito, precioso, bombilla no incluida, sin bombilla, no incluye bombilla.
- Evitar “compatible” en título; usa “Casquillo E27/G9/GU10” o “LED integrado” cuando aplique.
- No meter detalles de baja intención comercial: cable 2,4 m, incluye accesorios, instalación sencilla, base, distancia a pared, medidas secundarias. Esos van en bullets.
- IMPORTANTE: no bloquear palabras sueltas. "interruptor" puede ser valioso si es táctil, integrado, sensor, regulable o atributo visible; solo evita frases poco comerciales cuando no sean el argumento principal.
- Mantén estructura natural de Amazon España: marca + producto + material/forma/color + tamaño principal si ayuda + estilo + casquillo/LED + espacios principales.
- Si el título base ya es bueno, no lo destruyas; haz una versión refinada y dos alternativas cercanas.

Devuelve solo JSON:
{{"candidates": ["...", "...", "..."]}}
"""
    raw = llm(prompt, system="Especialista senior en títulos Amazon.es. Trabaja como chat de refinamiento de título. Output JSON only.", temperature=0.22, reasoning_effort_override="medium")
    data = safe_json(raw, {"candidates": []})
    candidates = data.get("candidates", []) if isinstance(data, dict) else []
    out = []
    for c in candidates[:6]:
        c = normalize_title_style(remove_water_phrases(str(c)), "ES")
        c = ensure_title(c, "ES", title_context_for_prompt("ES"))
        c = normalize_title_style(c, "ES")
        if c and c not in out and title_is_valid(c, "ES"):
            out.append(c)
    if not out:
        fb = user_message or "Mejorar el título de forma natural sin añadir detalles técnicos de bajo valor."
        out.append(refine_es_title_with_feedback(base_title, fb))
    while len(out) < n:
        alt = build_safe_title("ES")
        if alt not in out:
            out.append(alt)
        else:
            break
    # Store chat turn for future context, but keep short to avoid token growth.
    st.session_state.setdefault("title_chat_history", []).append({"from": base_title, "instruction": user_message, "result": out[:n]})
    st.session_state["title_chat_history"] = st.session_state["title_chat_history"][-8:]
    return out[:n]

def pro_audit_final_es_title(base_title: str) -> str:
    """V15.8: GPT-5.5 final title polish with rollback.
    Uses the normal model, not Pro, to avoid high cost and long waits.
    """
    base_title = normalize_title_style(base_title, "ES")
    must = st.session_state.get("title_must_keywords", []) or []
    banned = st.session_state.get("title_banned_keywords", []) or []
    min_len = int(st.session_state.get("min_title", 160))
    max_len = int(st.session_state.get("max_title", 200))
    prompt = f"""
Eres el revisor final de títulos Amazon.es para iluminación. Tu trabajo NO es inventar un título nuevo desde cero: mejora el título actual solo si aporta conversión, claridad y SEO real.

Título actual casi aprobado:
{base_title}

Hechos confirmados:
{facts_for_prompt('ES')}

Keywords que el usuario marcó como importantes:
{json.dumps(must, ensure_ascii=False)}

Keywords/frases prohibidas:
{json.dumps(banned, ensure_ascii=False)}

Reglas duras:
- Devuelve SOLO un título final, una línea, sin explicación.
- Debe empezar por Alpinaluz.
- Longitud objetivo {min_len}-{max_len} caracteres; si no cabe, prioriza precisión y naturalidad.
- No SKU/modelo. No serie salvo que esté activado. Serie actual: {get_series_name() or '(vacía)'}; política: {'INCLUIR' if title_should_include_series() else 'NO incluir'}.
- No añadir hechos ausentes. No cambiar E27/G9/GU10/LED integrado. No cambiar colores, materiales ni dimensiones confirmadas.
- Título para venta, no ficha técnica: incluye como máximo una dimensión principal visible si ayuda (por ejemplo Ø18 cm u Ø45 cm). No meter distancia a pared, base, cable, altura total, 65 cm u otras medidas secundarias; esas van en bullets.
- Si el interruptor es un valor comercial real (táctil, integrado, sensor, USB, regulable), puede aparecer; no lo elimines solo por contener la palabra interruptor.
- Prohibido en título: ideal para, perfecto para, compatible, bombilla no incluida, sin bombilla, no incluye bombilla.
- Para productos con casquillo, puedes escribir Casquillo E27/G9/GU10 o E27 G45 si aporta valor, pero no “compatible con”.
- Mantén estructura natural de Amazon: marca + producto + material/forma + tamaño principal + acabado/color relevante + estilo + casquillo + espacios principales.
- Debe sonar más bonito y comercial que técnico.
"""
    try:
        raw = llm(prompt, system="Revisor final senior de títulos Amazon.es para lámparas. Devuelve una sola línea.", temperature=0.08, model_override=st.session_state.get("final_title_model", "gpt-5.5"), reasoning_effort_override="medium")
        cand = raw.strip().splitlines()[0]
    except Exception:
        return base_title
    cand = normalize_title_style(cand, "ES")
    cand = commercial_title_clean(cand)
    cand = ensure_title(cand, "ES", facts_for_prompt("ES"))
    cand = normalize_title_style(cand, "ES")
    # Guardrail: if the polish returns something invalid or much worse, keep previous title.
    if not title_is_valid(cand, "ES") or len(cand) < 120 or contains_banned_keyword(cand, banned):
        return base_title
    old_score = score_title_es(base_title).get("score", 0)
    new_score = score_title_es(cand).get("score", 0)
    if new_score + 10 < old_score:
        return base_title
    return cand

def build_core_prompt(lang: str, es_master: str = "", locked_title: str = "") -> str:
    market = LANGS[lang]["market"]
    min_title = int(st.session_state.get("min_title", 140))
    max_title = int(st.session_state.get("max_title", 200))
    min_bullet = int(st.session_state.get("min_bullet", 150))
    max_bullet = int(st.session_state.get("max_bullet", 260))
    min_desc = int(st.session_state.get("min_description", 700))
    max_st = int(st.session_state.get("max_search_terms", 250))
    bulb_rule = product_type_hint_es() if lang == "ES" else "Respect bulb-included facts. Never say bulbs are included unless explicitly confirmed."
    title_rule = f"Use this exact title: {locked_title}" if locked_title else f"Generate a natural complete title between {min_title}-{max_title} characters."
    es_extra = "Generate the Spanish master version first."
    if lang != "ES":
        es_title_only = source_es_title(es_master)
        es_extra = f"""Use the ES master below as the only source of product strategy.
IMPORTANT FOR TITLE: the target-language TITLE must be a native localized version of this exact Spanish title, with the same facts and no extra specs:
{es_title_only}
Do not create the title from the fact card if it conflicts with the ES title. Bullets, description and A+ should follow the ES master closely but sound native for {market}. Do NOT mix Spanish words into the target language.

ES MASTER:
{es_master}"""
    return f"""
Write native Amazon listing copy for {market} in {LANGS[lang]['name']}.

{original_copy_policy_prompt() if lang == "ES" else "For target languages, preserve the ES master strategy and concrete facts. Do not simplify the title/bullets into poorer copy."}

Hard rules:
- {title_rule}
- Do NOT include SKU/model code in title, bullets, description, search terms, or A+.
- Title must be natural and complete. Never cut a sentence.
- Title should be readable, commercial and natural, not a raw keyword chain or technical fiche. Include at most one primary visible size in the title; move secondary dimensions such as wall distance, base size, cable length or installation measurements to bullets/description.
- TITLE MUST NOT include low-value phrases: compatible, bulb not included, bombilla no incluida, sin bombilla, ideal para, perfecto para. Use socket name like Casquillo E27 / E27 G45 in title; put bulb exclusion only in bullets or description.
- Do not output Chinese characters or placeholder brackets like [壁灯] in any target-language field.
- If language is not Spanish, do not leave Spanish phrases such as Aplique de Pared, Foco Orientable, Dormitorio, Salón, Bandeja, Puertos. Translate product type, room, material and colour fully into the target language.
- For integrated LED products, say LED integrated / built-in LED naturally in the target language and do NOT mention replaceable bulbs unless confirmed.
- 5 bullets, each ideally between {min_bullet} and {max_bullet} characters. If original bullets are strong, preserve every concrete point and expand it; do not summarize.
- Every bullet should follow the most natural Amazon high-conversion format for the target marketplace: a clear benefit/feature opening followed by concrete detail. A colon is allowed and recommended, but the label must sound human and can be 3-8 words, not a forced two-word label. Avoid awkward labels such as “Montaje Ordenado” or literal machine labels.
- Description should be at least {min_desc} characters, naturally structured and professional, without invented facts.
- Search terms must stay within {max_st} characters total.
- Do not use filler title phrases such as ideal para/perfecto para.
- Respect variant scope and do NOT place variant terms outside allowed sections.
- Platform safety: {bulb_rule}
- Never write “incluyendo LED, Edison o tradicionales”. Use only safe LED compatibility wording if needed.
- If adjustment level is weak, do not exaggerate with strong light-direction claims.
- A+ must follow this exact strategy:
  Module 1 = scene image copy for bedroom/living room/hotel use.
  Module 2 = feature detail 1.
  Module 3 = feature detail 2.
  Module 4 = feature detail 3.
  Module 5 = second scene image copy for another use environment.
- A+ output must use Chinese labels but target-language content.
- The field after “中文配图提示” MUST ALWAYS be Simplified Chinese, regardless of target language.
模块1 标题：...
模块1 正文：...
模块1 中文配图提示：中文配图提示...
...
模块5 标题：...
模块5 正文：...
模块5 中文配图提示：...
- Title capitalization: EN uses Amazon Title Case; ES uses Spanish Title Case; DE uses natural German capitalization; FR/IT/PT/NL/PL/SE use native marketplace style and must not look like Spanish.
- Search terms should be native, clean, and must not include random foreign color synonyms.
- Return JSON only.
- To save time and avoid extra API calls, also return Simplified Chinese explanations in the same JSON. Chinese explanation fields must explain ONLY the target-language text; do not add facts that are absent from the target-language field.

{es_extra}

FACTS:
{facts_for_prompt(lang)}

JSON format:
{{
  "title": "...",
  "title_cn": "中文解释标题，不添加原文没有的事实",
  "bullets": ["...","...","...","...","..."],
  "bullets_cn": ["中文解释五点1","中文解释五点2","中文解释五点3","中文解释五点4","中文解释五点5"],
  "description": "...",
  "description_cn": "中文解释长描述",
  "search_terms": "...",
  "search_terms_cn": "中文说明这组搜索词覆盖的搜索意图",
  "aplus": "模块1 标题：...\n模块1 正文：...\n模块1 中文配图提示：...\n..."
}}
"""


BULLET_LABELS = {
    "ES": ["Diseño Artesanal", "Material Natural", "Compatibilidad E27", "Medidas y Montaje", "Instalación Sencilla"],
    "EN": ["Handcrafted Design", "Natural Materials", "E27 Compatibility", "Size and Mounting", "Easy Installation"],
    "FR": ["Design artisanal", "Matériaux naturels", "Compatibilité E27", "Dimensions et montage", "Installation simple"],
    "DE": ["Handwerkliches Design", "Natürliche Materialien", "E27-Kompatibilität", "Maße und Montage", "Einfache Installation"],
    "IT": ["Design artigianale", "Materiali naturali", "Compatibilità E27", "Dimensioni e montaggio", "Installazione semplice"],
    "NL": ["Ambachtelijk design", "Natuurlijke materialen", "E27-compatibiliteit", "Afmetingen en montage", "Eenvoudige installatie"],
    "PL": ["Ręczne wykonanie", "Naturalne materiały", "Kompatybilność E27", "Wymiary i montaż", "Łatwa instalacja"],
    "PT": ["Design artesanal", "Materiais naturais", "Compatibilidade E27", "Dimensões e montagem", "Instalação simples"],
    "SE": ["Handgjord design", "Naturliga material", "E27-kompatibilitet", "Mått och montering", "Enkel installation"],
}


def enforce_bullet_label_format(bullets: List[str], lang: str) -> List[str]:
    labels = BULLET_LABELS.get(lang, BULLET_LABELS["EN"])
    out = []
    for i, b in enumerate(bullets[:5]):
        txt = re.sub(r"\s+", " ", str(b or "").strip())
        if not txt:
            out.append(txt)
            continue
        if re.match(r"^[^:]{2,42}:", txt):
            out.append(txt)
            continue
        label = labels[i] if i < len(labels) else labels[-1]
        body = txt[0].lower() + txt[1:] if len(txt) > 1 and lang in {"ES", "FR", "IT", "PT", "EN"} else txt
        out.append(f"{label}: {body}")
    while len(out) < 5:
        out.append("")
    return out[:5]



BAD_BULLET_LABEL_REPLACEMENTS = {
    "ES": {
        "Montaje Ordenado": "Instalación de Pared Limpia",
        "Montaje Limpio": "Instalación de Pared Limpia",
        "Orden y Montaje": "Instalación de Pared Limpia",
        "Instalación Ordenada": "Instalación de Pared Limpia",
        "Vidrio Trabajado": "Globo de Vidrio Multicolor",
        "Cristal Trabajado": "Globo de Cristal Decorativo",
        "Base Dorada": "Base Metálica Dorada",
        "Luz Envolvente": "Luz Ambiental Difusa",
        "Compatibilidad": "Casquillo y Bombilla Recomendada",
    },
    "EN": {"Tidy Mounting": "Clean Wall Installation", "Orderly Mounting": "Clean Wall Installation", "Crafted Glass": "Multicolour Glass Globe", "Gold-Tone Base": "Gold-Tone Metal Base"},
}

def normalize_bullet_label_text(bullet: str, lang: str) -> str:
    txt = str(bullet or "").strip()
    if ":" not in txt:
        return txt
    label, body = txt.split(":", 1)
    label_clean = label.strip()
    repl = BAD_BULLET_LABEL_REPLACEMENTS.get(lang, {}).get(label_clean)
    if repl:
        return f"{repl}: {body.strip()}"
    # Generic Spanish cleanup: labels should be a clear benefit, not a vague operational noun.
    if lang == "ES" and label_clean.lower() in {"montaje ordenado", "ordenado", "montaje"}:
        return f"Instalación de Pared Limpia: {body.strip()}"
    return txt

def sanitize_core(lang: str, core: Dict[str, Any], locked_title: str = "") -> Dict[str, Any]:
    title = locked_title or str(core.get("title", "")).strip().replace("\n", " ")
    title = ensure_title(title, lang, facts_for_prompt(lang))

    bullets = [remove_safety_bad_phrases(str(x).strip().replace("\n", " ")) for x in core.get("bullets", [])][:5]
    while len(bullets) < 5:
        bullets.append("")
    bullets = [clean_variants(b, lang, "BULLETS") for b in bullets]
    bullets = enforce_bullet_label_format(bullets, lang)
    bullets = [normalize_bullet_label_text(b, lang) for b in bullets]

    description = remove_safety_bad_phrases(str(core.get("description", "")).strip())
    description = clean_variants(description, lang, "DESCRIPTION")
    description = remove_model_codes(description).strip(" ,-–")

    search_terms = clean_variants(str(core.get("search_terms", "")).strip(), lang, "SEARCH TERMS")
    search_terms = trim_search_terms(search_terms)
    if st.session_state.get("variant_scope") not in {"标题+Search terms", "全文"}:
        search_terms = clean_variants(search_terms, lang, "FORCE_REMOVE")
        search_terms = trim_search_terms(search_terms)

    aplus = remove_safety_bad_phrases(str(core.get("aplus", "")).strip())
    aplus = clean_variants(aplus, lang, "A+")
    aplus = normalize_aplus_text(aplus)

    bullets_cn = core.get("bullets_cn", []) if isinstance(core.get("bullets_cn", []), list) else []
    while len(bullets_cn) < 5:
        bullets_cn.append("")
    return {
        "title": title,
        "title_cn": str(core.get("title_cn", "")).strip(),
        "bullets": bullets,
        "bullets_cn": [str(x).strip() for x in bullets_cn[:5]],
        "description": description,
        "description_cn": str(core.get("description_cn", "")).strip(),
        "search_terms": search_terms,
        "search_terms_cn": str(core.get("search_terms_cn", "")).strip(),
        "aplus": aplus,
    }


def core_has_language_errors(lang: str, core: Dict[str, Any]) -> List[str]:
    errs = []
    title = str(core.get("title", ""))
    fields = [title, str(core.get("description", "")), str(core.get("search_terms", ""))] + [str(x) for x in core.get("bullets", [])]
    if any(has_cjk(x) for x in fields):
        errs.append("目标语言字段含中文字符")
    joined = "\n".join(fields)
    for pat in language_forbidden_patterns(lang):
        if re.search(pat, joined, flags=re.I):
            errs.append("目标语言字段含占位符或错误语言残留")
            break
    if not title_is_valid(title, lang):
        errs.append("标题未通过语言/长度/完整性校验")
    return errs


def generate_core(lang: str, es_master: str = "", locked_title: str = "") -> Dict[str, Any]:
    base_prompt = build_core_prompt(lang, es_master, locked_title)
    last_errs = []
    # V14.5: 多语言默认快速生成。标题单独从 ES 标题对齐，正文只重试一次，速度比旧版明显快。
    max_attempts = 3 if lang == "ES" else (1 if st.session_state.get("fast_multilang", True) else 2)
    es_title = source_es_title(es_master) if lang != "ES" else ""
    aligned_title = foreign_title_from_keyword_strategy(lang, es_title) if (lang != "ES" and es_title) else ""

    for attempt in range(max_attempts):
        prompt = base_prompt
        if attempt > 0:
            prompt += "\n\nCRITICAL RETRY: Previous output failed validation: " + "; ".join(last_errs) + "\nRewrite all fields natively in the target language, remove placeholders/Chinese/Spanish leftovers, and keep title valid."
        raw = llm(prompt, system="You write native Amazon listing JSON for lighting products. Output valid JSON only.", temperature=0.26 if lang != "ES" else (0.32 if attempt else 0.38))
        core = safe_json(raw, {"title": "", "bullets": ["", "", "", "", ""], "description": "", "search_terms": "", "aplus": ""})
        if lang != "ES" and aligned_title:
            core["title"] = aligned_title
        core = sanitize_core(lang, core, locked_title=locked_title if lang == "ES" else "")
        if lang != "ES" and es_title and (title_has_extra_specs_vs_es(core.get("title", ""), es_title) or has_cjk(core.get("title", ""))):
            core["title"] = foreign_title_from_keyword_strategy(lang, es_title)
        last_errs = core_has_language_errors(lang, core)
        # 如果只有标题问题且有 ES 对齐标题，直接用对齐标题通过，不重试整篇，提升速度。
        if lang != "ES" and aligned_title:
            last_errs = [e for e in last_errs if "标题" not in e]
        if not last_errs:
            return core

    core["title"] = aligned_title or build_safe_title(lang)
    core["title"] = ensure_title(core["title"], lang, facts_for_prompt(lang))
    core["aplus"] = normalize_aplus_text(core.get("aplus", ""))
    return core


def generate_explain(lang: str, title: str, bullets: List[str], description: str, search_terms: str) -> Dict[str, Any]:
    prompt = f"""
请严格根据以下 {lang} 原文生成中文释义。
规则：
- 只能解释原文里已有的信息，不能补充原文没有的颜色、SKU、数量、参数。
- 标题释义只解释标题。
- 五点释义必须一一对应原文五点。
- 长描述释义只概括原文长描述。
- Search terms 中文解释要说明这组词覆盖的搜索意图，不要留空。
- 输出 JSON。

TITLE:
{title}

BULLETS:
{json.dumps(bullets, ensure_ascii=False)}

DESCRIPTION:
{description}

SEARCH TERMS:
{search_terms}

JSON format:
{{"title_cn":"...","bullets_cn":["...","...","...","...","..."],"description_cn":"...","search_terms_cn":"..."}}
"""
    raw = llm(prompt, system="You produce strict JSON only.", temperature=0.15)
    return safe_json(raw, {"title_cn": "", "bullets_cn": ["", "", "", "", ""], "description_cn": "", "search_terms_cn": ""})


def explain_from_core_or_generate(lang: str, core: Dict[str, Any]) -> Dict[str, Any]:
    """V16: prefer Chinese explanations returned in the same JSON as listing copy.
    This avoids a second API call per language. If the model missed a field, fall back to a compact extra call.
    """
    ex = {
        "title_cn": str(core.get("title_cn", "")).strip(),
        "bullets_cn": core.get("bullets_cn", []) if isinstance(core.get("bullets_cn", []), list) else [],
        "description_cn": str(core.get("description_cn", "")).strip(),
        "search_terms_cn": str(core.get("search_terms_cn", "")).strip(),
    }
    # Always use deterministic title Chinese explanation to stay synchronized with the final localized title.
    if lang != "ES":
        ex["title_cn"] = title_cn_from_skeleton(lang, core.get("title", ""))
    while len(ex["bullets_cn"]) < 5:
        ex["bullets_cn"].append("")
    ex["bullets_cn"] = [str(x).strip() for x in ex["bullets_cn"][:5]]
    if ex["title_cn"] and ex["description_cn"] and ex["search_terms_cn"] and all(ex["bullets_cn"]):
        return ex
    # Missing explanations are rare in V16 batch mode; only then use the old generator.
    return generate_explain(lang, core.get("title", ""), core.get("bullets", []), core.get("description", ""), core.get("search_terms", ""))


def build_batch_multilang_prompt(langs: List[str], es_master: str, es_title: str) -> str:
    """One prompt for several marketplaces. Reduces repeated input tokens and API overhead."""
    max_title = int(st.session_state.get("max_title", 200))
    min_bullet = int(st.session_state.get("min_bullet", 180))
    max_bullet = int(st.session_state.get("max_bullet", 260))
    min_desc = int(st.session_state.get("min_description", 700))
    max_st = int(st.session_state.get("max_search_terms", 250))
    lang_info = {l: LANGS[l] for l in langs}
    local_titles = {l: foreign_title_from_keyword_strategy(l, es_title) for l in langs}
    return f"""
You are generating localized Amazon listing packages for Alpinaluz lighting products.

Target languages/marketplaces:
{json.dumps(lang_info, ensure_ascii=False, indent=2)}

FINAL locked Amazon.es title. Treat this as the product-title truth:
{es_title}

FULL ES MASTER. Preserve facts and selling strategy, but write native local copy:
{es_master}

Exact localized titles to use. Do NOT rewrite these titles; copy each title exactly into the corresponding TITLE field:
{json.dumps(local_titles, ensure_ascii=False, indent=2)}

Confirmed product facts, for fact checking only. If a fact conflicts with the final ES title or exact localized title, follow the final ES title/localized title:
{facts_for_prompt('ES')}

Hard rules for every target language:
- Output valid JSON only, object keyed by language code: {json.dumps(langs, ensure_ascii=False)}.
- Each title MUST start with Alpinaluz.
- Title must be native for the target marketplace and should not look like word-for-word Spanish.
- TITLE field must exactly match the provided localized title for that language. Do not rewrite, shorten or expand it.
- No Chinese inside target-language title/bullets/description/search terms. Chinese only in *_cn fields and A+ image tips.
- No Spanish leftovers in non-Spanish languages except universal codes such as E27, G45, LED, IP20, USB-C.
- Use local capitalization: EN title case; DE natural German noun capitalization; FR/IT/PT/NL/PL/SE native marketplace style, not Spanish Title Case.
- Title max {max_title} characters. Prefer natural, beautiful, sales-oriented titles over technical-fiche titles. Do not include low-value phrases: ideal/perfect/compatible/bulb not included in the title.
- Bullets: exactly 5. Use native Amazon high-conversion bullet style. The prefix before the colon should be a natural selling point phrase, usually 3-9 words, not a forced two-word label. Do not invent vague labels such as “Orderly Mounting / Montaje Ordenado”. Preserve concrete facts from ES.
- Description: at least {min_desc} characters when natural. Professional, no invented facts.
- Search terms: native search terms only, max {max_st} characters.
- A+ modules: exactly 5 modules. Module 1 and 5 are scene/use image copy. Modules 2/3/4 are three most important feature details. Use the format with Chinese labels:
  模块1 标题：target language title
  模块1 正文：target language body
  模块1 中文配图提示：Simplified Chinese image prompt
  ... through 模块5.
- Also include Simplified Chinese explanations in the same JSON fields. These explanations must only explain the generated target-language text; do not add extra facts.

For each language code, return this schema:
{{
  "TITLE": "...",
  "title_cn": "...",
  "BULLETS": ["...", "...", "...", "...", "..."],
  "bullets_cn": ["...", "...", "...", "...", "..."],
  "DESCRIPTION": "...",
  "description_cn": "...",
  "SEARCH_TERMS": "...",
  "search_terms_cn": "...",
  "APLUS": "模块1 标题：...\\n模块1 正文：...\\n模块1 中文配图提示：...\\n\\n模块2 标题：..."
}}
"""


def generate_multilang_batch(langs: List[str], es_master: str, es_title: str) -> Dict[str, str]:
    """V16 fast path: generate several countries per API call and include Chinese explanations in one response."""
    result: Dict[str, str] = {}
    if not langs:
        return result
    batch_size = int(st.session_state.get("multilang_batch_size", 4) or 4)
    batch_size = max(2, min(8, batch_size))
    batches = [langs[i:i+batch_size] for i in range(0, len(langs), batch_size)]
    progress = st.progress(0, text="准备批量生成多语言...")
    for bi, group in enumerate(batches, start=1):
        progress.progress((bi-1)/len(batches), text=f"正在生成第 {bi}/{len(batches)} 组：{', '.join(group)}")
        prompt = build_batch_multilang_prompt(group, es_master, es_title)
        raw = llm(prompt, system="Native Amazon marketplace localization engine. Output strict JSON only.", temperature=0.18, reasoning_effort_override="medium")
        data = safe_json(raw, {})
        if not isinstance(data, dict):
            data = {}
        for lang in group:
            item = data.get(lang) or data.get(lang.lower()) or data.get(LANGS[lang]["name"]) or {}
            if not isinstance(item, dict):
                item = {}
            core = {
                "title": item.get("TITLE") or item.get("title") or "",
                "title_cn": item.get("title_cn") or item.get("标题中文解释") or "",
                "bullets": item.get("BULLETS") or item.get("bullets") or [],
                "bullets_cn": item.get("bullets_cn") or item.get("五点中文解释") or [],
                "description": item.get("DESCRIPTION") or item.get("description") or "",
                "description_cn": item.get("description_cn") or item.get("长描述中文解释") or "",
                "search_terms": item.get("SEARCH_TERMS") or item.get("search_terms") or "",
                "search_terms_cn": item.get("search_terms_cn") or item.get("Search Terms中文解释") or "",
                "aplus": item.get("APLUS") or item.get("aplus") or "",
            }
            # V16.6: title is generated from the ES semantic skeleton, not free-generated by the batch model.
            # This keeps brand first, local capitalization stable, and prevents broken fragments.
            if es_title:
                core["title"] = foreign_title_from_keyword_strategy(lang, es_title)
            core = sanitize_core(lang, core)
            if es_title:
                core["title"] = foreign_title_from_keyword_strategy(lang, es_title)
            explain = explain_from_core_or_generate(lang, core)
            result[lang] = compose_listing(lang, core, explain)
    progress.progress(1.0, text="多语言生成完成")
    return result


def sanitize_bullets_natural(lang: str, bullets: List[str]) -> List[str]:
    """Post-process obvious machine-style bullet prefixes without changing facts.
    Keeps Amazon bullet style natural and prevents labels like “Montaje Ordenado” or double prefixes.
    """
    out = []
    replacements = {
        "ES": [(r"^Montaje Ordenado\s*:", "Instalación de Pared Limpia:"), (r"^Vidrio Trabajado\s*:", "Globo de Vidrio Decorativo:")],
        "EN": [(r"^Orderly Mounting\s*:", "Clean Wall Installation:"), (r"^Crafted Glass\s*:", "Decorative Glass Globe:")],
        "FR": [(r"^Montage Ordonné\s*:", "Installation murale soignée:"), (r"^Verre travaillé\s*:", "Globe en verre décoratif:")],
        "DE": [(r"^Natürliche Materialien:\s*Verarbeitetes Glas, jedes Stück einzigartig\s*:", "Verarbeitetes Glas mit individuellem Charakter:"), (r"^Verarbeitetes Glas, jedes Stück einzigartig\s*:", "Verarbeitetes Glas mit individuellem Charakter:")],
        "IT": [(r"^Montaggio ordinato\s*:", "Installazione a parete pulita:"), (r"^Vetro lavorato\s*:", "Globo in vetro decorativo:")],
        "PT": [(r"^Montagem ordenada\s*:", "Instalação de parede limpa:"), (r"^Vidro trabalhado\s*:", "Globo de vidro decorativo:")],
        "NL": [(r"^Ordelijk gemonteerd\s*:", "Nette wandmontage:"), (r"^Bewerkt glas\s*:", "Decoratieve glazen bol:")],
        "PL": [(r"^Uporządkowany montaż\s*:", "Estetyczny montaż ścienny:"), (r"^Obrabiane szkło\s*:", "Dekoracyjna szklana kula:")],
        "SE": [(r"^Ordnad montering\s*:", "Ren väggmontering:"), (r"^Bearbetat glas\s*:", "Dekorativt glasklot:")],
    }.get(lang, [])
    for b in (bullets or [])[:5]:
        b = str(b or "").strip()
        for pat, rep in replacements:
            b = re.sub(pat, rep, b, flags=re.I)
        # Avoid repeated prefix pattern like "X: Y:" at the start.
        b = re.sub(r"^([^:.]{3,45}:\s*)([^:.]{3,55}:\s*)", r"\2", b)
        out.append(b)
    while len(out) < 5:
        out.append("")
    return out[:5]


def compose_listing(lang: str, core: Dict[str, Any], explain: Dict[str, Any]) -> str:
    out = [f"[{lang}]", "", "[TITLE]", core["title"], "", "[标题中文解释]", str(explain.get("title_cn", "")).strip(), ""]
    core["bullets"] = sanitize_bullets_natural(lang, core.get("bullets", []))
    out += ["[BULLETS]"]
    for i, b in enumerate(core["bullets"], start=1):
        out.append(f"{i}. {b}")
    out += ["", "[五点中文解释]"]
    bcn = explain.get("bullets_cn", []) or []
    for i in range(5):
        out.append(f"{i+1}. {bcn[i] if i < len(bcn) else ''}")
    out += ["", "[DESCRIPTION]", core["description"], "", "[长描述中文解释]", str(explain.get("description_cn", "")).strip(), "", "[SEARCH TERMS]", core["search_terms"], "", "[Search Terms中文解释]", str(explain.get("search_terms_cn", "")).strip(), "", "[A+]", normalize_aplus_text(core["aplus"])]
    return "\n".join(out).strip() + "\n"


def export_zip() -> bytes:
    buf = io.BytesIO()
    sku = st.session_state.get("sku", "SKU") or "SKU"
    name = f"{sku}_{date.today().isoformat()}_AMAZON-LISTING.zip"
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # V16.5 default: only export files that new staff actually upload/use.
        if st.session_state.get("es_text"):
            zf.writestr("listing/ES_Listing.txt", st.session_state["es_text"])
        for lang, text in st.session_state.get("localized_texts", {}).items():
            zf.writestr(f"listing/{lang}_Listing.txt", text)
        if st.session_state.get("export_quality_files"):
            zf.writestr("tech_specs/field_cards.txt", "\n".join(field_card_lines()))
            tech_lines = [
                f"SKU: {st.session_state.get('sku','')}",
                f"EAN: {st.session_state.get('ean','')}",
                f"品牌: {st.session_state.get('brand','Alpinaluz')}",
                "",
                "【产品事实卡】",
                *field_card_lines(),
            ]
            zf.writestr("tech_specs/manual_required_fields.txt", "\n".join(tech_lines))
            if st.session_state.get("title_candidates"):
                details_text = format_title_candidate_details(st.session_state.get("title_candidate_details") or generate_title_candidate_details(st.session_state.get("title_candidates", [])))
                zf.writestr("quality/title_candidates_es.txt", details_text)
            if st.session_state.get("fact_suggestions"):
                zf.writestr("quality/ai_fact_suggestions.json", json.dumps(st.session_state.get("fact_suggestions"), ensure_ascii=False, indent=2))
    buf.seek(0)
    st.session_state["zip_name"] = name
    return buf.read()


# ------------------------ UI ------------------------
init_state()
apply_pending_facts()

with st.sidebar:
    st.header("API 与模式")
    st.text_input("OpenAI API Key", type="password", key="openai_api_key")
    st.selectbox("主力模型", ["gpt-5.4", "gpt-5.5", "gpt-5.4-mini", "gpt-4.1"], key="model", help="默认 GPT-5.4：日常生成更快、更省。重要链接可手动切 GPT-5.5。")
    st.selectbox("推理强度", ["medium", "high", "xhigh"], key="reasoning_effort", help="默认 medium：质量/速度平衡。重要产品可用 high；xhigh 会明显更慢。")
    st.selectbox("图片识别模式", ["快速：只用文字和图片文件名", "标准：分析前3张图（推荐）", "完整：分析前6张图（较慢）"], key="image_analysis_mode", help="图片越多越准但越慢。日常建议前3张：主图、尺寸图、关键细节图。")
    st.checkbox("AI生成标题中文解释/优缺点（更慢）", key="ai_title_explanations", value=st.session_state.get("ai_title_explanations", False), help="关闭时使用规则解释，能少一次API调用，标题候选会快很多。")
    st.radio("使用模式", ["新手模式", "专业模式"], key="mode", help="新手模式：先识别事实卡，再生成标题候选和ES母版。专业模式：保留更多可调项。")
    st.checkbox("快速多语言生成", key="fast_multilang", value=True, help="默认开启：V16会减少多语言重试，并尽量用同一次输出生成中文解释。")
    if st.session_state.get("foreign_title_mode") not in ["语义骨架本地化（推荐，快且稳）", "严格翻译ES标题（备用）"]:
        st.session_state["foreign_title_mode"] = "语义骨架本地化（推荐，快且稳）"
    st.selectbox("多语言标题方式", ["语义骨架本地化（推荐，快且稳）", "严格翻译ES标题（备用）"], key="foreign_title_mode", help="推荐：先解析最终ES标题的语义骨架，再按各国Amazon标题习惯本地化，减少翻车和token浪费。")
    st.selectbox("多语言生成方式", ["批量合并生成（推荐，快）", "逐国稳定生成（慢）"], key="multilang_generation_mode", help="批量合并：每次请求同时生成多个国家，减少重复输入和等待；逐国稳定：旧流程，慢但便于定位单个国家问题。")
    st.number_input("批量每组国家数", min_value=2, max_value=8, key="multilang_batch_size", help="默认8：一次生成全部国家。若某次格式不稳定，再改为4排查。")
    st.checkbox("只生成缺失国家", key="multilang_only_missing", help="已生成过的国家不重跑，方便只补新国家或出错国家。")
    with st.expander("高级导出设置", expanded=False):
        st.checkbox("导出 quality / tech_specs 调试文件", key="export_quality_files", help="默认关闭。新手只需要 listing 文件夹；打开后才会额外导出质量检查和字段卡。")
    st.checkbox("生成完成声音提示", key="sound_notify", value=st.session_state.get("sound_notify", True), help="长时间等待多语言生成时，完成后播放一声提示。部分浏览器可能需要允许声音。")
    st.divider()
    render_usage_dashboard()
    st.divider()
    st.markdown("### 长度控制")
    st.number_input("标题最小字符", min_value=80, max_value=220, key="min_title")
    st.number_input("标题最大字符", min_value=100, max_value=220, key="max_title")
    st.number_input("五点最小字符", min_value=80, max_value=260, key="min_bullet")
    st.number_input("五点最大字符", min_value=120, max_value=320, key="max_bullet")
    st.number_input("长描述最小字符", min_value=300, max_value=1200, key="min_description")
    st.number_input("Search terms 最大字符", min_value=80, max_value=250, key="max_search_terms")
    st.divider()
    if st.button("清空生成结果（保留输入）"):
        for k in ["es_core", "es_explain", "es_text", "localized_texts", "es_locked", "title_candidates", "selected_es_title"]:
            st.session_state.pop(k, None)
        st.success("已清空生成结果")
    if st.button("仅清空图片"):
        st.session_state["uploaded_images"] = []
        st.success("已清空图片")

st.title("Alpinaluz Listing Generator V16.9")
st.caption("GPT-5.4日常主力 · 标题聊天主流程 · 多语言标题骨架修复 · 只导出Listing · 可扩展Mirakl平台")

if st.session_state.get("mode") == "新手模式":
    st.info("新手流程：①上传资料 → ②AI识别产品事实卡 → ③确认事实 → ④生成3个ES标题候选 → ⑤选择标题生成ES母版 → ⑥锁定后生成各国版本。")

left, right = st.columns([1.2, 1])
with left:
    st.subheader("1）资料输入")
    st.text_input("SKU", key="sku")
    st.text_input("EAN", key="ean")
    st.text_input("品牌", key="brand", help="标题必须以 Alpinaluz 开头；除非你明确修改品牌。")
    st.text_input("产品系列名（可选，默认不进标题）", key="manual_series_name", help="例如 TOURS / SION / Mini Gala。默认只进入字段卡和内部识别，不占用Amazon标题SEO位置。")
    st.checkbox("标题中包含系列名", key="title_include_series", help="默认关闭。只有系列名本身有搜索价值或品牌识别价值时才打开。")
    st.text_area("网站原始内容 / 老链接内容", key="source_text", height=150, help="权重高。把网站标题、描述、参数粘贴进来，AI会优先从这里提取事实。")
    st.text_area("手动标题（可选）", key="manual_title", height=80, help="权重很高。默认策略会优先优化原始标题，而不是推翻重写。")
    st.text_area("技术备注", key="tech_notes", height=100, help="权重最高。写不能错的事实：E27、不含灯泡、IP44、直径、材质、不可精确调角度等。")
    st.text_area("SEO关键词", key="keywords", height=80, help="权重中等。用于补充标题和Search terms，不会覆盖产品事实。")
    st.text_area("手动长描述（可选）", key="manual_description", height=90, help="权重中等。用于补充场景和卖点，不会逐字复制。")
    st.selectbox("原文处理方式", ["优质原文保留增强（推荐）", "原文一般，AI重写优化", "资料很少，AI从零生成"], key="source_quality_mode", help="如果原始标题/五点/描述已经不错，必须选保留增强，AI只做SEO增强和格式规范，不允许删减核心信息。")
    files = st.file_uploader("上传图片（可多张）", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, help="用于识别颜色、材质、结构、风格。不要上传带灯泡详情的图片，容易误判为含灯泡。")
    if files is not None:
        st.session_state["uploaded_images"] = files
    if st.session_state.get("uploaded_images"):
        st.markdown("**图片用途检查**")
        for idx, f in enumerate(st.session_state["uploaded_images"]):
            img_name = getattr(f, "name", f"image_{idx}")
            st.checkbox(
                f"排除这张图用于事实识别：{idx + 1}. {img_name}",
                key=image_exclude_key(f, idx),
                value=image_is_excluded(f, idx),
                help="比如带灯泡详情、尺寸不对应、有Logo、不是当前SKU的图。即使多张图片同名，也不会再报错。",
            )
        st.checkbox("至少需要一张有光效/光斑的场景图", key="image_light_effect_required")

with right:
    st.subheader("2）产品事实卡")
    if st.button("AI识别/更新产品事实卡", type="primary"):
        try:
            with st.spinner("正在识别产品类型、颜色结构、灯头、风格、图片风险..."):
                facts = analyze_product_facts()
                st.session_state["fact_suggestions"] = facts
                st.session_state["pending_apply_facts"] = facts
            st.rerun()
        except Exception as e:
            st.error(str(e))

    if st.session_state.get("fact_suggestions"):
        with st.expander("查看上次AI识别建议", expanded=False):
            st.json(st.session_state["fact_suggestions"])

    col_a, col_b = st.columns(2)
    with col_a:
        st.session_state["data::产品类型"] = pick_value("产品类型", "data::产品类型", "产品类型会决定安装方式、标题模板和必填参数。")
        if st.button("按产品类型自动填默认安装/LED/灯泡规则"):
            apply_product_defaults(get_field("产品类型"))
            st.rerun()
        st.session_state["data::材质"] = pick_value("材质", "data::材质")
        st.session_state["data::颜色"] = pick_value("颜色", "data::颜色", "这是主变体颜色，不一定等于电线/灯罩/底座颜色。")
        st.session_state["data::灯头"] = pick_value("灯头", "data::灯头")
        st.session_state["data::风格"] = pick_value("风格", "data::风格", "风格要锁定。比如F008应为 Retro Cinema/Vintage，不要写现代极简。")
    with col_b:
        st.session_state["data::适用空间"] = pick_value("适用空间", "data::适用空间")
        st.session_state["data::安装方式"] = pick_value("安装方式", "data::安装方式")
        st.session_state["data::室内/室外"] = pick_value("室内/室外", "data::室内/室外")
        st.session_state["data::是否含灯泡"] = pick_value("是否含灯泡", "data::是否含灯泡", "普通灯具默认选“否”。文案会强制写 Bombilla no incluida。")
        st.session_state["data::是否LED"] = pick_value("是否LED", "data::是否LED")
        st.session_state["data::调节能力"] = pick_value("调节能力", "data::调节能力", "避免把轻微可调写成精准多角度调光。")

    with st.expander("颜色结构 / 尺寸 / 高风险事实（建议确认）", expanded=st.session_state.get("mode") == "新手模式"):
        for label in COLOR_PART_FIELDS:
            st.text_input(label, key=f"fact::{label}", help="复杂颜色不要只填一个主色。比如灯罩白色、底座金色、电线黑白编织。")
        colx, coly, colz = st.columns(3)
        with colx:
            st.text_input("尺寸", key="fact::尺寸")
            st.text_input("直径", key="fact::直径")
            st.text_input("高度", key="fact::高度")
        with coly:
            st.text_input("最大功率W", key="fact::最大功率W", help="如 E27 最大40W，就填40。")
            st.text_input("流明lm", key="fact::流明lm")
            st.text_input("色温K", key="fact::色温K")
        with colz:
            st.text_input("IP等级", key="fact::IP等级")
            st.text_input("AI识别系列名（可被上方产品系列名覆盖）", key="fact::系列名")
            st.text_input("禁用风格词", key="fact::禁用风格词", help="例如 moderno,minimalista。标题/文案会检查。")
        st.text_input("核心卖点1", key="fact::核心卖点1")
        st.text_input("核心卖点2", key="fact::核心卖点2")
        st.text_input("核心卖点3", key="fact::核心卖点3")
        st.text_area("特殊禁止写法", key="fact::特殊禁止写法", height=60, help="如：不能写 incluyendo LED, Edison o tradicionales；不能说精准调角度。")
        st.text_area("图片注意事项", key="fact::图片注意事项", height=60, help="如：顶盘用白色；去掉电线；小号D29用于厨房岛台双灯。")

    st.markdown("**字段对照卡预览**")
    lines = field_card_lines()
    st.text_area("字段对照", value="\n".join(lines), height=260)

if st.session_state.get("mode") == "专业模式":
    st.subheader("3）专业控制")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.radio("标题策略", ["优先优化原始标题", "全新生成标题"], key="title_strategy")
        st.selectbox("标题格式", ["自然亚马逊标题（推荐）", "结构化特性标题（技术款）", "SEO长标题", "简洁安全标题"], key="title_format_mode", help="自然标题最像常见Amazon高转化标题；结构化标题适合参数很多的技术款；SEO长标题信息更全；简洁安全标题更短更稳。")
    with c2:
        st.checkbox("启用变体中性模式", key="variant_neutral")
        st.selectbox("变体体现范围", ["仅标题", "标题+Search terms", "全文", "完全中性"], key="variant_scope")
    with c3:
        st.multiselect("变体字段", ["颜色", "尺寸", "功率", "色温", "套装数量", "左右款"], key="variant_fields")
        st.text_input("变体词/短语（多个用逗号隔开）", key="variant_terms")
else:
    with st.expander("变体/父体设置（新手简化版）", expanded=False):
        st.checkbox("这套A+是否要给多个变体共用？", key="variant_neutral", help="勾选后，A+会尽量不写颜色/尺寸/套装数量，方便父体共用。")
        st.selectbox("标题/Search terms 是否保留当前变体词", ["标题+Search terms", "仅标题", "完全中性", "全文"], key="variant_scope")
        st.multiselect("当前变体字段", ["颜色", "尺寸", "功率", "色温", "套装数量", "左右款"], key="variant_fields")
        st.text_input("变体词/短语（多个用逗号隔开）", key="variant_terms", help="例如 Negro, lote 2 blanco。")

st.subheader("4）ES 标题候选与母版生成")
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("生成3个ES标题候选", type="primary"):
        try:
            with st.spinner("正在生成并评分标题候选..."):
                st.session_state["title_candidates"] = generate_es_title_candidates()
                st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                st.session_state["title_round_history"] = [st.session_state["title_candidates"].copy()]
                st.session_state["selected_title_idx"] = 0
                if st.session_state.get("title_candidates"):
                    st.session_state["last_title_zh"] = cheap_title_zh(st.session_state["title_candidates"][0])
                    st.session_state["last_title_zh_source"] = st.session_state["title_candidates"][0]
                notify_done("ES标题候选已生成")
        except Exception as e:
            st.error(str(e))
with col2:
    if st.button("直接生成ES母版"):
        try:
            with st.spinner("正在生成ES母版..."):
                locked = st.session_state.get("selected_es_title", "")
                if not locked and not st.session_state.get("title_candidates"):
                    st.session_state["title_candidates"] = generate_es_title_candidates()
                    st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                    locked = st.session_state["title_candidates"][0]
                elif not locked:
                    locked = st.session_state["title_candidates"][st.session_state.get("selected_title_idx", 0)]
                st.session_state["selected_es_title"] = locked
                core = generate_core("ES", locked_title=locked)
                explain = explain_from_core_or_generate("ES", core)
                st.session_state["es_core"] = core
                st.session_state["es_explain"] = explain
                st.session_state["es_text"] = compose_listing("ES", core, explain)
                st.session_state["es_locked"] = False
                notify_done("ES母版已生成")
        except Exception as e:
            st.error(str(e))
with col3:
    if st.button("锁定ES母版"):
        if st.session_state.get("es_text"):
            final_title = st.session_state.get("selected_es_title") or source_es_title(st.session_state.get("es_text", ""))
            if final_title:
                final_title = normalize_title_style(clean_title_candidate(final_title), "ES")
                st.session_state["locked_es_title"] = final_title
                st.session_state["es_text"] = replace_listing_title(st.session_state.get("es_text", ""), final_title)
                if isinstance(st.session_state.get("es_core"), dict):
                    st.session_state["es_core"]["title"] = final_title
            st.session_state["es_locked"] = True
            st.success("ES 已锁定，并已同步当前选定标题")
        else:
            st.warning("请先生成 ES 母版")

if st.session_state.get("title_candidates"):
    st.markdown("### 标题候选评分与中文解释")
    if not st.session_state.get("title_candidate_details"):
        st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
    details = st.session_state.get("title_candidate_details", [])
    labels = []
    for i, t in enumerate(st.session_state["title_candidates"]):
        sc = score_title_es(t)
        usage = details[i].get("usage", "") if i < len(details) else ""
        labels.append(f"候选{i+1}｜{usage}｜{sc['score']}分｜{sc['len']}字符")

    idx = st.radio(
        "选择一个标题作为ES母版标题",
        list(range(len(labels))),
        format_func=lambda i: labels[i],
        horizontal=False,
        key="selected_title_idx",
    )
    selected = st.session_state["title_candidates"][idx]
    st.session_state["selected_es_title"] = selected
    d = details[idx] if idx < len(details) else {}
    edited_selected = st.text_area("选定标题（可直接手动微调）", value=selected, height=80, help="这里就是最终ES标题工作区。可以直接手动改；锁定ES母版时会使用这里的当前标题。")
    if edited_selected and edited_selected.strip() != selected:
        edited_selected = normalize_title_style(clean_title_candidate(edited_selected.strip()), "ES")
        st.session_state["title_candidates"][idx] = edited_selected
        st.session_state["selected_es_title"] = edited_selected
        selected = edited_selected
        st.session_state["last_title_zh"] = ""
        st.session_state["last_title_zh_source"] = ""

    zh_cols = st.columns([1.2, 3])
    with zh_cols[0]:
        if st.button("便宜翻译当前标题", use_container_width=True):
            try:
                with st.spinner("正在用轻量模型翻译标题..."):
                    _title_to_translate = st.session_state.get("selected_es_title", selected)
                    st.session_state["last_title_zh"] = cheap_title_zh(_title_to_translate)
                    st.session_state["last_title_zh_source"] = _title_to_translate
            except Exception as e:
                st.error(str(e))
    with zh_cols[1]:
        if st.session_state.get("last_title_zh_source") == selected and st.session_state.get("last_title_zh"):
            current_zh = st.session_state.get("last_title_zh")
        else:
            current_zh = d.get("cn", "") or "标题已变化，建议点击左侧按钮刷新中文释义。"
        st.text_area("当前标题中文释义（给新手判断用）", value=current_zh, height=72, disabled=True)

    st.markdown("#### V16.6 标题聊天工作台（主流程）")
    st.caption("像聊天窗口一样改标题：只读取精简事实 + 当前标题 + 你的修改要求，不再反复读取完整长描述/A+。中文释义会在标题生成后同步刷新，避免新手误判。")
    chat_cols = st.columns([3, 1, 1])
    with chat_cols[0]:
        st.text_area("标题聊天指令", key="title_chat_instruction", height=75, placeholder="例如：更像亚马逊西班牙站标题；突出复古电影风；不要写电线长度；保留触摸开关；标题更有成交感。")
    with chat_cols[1]:
        if st.button("聊天式生成3个标题", type="primary", use_container_width=True):
            try:
                with st.spinner("正在像聊天窗口一样精修标题...只使用精简标题上下文"):
                    prev = st.session_state.get("title_candidates", []).copy()
                    new_titles = chat_title_workspace_round(selected, st.session_state.get("title_chat_instruction", ""), n=3)
                    st.session_state.setdefault("title_round_history", []).append(prev)
                    # Put chat candidates first, keep one previous candidate as safety fallback.
                    merged = []
                    for t in new_titles + [selected] + prev:
                        if t and t not in merged:
                            merged.append(t)
                    st.session_state["title_candidates"] = merged[:4]
                    st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                    st.session_state["selected_es_title"] = st.session_state["title_candidates"][0]
                    st.session_state["last_title_zh"] = cheap_title_zh(st.session_state["selected_es_title"])
                    st.session_state["last_title_zh_source"] = st.session_state["selected_es_title"]
                    notify_done("聊天式标题已生成")
                st.rerun()
            except Exception as e:
                st.error(str(e))
    with chat_cols[2]:
        if st.button("回退聊天前标题", use_container_width=True):
            hist = st.session_state.get("title_round_history", [])
            if hist:
                st.session_state["title_candidates"] = hist.pop()
                st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                st.session_state["selected_es_title"] = st.session_state["title_candidates"][0] if st.session_state["title_candidates"] else ""
                st.rerun()
            else:
                st.info("暂无可回退版本。")
    with st.expander("标题聊天规则说明", expanded=False):
        st.markdown("""
- 标题聊天只使用精简上下文：原标题、事实卡核心字段、必须词/禁止词和当前标题。
- 不会把完整五点、长描述、A+重复喂给标题模型，减少token和负优化。
- 不粗暴禁止单词：例如 `interruptor táctil`、`interruptor integrado` 如果是核心卖点可以保留；只是避免 `cable 2,4 m`、`bombilla no incluida`、`instalación sencilla` 这类低价值说明占标题位置。
- 标题确认后再生成ES母版；多语言标题会基于最终锁定ES标题的语义骨架本地化。
""")

    with st.expander("这个标题的中文解释 / 优点 / 风险（默认折叠）", expanded=False):
        st.markdown(f"**中文解释：** {d.get('cn','')}")
        st.markdown(f"**优点：** {d.get('pros','')}")
        st.markdown(f"**风险：** {d.get('risks','')}")

    with st.expander("标题评分检查（默认折叠，减少上下滑动）", expanded=False):
        sc = score_title_es(selected)
        cols = st.columns(2)
        for n, (status, msg) in enumerate(sc["checks"]):
            with cols[n % 2]:
                if status == "通过":
                    st.success(msg)
                else:
                    st.warning(msg)

    with st.expander("高级：关键词参考与三态表（默认折叠，聊天标题优先）", expanded=False):
        st.markdown("### 关键词参考 / 必须词 / 禁止词")
        st.caption("现在主流程建议用标题聊天工作台。这里主要给新手查看关键词中文含义，或在特殊情况下手动设置必须/禁止词。")
        st.markdown("### 新手关键词三态优化（推荐）")
        st.caption("不用懂西语：✅必须包含 = 下一轮标题一定要自然出现；➖可选 = 可出现可不出现；🚫禁止出现 = 下一轮标题绝不能出现。自定义词加入后会自动进入 ✅必须包含，方便连续迭代。")

        # Initialize default must keywords only once, using the current product facts and candidate pool.
        keyword_pool = title_keyword_pool_es(st.session_state.get("title_candidates", []))
        if "title_must_keywords" not in st.session_state:
            default_phrases = []
            for x in keyword_pool:
                lab = (x.get("phrase", "") + " " + x.get("cn", "")).lower()
                if any(k in lab for k in ["lámpara colgante", "ratán", "mimbre", "e27", "salón", "comedor"]):
                    default_phrases.append(x.get("phrase", ""))
            st.session_state["title_must_keywords"] = default_phrases[:8]
        if "title_banned_keywords" not in st.session_state:
            st.session_state["title_banned_keywords"] = []

        st.markdown("<div class='title-compact-note'>先在下面表格里把关键词设为 ✅/➖/🚫。也可以直接补充必须词或禁止词：必须词会进入红色勾选区，禁止词会进入黑红删除区，并会持续参与后续迭代和多语言标题。</div>", unsafe_allow_html=True)
        custom_cols = st.columns([2.2, 0.9, 2.2, 0.9, 0.85, 0.85])
        with custom_cols[0]:
            st.text_input("补充必须关键词", key="title_custom_keywords", help="多个用逗号分隔。例如：pantalla de ratán, efecto de sombras, diseño artesanal。")
        with custom_cols[1]:
            if st.button("加入必须", use_container_width=True):
                added = add_custom_keywords_to_state(st.session_state.get("title_custom_keywords", ""), as_must=True)
                if added:
                    st.success("已加入必须：" + ", ".join(added))
                    st.rerun()
                else:
                    st.info("请先输入关键词。")
        with custom_cols[2]:
            st.text_input("补充禁止关键词", key="title_custom_banned_keywords", help="多个用逗号分隔。例如：bambú, moderno, industrial。")
        with custom_cols[3]:
            if st.button("加入禁止", use_container_width=True):
                added = add_custom_keywords_as_banned(st.session_state.get("title_custom_banned_keywords", ""))
                if added:
                    st.success("已加入禁止：" + ", ".join(added))
                    st.rerun()
                else:
                    st.info("请先输入禁止词。")
        with custom_cols[4]:
            if st.button("清空必须", use_container_width=True):
                st.session_state["title_must_keywords"] = []
                st.rerun()
        with custom_cols[5]:
            if st.button("清空禁止", use_container_width=True):
                st.session_state["title_banned_keywords"] = []
                st.rerun()

        # Refresh pool after any custom additions and merge persistent states.
        keyword_pool = title_keyword_pool_es(st.session_state.get("title_candidates", []))
        must_set = {x.lower() for x in st.session_state.get("title_must_keywords", [])}
        ban_set = {x.lower() for x in st.session_state.get("title_banned_keywords", [])}
        rows = []
        for x in keyword_pool:
            phrase = x.get("phrase", "")
            key = phrase.lower()
            if key in ban_set:
                state = "🚫 禁止出现"
            elif key in must_set:
                state = "✅ 必须包含"
            else:
                state = "➖ 可选"
            rows.append({"状态": state, "关键词": phrase, "中文解释": x.get("cn", "")})

        edited_rows = st.data_editor(
            rows,
            key="keyword_state_editor_v154",
            hide_index=True,
            use_container_width=True,
            height=min(520, 58 + 32 * max(4, len(rows))),
            column_config={
                "状态": st.column_config.SelectboxColumn("状态", help="✅必须包含 / ➖可选 / 🚫禁止出现", width="small", options=["✅ 必须包含", "➖ 可选", "🚫 禁止出现"]),
                "关键词": st.column_config.TextColumn("西语关键词", width="medium", disabled=True),
                "中文解释": st.column_config.TextColumn("中文解释", width="large", disabled=True),
            },
            disabled=["关键词", "中文解释"],
        )

        # Sync tri-state table into session; this is not a widget key, so it is safe.
        current_must, current_ban = [], []
        edited_records = editor_rows_to_records(edited_rows)
        for r in edited_records:
            if not isinstance(r, dict):
                continue
            phrase = str(r.get("关键词", "")).strip()
            state = str(r.get("状态", "➖ 可选"))
            if not phrase:
                continue
            if state.startswith("✅"):
                if keyword_key(phrase) not in {keyword_key(x) for x in current_must}:
                    current_must.append(phrase)
            elif state.startswith("🚫"):
                if keyword_key(phrase) not in {keyword_key(x) for x in current_ban}:
                    current_ban.append(phrase)
        # Auto-merge custom inputs if user clicks generate without pressing add.
        pending_custom = split_keyword_input(st.session_state.get("title_custom_keywords", ""))
        pending_ban = split_keyword_input(st.session_state.get("title_custom_banned_keywords", ""))
        if pending_custom:
            for w in pending_custom:
                if keyword_key(w) not in {keyword_key(x) for x in current_must} and keyword_key(w) not in {keyword_key(x) for x in current_ban}:
                    current_must.append(w)
            add_custom_keywords_to_state(st.session_state.get("title_custom_keywords", ""), as_must=True)
        if pending_ban:
            for w in pending_ban:
                if keyword_key(w) not in {keyword_key(x) for x in current_ban}:
                    current_ban.append(w)
            add_custom_keywords_as_banned(st.session_state.get("title_custom_banned_keywords", ""))
            # Negative list wins if the same phrase was selected as must.
            ban_low = {keyword_key(x) for x in current_ban}
            current_must = [x for x in current_must if keyword_key(x) not in ban_low]
        st.session_state["title_must_keywords"] = current_must
        st.session_state["title_banned_keywords"] = current_ban

        # Render chips AFTER syncing editor state, so the red/ban lists reflect the latest click immediately.
        render_keyword_chips("✅ 当前必须包含：", current_must, "kw-must")
        render_keyword_chips("🚫 当前禁止出现：", current_ban, "kw-ban")

        hcol1, hcol2, hcol3 = st.columns([1.3, 1, 2.2])
        with hcol1:
            if st.button("按三态关键词生成下一轮标题", type="primary", use_container_width=True):
                try:
                    with st.spinner("正在按必须/禁止关键词自然重组标题..."):
                        prev = st.session_state.get("title_candidates", [])
                        new_round = generate_next_title_round_from_keywords(current_must, "", current_ban)
                        st.session_state.setdefault("title_round_history", []).append(prev.copy())
                        st.session_state["title_candidates"] = new_round
                        st.session_state["title_candidate_details"] = generate_title_candidate_details(new_round)
                        st.session_state["selected_es_title"] = new_round[0] if new_round else ""
                        if st.session_state.get("selected_es_title"):
                            st.session_state["last_title_zh"] = cheap_title_zh(st.session_state["selected_es_title"])
                            st.session_state["last_title_zh_source"] = st.session_state["selected_es_title"]
                        notify_done("下一轮标题已生成")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with hcol2:
            if st.button("返回上一轮标题", use_container_width=True):
                hist = st.session_state.get("title_round_history", [])
                if hist:
                    st.session_state["title_candidates"] = hist.pop()
                    st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                    st.session_state["selected_es_title"] = st.session_state["title_candidates"][0] if st.session_state["title_candidates"] else ""
                    st.rerun()
                else:
                    st.info("暂无上一轮。")
        with hcol3:
            st.markdown("<div class='kw-help'>建议：✅选 5–10 个真正重要的词，例如产品类型、材质、尺寸、灯头、风格、主要空间；🚫把错误风格、错误材质、错误场景或不想出现的词设为禁止。系统会按自然语序重排，不会直接堆词。</div>", unsafe_allow_html=True)

    with st.expander("高级：只修改当前选定标题（熟手用）", expanded=False):
        st.text_area("针对这个标题的修改要求（只改当前标题）", key="title_refine_feedback", height=80, help="例如：补上USB-C和28 cm托盘；去掉moderno；强调Retro Cinema；不要写ideal para。")
        st.text_area("系统自动改进建议", value=auto_title_repair_feedback(selected), height=90, disabled=True)
        st.selectbox("把当前标题快速转成哪种样式", ["自然亚马逊标题（推荐）", "结构化特性标题（技术款）", "SEO长标题", "简洁安全标题"], key="candidate_convert_style")
        ac1, ac2, ac3 = st.columns([1,1,1])
        with ac1:
            if st.button("按所选样式转换当前标题"):
                try:
                    old_mode = st.session_state.get("title_format_mode", "自然亚马逊标题（推荐）")
                    st.session_state["title_format_mode"] = st.session_state.get("candidate_convert_style", old_mode)
                    new_title = build_safe_title("ES")
                    st.session_state["title_format_mode"] = old_mode
                    st.session_state["title_candidates"][idx] = new_title
                    st.session_state["selected_es_title"] = new_title
                    st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with ac2:
            if st.button("按评分自动修复当前标题"):
                try:
                    with st.spinner("正在根据评分问题自动修复当前标题..."):
                        auto_fb = auto_title_repair_feedback(selected)
                        new_title = refine_es_title_with_feedback(selected, auto_fb)
                        st.session_state["title_candidates"][idx] = new_title
                        st.session_state["selected_es_title"] = new_title
                        st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with ac3:
            if st.button("按要求优化当前标题"):
                try:
                    with st.spinner("正在按你的修改要求重写当前标题..."):
                        new_title = refine_es_title_with_feedback(selected, st.session_state.get("title_refine_feedback", ""))
                        st.session_state["title_candidates"][idx] = new_title
                        st.session_state["selected_es_title"] = new_title
                        st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

if st.session_state.get("es_text"):
    st.subheader("ES母版预览")
    st.text_area("ES", st.session_state["es_text"], height=700)
    render_stats(st.session_state["es_text"], "ES ")

st.subheader("5）多语言与导出")
st.multiselect("目标国家", ALL_TARGETS, key="targets")
if st.button("生成各国版本"):
    if not st.session_state.get("es_text"):
        st.error("请先生成 ES 母版")
    elif not st.session_state.get("es_locked"):
        st.error("请先锁定 ES 母版")
    else:
        try:
            localized = {}
            es_master = st.session_state["es_text"]
            es_title_for_multilang = st.session_state.get("locked_es_title") or st.session_state.get("selected_es_title") or source_es_title(es_master)
            if es_title_for_multilang:
                es_title_for_multilang = normalize_title_style(clean_title_candidate(es_title_for_multilang), "ES")
                es_master = replace_listing_title(es_master, es_title_for_multilang)
            targets = list(st.session_state.get("targets", []))
            if st.session_state.get("multilang_only_missing"):
                existing = st.session_state.get("localized_texts", {}) or {}
                localized.update(existing)
                targets = [l for l in targets if l not in existing]
            with st.spinner("正在根据锁定ES标题语义骨架生成各国本地化版本..."):
                if st.session_state.get("multilang_generation_mode", "批量合并生成（推荐，快）").startswith("批量"):
                    localized.update(generate_multilang_batch(targets, es_master, es_title_for_multilang))
                else:
                    for lang in targets:
                        core = generate_core(lang, es_master)
                        # Final hard guard. Foreign title must follow the final locked ES title and localized must/ban keyword strategy.
                        core["title"] = foreign_title_from_keyword_strategy(lang, es_title_for_multilang)
                        explain = explain_from_core_or_generate(lang, core)
                        localized[lang] = compose_listing(lang, core, explain)
            st.session_state["localized_texts"] = localized
            notify_done("多语言版本已生成")
        except Exception as e:
            st.error(str(e))

if st.session_state.get("localized_texts"):
    tabs = st.tabs(list(st.session_state["localized_texts"].keys()))
    for tab, lang in zip(tabs, st.session_state["localized_texts"].keys()):
        with tab:
            with st.expander(f"展开查看 {lang} 完整内容", expanded=True):
                st.text_area(lang, st.session_state["localized_texts"][lang], height=760)
                render_stats(st.session_state["localized_texts"][lang], f"{lang} ")

zip_bytes = export_zip()
st.download_button(
    "下载 ZIP",
    data=zip_bytes,
    file_name=st.session_state.get("zip_name", f"SKU_{date.today().isoformat()}_AMAZON-LISTING.zip"),
    mime="application/zip",
)
