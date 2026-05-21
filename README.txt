Alpinaluz Listing Generator V14.4

执行：
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

V14.4 重点：
- 统一深色界面：黑底浅字，输入框、预览框、字数检测都保持高对比度。
- 标题格式增加 4 种样式：自然亚马逊标题、结构化特性标题、SEO长标题、简洁安全标题。
- 默认改为自然亚马逊标题，避免标题像机械参数表或关键词堆砌。
- 每个候选标题可快速转换成任意样式，再按局部修改要求继续优化。
- 保留多语言标题校验：禁中文、禁占位符、禁西语残留、禁SKU误删USB-C/USB-A。
- 修复/保留 CCT 3000K/4000K/6000K 完整性。
