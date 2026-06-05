Alpinaluz Listing Generator V17.7

重点：
- 保留 V17.6 的标题信息预算、A/B/C 三级取舍、多语标题自动预审和压缩。
- 新增低误报风险引擎：红色必须修，黄色建议看，灰色/低置信提示不打扰新手。
- 增加多语言产品类型同义词识别，避免 Stehlampe / Vloerlamp / Lampadaire / Lampada da Terra / Lampa Podłogowa 被误判为缺失“落地灯类型”。
- 修复木头颜色误报：madera natural / natural wood / Naturholz 作为材质/饰面处理，不再误判成必须出现“金色/黄铜色”。
- 风险提示优先使用当前 ES 定稿标题和当前事实卡，降低上一个产品的 G9/GU10/E27 或颜色信息污染。
- “确认全部绿色标题”更安全，只拦截真正硬风险，减少无效人工检查。

本地运行：
Mac: 双击 run.command
Windows: 双击 run_windows.bat

Streamlit Cloud 上传：
app.py
requirements.txt
README.txt
可选：run.command / run_windows.bat
