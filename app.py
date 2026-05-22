import base64
import io
import json
import re
import zipfile
from datetime import date
from typing import Dict, List, Tuple, Any

import streamlit as st
import streamlit.components.v1 as components

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(page_title="Alpinaluz Listing Generator V14.6", layout="wide")

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


/* V14.6 进一步修复白底白字 / hover 难读 / 上传控件浅色问题 */
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
        "model": "gpt-4.1-mini",
        "targets": ALL_TARGETS.copy(),
        "variant_neutral": True,
        "variant_scope": "标题+Search terms",
        "variant_fields": ["颜色"],
        "variant_terms": "",
        "es_locked": False,
        "max_title": 200,
        "min_title": 140,
        "min_bullet": 150,
        "max_bullet": 250,
        "max_search_terms": 250,
        "ean": "",
        "sku": "",
        "brand": "Alpinaluz",
        "mode": "新手模式",
        "title_strategy": "优先优化原始标题",
        "title_format_mode": "自然亚马逊标题（推荐）",
        "source_text": "",
        "selected_title_idx": 0,
        "content_safety_strict": True,
        "image_light_effect_required": False,
        "foreign_title_mode": "本地SEO润色（推荐）",
        "sound_notify": True,
        "notify_after_multilang": False,
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

    if traditional_socket_context and not explicit_integrated_led:
        socket = socket_match.group(1).upper()
        facts["灯头"] = socket
        facts["是否LED"] = "兼容LED灯泡"
        facts["是否含灯泡"] = "否"
        if not re.search(r"\b(3000k|4000k|6000k|cct|temperatura de color|色温)\b", raw_blob, flags=re.I):
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


