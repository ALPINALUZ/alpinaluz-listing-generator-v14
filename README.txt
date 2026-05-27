Alpinaluz Listing Generator V16.1

执行：
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

V16.1 重点：
- 保持 GPT-5.4 作为日常主力模型，继续降低成本和等待时间。
- 多语言生成新增“批量合并生成”：每次请求同时生成多个国家，减少重复输入 prompt 和多次等待。
- 多语言中文解释与外语正文合并在同一次 JSON 输出中，减少额外 API 调用。
- 多语言标题继续以最终锁定 ES 标题 + 三态关键词策略为真源，避免从事实卡跑偏。
- 多语言标题更强调本地 Amazon 语序和大小写，避免机械直译和西语残留。
- 支持“只生成缺失国家”，已生成的国家不重跑，方便只补新站点或单独重试。
- 保留逐国稳定生成模式，必要时用于定位某个国家的问题。
- 保留原文增强策略：已有优质标题/五点/描述时，只优化不压缩、不负优化。
- 继续禁止标题水词：ideal para、perfecto para、compatible、bombilla no incluida、sin bombilla 等。

建议使用流程：
1. 日常新链接用默认 GPT-5.4 + 标准图片识别前3张。
2. 如果原文很完整，保持“优质原文保留增强”。
3. 先生成 ES 标题候选，用关键词池快速调整。
4. 确认 ES 母版后锁定。
5. 多语言生成方式使用“批量合并生成（推荐，快）”，批量每组国家数建议 4。
6. 如果只需要补某个站点，勾选“只生成缺失国家”或取消不需要的目标国家。


V16.1 修复：上传多张同名图片时，排除图片复选框不再触发 StreamlitDuplicateElementKey。
