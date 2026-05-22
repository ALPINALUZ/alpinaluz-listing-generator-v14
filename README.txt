Alpinaluz Listing Generator V14.6

主要修复：
1. 进一步统一深色界面，修复白底白字、按钮 hover 难读、上传控件浅色模式显示问题。
2. 多语言标题增加两种方式：
   - 本地SEO润色（推荐）：更像当地 Amazon 标题，不是机械直译。
   - 严格翻译ES标题（最快）：更快、更贴近 ES 标题。
3. 多语言标题继续保持事实与 ES 标题一致，不从事实卡重新乱生成。
4. 修复常见标题格式问题：USB-A / USB-C 大小写、3000K、28 cm、重复 Foco Orientable、德语 integrierter LED、荷兰语 draaibare。
5. 增加“生成完成声音提示”，长时间生成完会弹 toast 并尝试播放提示音。

运行：
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