def llm(prompt: str, system: str = "You are a senior Amazon marketplace SEO copywriter for lighting products.", temperature: float = 0.35) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("请先在左侧输入 OpenAI API Key")
    resp = client.chat.completions.create(
        model=st.session_state.get("model", "gpt-4.1-mini"),
        temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


def llm_multimodal(prompt: str, files: List[Any], system: str = "You identify lighting product facts from text and images.") -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("请先在左侧输入 OpenAI API Key")
    content = [{"type": "text", "text": prompt}]
    for f in files[:8]:
        try:
            data = f.getvalue()
            mime = f.type or "image/jpeg"
            b64 = base64.b64encode(data).decode("utf-8")
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
        except Exception:
            continue
    resp = client.chat.completions.create(
        model=st.session_state.get("model", "gpt-4.1-mini"),
        temperature=0.15,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
    )
    return resp.choices[0].message.content.strip()



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
    return st.session_state.get(f"fact::{label}", "")


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


def image_names_for_prompt() -> str:
    files = st.session_state.get("uploaded_images", []) or []
    if not files:
        return ""
    excluded = []
    used = []
    for f in files:
        key = f"exclude_img::{f.name}"
        if st.session_state.get(key):
            excluded.append(f.name)
        else:
            used.append(f.name)
    out = []
    if used:
        out.append("Used images: " + ", ".join(used))
    if excluded:
        out.append("Excluded images: " + ", ".join(excluded))
    return "\n".join(out)


def images_for_analysis() -> List[Any]:
    files = st.session_state.get("uploaded_images", []) or []
    return [f for f in files if not st.session_state.get(f"exclude_img::{f.name}")]


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
    raw = llm_multimodal(prompt, files) if files else llm(prompt, system="You extract product facts and output JSON only.", temperature=0.1)
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


def normalize_title_style(title: str, lang: str) -> str:
    title = normalize_title_units(clean_title_candidate(title))
    if lang == "ES":
        return normalize_title_units(spanish_title_case(title))
    if lang == "EN":
        return normalize_title_units(title_case_en_like(title))
    # 其他欧洲语言不要强行全词首大写，交给模型；只修正常见缩写和单位。
    return normalize_title_units(title)

def remove_water_phrases(title: str) -> str:
    t = title
    for phrase in WATER_TITLE_PHRASES:
        t = re.sub(rf"(?i)\b{re.escape(phrase)}\b", "", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    return t.strip(" ,;-–—")


def normalize_title_units(title: str) -> str:
    t = str(title or "")
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
    # Language-specific grammar/typo hotfixes from repeated tests.
    t = t.replace("mit integrierte LED", "mit integrierter LED")
    t = t.replace("draaibaare", "draaibare")
    t = t.replace("USB-a", "USB-A").replace("USB-c", "USB-C")
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
        r"\bEstructura\s+de\s+Acero\b", r"\bL[aá]mpara\b", r"\bDormitorio\b", r"\bSal[oó]n\b"
    ]
    if lang == "IT":
        return common + spanish_residual
    if lang in {"DE", "NL", "PL", "SE", "EN"}:
        return common + spanish_residual
    if lang == "FR":
        return common + [r"\bFoco\s+Orientable\b", r"\bAplique\s+de\s+Pared\b"]
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
    series = get_fact("系列名") if not has_cjk(get_fact("系列名")) else ""
    product = map_value("产品类型", get_field("产品类型"), lang) or {
        "ES":"aplique de pared", "FR":"applique murale", "DE":"Wandleuchte", "IT":"applique da parete", "NL":"wandlamp", "PL":"kinkiet", "PT":"aplique de parede", "SE":"vägglampa", "EN":"wall light"
    }.get(lang, "wall light")
    light = map_value("灯头", get_field("灯头"), lang) or map_value("是否LED", get_field("是否LED"), lang)
    power = clean_power_value(get_fact("最大功率W"))
    cct = map_value("光色调节", get_fact("光色调节"), lang) or ("CCT " + "/".join([x + "K" for x in normalize_to_list(get_fact("色温K")) if x.isdigit()]) if normalize_to_list(get_fact("色温K")) else "")
    if "3000" in str(get_fact("色温K")) and "4000" in str(get_fact("色温K")) and "6000" in str(get_fact("色温K")):
        cct = "CCT 3000K/4000K/6000K"
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
    short_map = {
        "ES": f"{p['brand']} {p['product']} {p['light']} {p['power']} con CCT 3000K/4000K/6000K y USB-C",
        "EN": f"{p['brand']} {p['light']} {p['product']} {p['power']} with CCT 3000K/4000K/6000K and USB-C",
        "DE": f"{p['brand']} {p['product']} mit {p['light']} {p['power']}, CCT 3000K/4000K/6000K und USB-C",
        "IT": f"{p['brand']} {p['product']} {p['light']} {p['power']} con CCT 3000K/4000K/6000K e USB-C",
        "FR": f"{p['brand']} {p['product']} {p['light']} {p['power']} avec CCT 3000K/4000K/6000K et USB-C",
        "PT": f"{p['brand']} {p['product']} {p['light']} {p['power']} com CCT 3000K/4000K/6000K e USB-C",
        "NL": f"{p['brand']} {p['light']} {p['product']} {p['power']} met CCT 3000K/4000K/6000K en USB-C",
        "PL": f"{p['brand']} {p['product']} {p['light']} {p['power']} z CCT 3000K/4000K/6000K i USB-C",
        "SE": f"{p['brand']} {p['product']} {p['light']} {p['power']} med CCT 3000K/4000K/6000K och USB-C",
    }
    return normalize_title_style(short_map.get(lang, f"{p['brand']} {p['product']} {p['light']}"), lang)

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
- For Spanish: title MUST start with Alpinaluz; use Spanish Amazon title case; do not use filler phrases such as ideal para/perfecto para.
- For non-Spanish languages: do NOT use Spanish phrases such as Aplique de Pared, Foco Orientable, Dormitorio, Salón, Bandeja, Puertos. Translate the title fully into the target language.
- Title capitalization: EN uses Amazon Title Case; ES uses Spanish Title Case; DE uses natural German capitalization; FR/IT/PT/NL/PL/SE use native marketplace style, not Spanish capitalization.
- Do not output Chinese characters or placeholder brackets like [壁灯].
- Keep only useful words: brand, product type, style if locked, socket/LED, material/color if relevant, key use/room.
- Use a readable Amazon title format with separators when useful, e.g. “Product – Feature: detail, Feature: detail”. Do not output a raw list of disconnected keywords.

Product facts:
{facts}

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


def foreign_title_from_es(lang: str, es_title: str) -> str:
    """Translate/localize the locked ES title only. This prevents foreign titles from drifting to wrong facts."""
    es_title = clean_title_candidate(es_title)
    if not es_title:
        return ""
    cache = st.session_state.setdefault("title_translation_cache", {})
    cache_key = f"{lang}::{es_title}::{st.session_state.get('max_title', 200)}::{st.session_state.get('foreign_title_mode', '本地SEO润色（推荐）')}"
    if cache_key in cache:
        return cache[cache_key]
    max_len = int(st.session_state.get("max_title", 200))
    mode = st.session_state.get("foreign_title_mode", "本地SEO润色（推荐）")
    if mode.startswith("严格"):
        localize_instruction = "Translate accurately and keep the ES title order as much as possible, but make grammar natural."
        temp = 0.10
    else:
        localize_instruction = "Rewrite as a native high-converting Amazon title for the local marketplace. You may reorder phrases to match local search habits, but must keep the same facts. Do not sound like a machine translation."
        temp = 0.22
    prompt = f"""
Translate/localize this locked Amazon.es title into native {LANGS[lang]['name']} for {LANGS[lang]['market']}.

ES title source:
{es_title}

Localization mode:
{localize_instruction}

Rules:
- Keep EXACTLY the same product facts and commercial meaning as the ES title.
- Do NOT add specifications that are not present in the ES title. If the ES title has no CCT/3000K/4000K/6000K, do not add CCT. If it has no tray/bandeja, do not add tray.
- Do NOT remove important facts from the ES title: product type, style, material/colour, socket/LED, adjustment, room/use.
- Native Amazon marketplace style, readable and commercial, not a raw keyword chain.
- Avoid mechanical labels such as "CCT:", "Spot:", "Charging:", "Tray:" unless they are natural in that language.
- Prefer a natural title like: Brand + product type + key style/function + socket/LED + material/colour + main use.
- No Chinese, no Spanish leftovers unless the term is a universal code such as E27, LED, USB-C, IP20.
- No SKU/model code.
- <= {max_len} characters. Shorter is acceptable if complete and natural.
- EN uses Amazon Title Case. DE uses natural German capitalization. FR/IT/PT/NL/PL/SE use native marketplace style.
- Fix obvious grammar, capitalization and unit format: USB-A, USB-C, 3000K, 28 cm.
Return ONLY the final title, one line.
"""
    raw = llm(prompt, system="You are a native Amazon marketplace title localizer for lighting products. Return one polished title only.", temperature=temp)
    title = normalize_title_style(clean_title_candidate(raw.splitlines()[0]), lang)
    title = clean_variants(title, lang, "TITLE")
    if not title_is_valid(title, lang):
        raw = llm(prompt + "\nCRITICAL: previous title failed validation. Output a clean native title with no Chinese, no placeholders, no added specs.", system="Strict marketplace title translator. One line only.", temperature=0.05)
        title = normalize_title_style(clean_variants(clean_title_candidate(raw.splitlines()[0]), lang, "TITLE"), lang)
    if not title_is_valid(title, lang):
        title = build_safe_title(lang)
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
    max_st = int(st.session_state.get("max_search_terms", 250))
    st.markdown(f"**{prefix}字数检测**")

    def row(label: str, value: int, ok: bool, extra: str = "") -> None:
        klass = "stat-ok" if ok else "stat-bad"
        st.markdown(f"<div class='{klass}'>{label}: {value} 字符 {extra}</div>", unsafe_allow_html=True)

    row("标题", len(title), min_title <= len(title) <= max_title, f"/ 建议 {min_title}-{max_title}")
    for i in range(5):
        val = len(bullets[i]) if i < len(bullets) else 0
        row(f"五点{i+1}", val, min_bullet <= val <= max_bullet, f"/ 建议 {min_bullet}-{max_bullet}")
    row("长描述", len(description), len(description) >= 350, "/ 建议≥350")
    row("Search terms", len(search_terms), len(search_terms) <= max_st, f"/ 建议≤{max_st}")
    warns = safety_warnings(title + "\n" + extract_section(listing_text, "DESCRIPTION") + "\n" + extract_section(listing_text, "BULLETS"))
    if warns:
        st.warning("；".join(sorted(set(warns))))


def score_title_es(title: str) -> Dict[str, Any]:
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

    check(t.lower().startswith("alpinaluz"), "品牌 Alpinaluz 第一位", 25)
    check(min_len <= len(t) <= max_len, f"长度 {len(t)} / {min_len}-{max_len}", 20)
    check(not find_model_codes(t), "无 SKU / 型号代码", 20)
    check(t.split()[-1].lower().strip(".,;:-–—") not in TRAILING_BAD, "不是介词/连接词结尾", 20)
    check(not any(re.search(rf"(?i)\b{re.escape(p)}\b", t) for p in WATER_TITLE_PHRASES), "无 ideal para / perfecto para 等水词", 15)
    product_es = map_value("产品类型", get_field("产品类型"), "ES")
    if product_es:
        check(product_es.lower().split()[0] in t.lower(), f"包含产品类型：{product_es}", 10)
    socket = map_value("灯头", get_field("灯头"), "ES")
    if socket and socket not in {"sin portalámparas"}:
        check(socket.lower() in t.lower(), f"包含灯头/光源：{socket}", 10)
    style = map_value("风格", get_field("风格"), "ES")
    banned = [x.strip().lower() for x in get_fact("禁用风格词").replace("，", ",").split(",") if x.strip()]
    if banned:
        check(not any(b in t.lower() for b in banned), "未出现禁用风格词", 20)
    return {"score": max(score, 0), "checks": checks, "len": len(t)}




def generate_title_candidate_details(candidates: List[str]) -> List[Dict[str, Any]]:
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
Si hay título original/manual y está bien, optimízalo sin destruir su estructura.

Reglas duras:
- Los 4 títulos deben empezar EXACTAMENTE por Alpinaluz.
- Longitud objetivo: {min_len}-{max_len} caracteres. Mejor corto y correcto que largo con relleno.
- No usar frases de relleno: ideal para, perfecto para, bonito, precioso, para todo tipo de espacios.
- No incluir SKU/modelo.
- No terminar con preposición/conector.
- Usar Title Case español: palabras importantes con inicial mayúscula; de, del, para, con, sin, y, en en minúscula.
- Crear 4 estilos:
  1) Natural Amazon: título fluido, legible, con comas moderadas, sin etiquetas excesivas.
  2) SEO equilibrado: más keywords pero todavía natural.
  3) Técnico estructurado: pocas etiquetas útiles como “CCT”, “Carga”, “Bandeja”.
  4) Corto seguro: más breve, claro y estable.
