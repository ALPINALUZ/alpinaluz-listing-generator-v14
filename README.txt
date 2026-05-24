Alpinaluz Listing Generator V15.5

执行：
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

V15.5 重点：
- 默认标题/五点/长描述最小长度提高：标题 160 起，五点 180 起，长描述 700 起。
- 五点文案改成“卖点标签: 具体说明”格式，更适合 Amazon 阅读和转化。
- 字数检测新增长描述最小字符控制。
- 多语言标题继续使用最终 ES 标题 + 三态关键词策略。
- 增强非西语标题清理，减少 triple pantalla / lámpara colgante / ratán / mimbre 等西语残留。


V15.5 重点：修复关键词过多/否定词过多导致标题塌缩为超短标题；多语言标题残留 triple pantalla/pantalla 等西语词的清理；保留 V15.4 的标签式五点。
