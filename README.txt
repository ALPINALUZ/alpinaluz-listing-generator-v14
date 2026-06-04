Alpinaluz Listing Generator V16.9

重点：
- 基于 V16.6 稳定版修复，不采用 V16.7 的强制标题美化逻辑。
- 多语言标题不再只读取最终 ES 标题，而是用 ES 标题 + ES母版 + 原始资料提取语义骨架，避免 FR/EN/DE/IT 等国家标题省略日落效果、金色底座、玻璃颜色等高价值信息。
- 多语言标题使用更短的标题专用短语，尽量保留核心视觉卖点，同时不把标题写成技术参数表。
- 修复常见语言残留：IT stile moderna、NL modern stijl、DE -Leuchtmittel、sunset 英文残留等。
- 保留 V16.6 标题聊天工作台和双击运行。

运行：
Mac：双击 run.command
Windows：双击 run_windows.bat

Streamlit Cloud：上传 app.py、requirements.txt、README.txt 即可。