- No crear una lista mecánica de palabras sueltas. Las etiquetas tipo “Característica: detalle” solo se usan en el estilo técnico.
- Respetar estilo bloqueado. Si el estilo es Retro/Vintage/Cinema, NO escribir moderno/minimalista salvo que el usuario lo permita.
- Resolver colores complejos sin confundir partes: cable, pantalla, base y cuerpo.
- Si el producto usa E27/E14/GU10/G9 y la bombilla no está incluida, no insinuar que incluye bombilla.

Facts:
{facts_for_prompt('ES')}

Devuelve JSON:
{{"candidates": ["natural...", "seo...", "tecnico...", "corto..."]}}
"""
    raw = llm(prompt, system="You are a strict Amazon.es title specialist. Output JSON only.", temperature=0.35)
    data = safe_json(raw, {"candidates": []})
    cands = data.get("candidates", []) if isinstance(data, dict) else []
    out = []
    for c in cands[:5]:
        c = ensure_title(str(c), "ES", facts_for_prompt("ES"))
        c = spanish_title_case(remove_water_phrases(c))
        if c and c not in out:
            out.append(c)
    while len(out) < 4:
        fallback = build_safe_title("ES")
        if fallback not in out:
            out.append(fallback)
        else:
            break
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
- No usar relleno como ideal para/perfecto para.
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

def build_core_prompt(lang: str, es_master: str = "", locked_title: str = "") -> str:
    market = LANGS[lang]["market"]
    min_title = int(st.session_state.get("min_title", 140))
    max_title = int(st.session_state.get("max_title", 200))
    min_bullet = int(st.session_state.get("min_bullet", 150))
    max_bullet = int(st.session_state.get("max_bullet", 250))
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

Hard rules:
- {title_rule}
- Do NOT include SKU/model code in title, bullets, description, search terms, or A+.
- Title must be natural and complete. Never cut a sentence.
- Title should be readable, not a raw keyword chain. Prefer “Product – Feature: detail, Feature: detail” for technical products.
- Do not output Chinese characters or placeholder brackets like [壁灯] in any target-language field.
- If language is not Spanish, do not leave Spanish phrases such as Aplique de Pared, Foco Orientable, Dormitorio, Salón, Bandeja, Puertos. Translate product type, room, material and colour fully into the target language.
- For integrated LED products, say LED integrated / built-in LED naturally in the target language and do NOT mention replaceable bulbs unless confirmed.
- 5 bullets, each ideally between {min_bullet} and {max_bullet} characters.
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

{es_extra}

FACTS:
{facts_for_prompt(lang)}

JSON format:
{{
  "title": "...",
  "bullets": ["...","...","...","...","..."],
  "description": "...",
  "search_terms": "...",
  "aplus": "模块1 标题：...\n模块1 正文：...\n模块1 中文配图提示：...\n..."
}}
"""


def sanitize_core(lang: str, core: Dict[str, Any], locked_title: str = "") -> Dict[str, Any]:
    title = locked_title or str(core.get("title", "")).strip().replace("\n", " ")
    title = ensure_title(title, lang, facts_for_prompt(lang))

    bullets = [remove_safety_bad_phrases(str(x).strip().replace("\n", " ")) for x in core.get("bullets", [])][:5]
    while len(bullets) < 5:
        bullets.append("")
    bullets = [clean_variants(b, lang, "BULLETS") for b in bullets]

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

    return {"title": title, "bullets": bullets, "description": description, "search_terms": search_terms, "aplus": aplus}


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
    aligned_title = foreign_title_from_es(lang, es_title) if (lang != "ES" and es_title) else ""

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
            core["title"] = foreign_title_from_es(lang, es_title)
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


def compose_listing(lang: str, core: Dict[str, Any], explain: Dict[str, Any]) -> str:
    out = [f"[{lang}]", "", "[TITLE]", core["title"], "", "[标题中文解释]", str(explain.get("title_cn", "")).strip(), ""]
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
        if st.session_state.get("es_text"):
            zf.writestr("listing/ES_Listing.txt", st.session_state["es_text"])
        for lang, text in st.session_state.get("localized_texts", {}).items():
            zf.writestr(f"listing/{lang}_Listing.txt", text)
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
    st.selectbox("模型", ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"], key="model")
    st.radio("使用模式", ["新手模式", "专业模式"], key="mode", help="新手模式：先识别事实卡，再生成标题候选和ES母版。专业模式：保留更多可调项。")
    st.checkbox("快速多语言生成（推荐）", key="fast_multilang", value=True, help="锁定ES后，各国正文少重试，速度更快。标题仍会按下面的方式生成。")
    st.selectbox("多语言标题方式", ["本地SEO润色（推荐）", "严格翻译ES标题（最快）"], key="foreign_title_mode", help="本地SEO润色：标题更自然，更像当地Amazon；严格翻译：速度更快、更贴近ES标题。")
    st.checkbox("生成完成声音提示", key="sound_notify", value=st.session_state.get("sound_notify", True), help="长时间等待多语言生成时，完成后播放一声提示。部分浏览器可能需要允许声音。")
    st.divider()
    st.markdown("### 长度控制")
    st.number_input("标题最小字符", min_value=80, max_value=220, key="min_title")
    st.number_input("标题最大字符", min_value=100, max_value=220, key="max_title")
    st.number_input("五点最小字符", min_value=80, max_value=260, key="min_bullet")
    st.number_input("五点最大字符", min_value=100, max_value=300, key="max_bullet")
    st.number_input("Search terms 最大字符", min_value=80, max_value=250, key="max_search_terms")
    st.divider()
    if st.button("清空生成结果（保留输入）"):
        for k in ["es_core", "es_explain", "es_text", "localized_texts", "es_locked", "title_candidates", "selected_es_title"]:
            st.session_state.pop(k, None)
        st.success("已清空生成结果")
    if st.button("仅清空图片"):
        st.session_state["uploaded_images"] = []
        st.success("已清空图片")

st.title("Alpinaluz Listing Generator V14.6")
st.caption("新手/专业双模式 · ES标题对齐多语言 · 产品事实卡 · 平台安全检查 · A+场景/特性结构")

if st.session_state.get("mode") == "新手模式":
    st.info("新手流程：①上传资料 → ②AI识别产品事实卡 → ③确认事实 → ④生成3个ES标题候选 → ⑤选择标题生成ES母版 → ⑥锁定后生成各国版本。")

left, right = st.columns([1.2, 1])
with left:
    st.subheader("1）资料输入")
    st.text_input("SKU", key="sku")
    st.text_input("EAN", key="ean")
    st.text_input("品牌", key="brand", help="标题必须以 Alpinaluz 开头；除非你明确修改品牌。")
    st.text_area("网站原始内容 / 老链接内容", key="source_text", height=150, help="权重高。把网站标题、描述、参数粘贴进来，AI会优先从这里提取事实。")
    st.text_area("手动标题（可选）", key="manual_title", height=80, help="权重很高。默认策略会优先优化原始标题，而不是推翻重写。")
    st.text_area("技术备注", key="tech_notes", height=100, help="权重最高。写不能错的事实：E27、不含灯泡、IP44、直径、材质、不可精确调角度等。")
    st.text_area("SEO关键词", key="keywords", height=80, help="权重中等。用于补充标题和Search terms，不会覆盖产品事实。")
    st.text_area("手动长描述（可选）", key="manual_description", height=90, help="权重中等。用于补充场景和卖点，不会逐字复制。")
    files = st.file_uploader("上传图片（可多张）", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, help="用于识别颜色、材质、结构、风格。不要上传带灯泡详情的图片，容易误判为含灯泡。")
    if files is not None:
        st.session_state["uploaded_images"] = files
    if st.session_state.get("uploaded_images"):
        st.markdown("**图片用途检查**")
        for f in st.session_state["uploaded_images"]:
            st.checkbox(f"排除这张图用于事实识别：{f.name}", key=f"exclude_img::{f.name}", help="比如带灯泡详情、尺寸不对应、有Logo、不是当前SKU的图。")
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
            st.text_input("系列名", key="fact::系列名")
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
                st.session_state["selected_title_idx"] = 0
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
                explain = generate_explain("ES", core["title"], core["bullets"], core["description"], core["search_terms"])
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
            st.session_state["es_locked"] = True
            st.success("ES 已锁定")
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
    idx = st.radio("选择一个标题作为ES母版标题", list(range(len(labels))), format_func=lambda i: labels[i], horizontal=False, key="selected_title_idx")
    selected = st.session_state["title_candidates"][idx]
    st.session_state["selected_es_title"] = selected
    d = details[idx] if idx < len(details) else {}
    st.text_area("选定标题", value=selected, height=80)
    st.text_area("针对这个标题的修改要求（只改当前标题）", key="title_refine_feedback", height=80, help="例如：补上USB-C和28 cm托盘；去掉moderno；强调Retro Cinema；不要写ideal para。")
    st.selectbox("把当前标题快速转成哪种样式", ["自然亚马逊标题（推荐）", "结构化特性标题（技术款）", "SEO长标题", "简洁安全标题"], key="candidate_convert_style")
    c_ref1, c_ref2 = st.columns([1, 2])
    with c_ref1:
        if st.button("按所选样式转换标题"):
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
        if st.button("按要求优化这个标题"):
            try:
                with st.spinner("正在按你的修改要求重写当前标题..."):
                    new_title = refine_es_title_with_feedback(selected, st.session_state.get("title_refine_feedback", ""))
                    st.session_state["title_candidates"][idx] = new_title
                    st.session_state["selected_es_title"] = new_title
                    st.session_state["title_candidate_details"] = generate_title_candidate_details(st.session_state["title_candidates"])
                st.rerun()
            except Exception as e:
                st.error(str(e))
    with c_ref2:
        st.caption("这两个按钮只针对当前选中的标题：可以先转换成不同标题样式，再按你的修改要求继续优化。")
    with st.expander("这个标题的中文解释 / 优点 / 风险", expanded=True):
        st.markdown(f"**中文解释：** {d.get('cn','')}")
        st.markdown(f"**优点：** {d.get('pros','')}")
        st.markdown(f"**风险：** {d.get('risks','')}")
    sc = score_title_es(selected)
    cols = st.columns(2)
    for n, (status, msg) in enumerate(sc["checks"]):
        with cols[n % 2]:
            if status == "通过":
                st.success(msg)
            else:
                st.warning(msg)

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
            with st.spinner("正在生成各国版本..."):
                for lang in st.session_state.get("targets", []):
                    core = generate_core(lang, es_master)
                    explain = generate_explain(lang, core["title"], core["bullets"], core["description"], core["search_terms"])
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
