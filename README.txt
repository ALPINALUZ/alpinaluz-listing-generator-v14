Alpinaluz Listing Generator V16.6

运行方式（本地）：
Mac：双击 run.command
Windows：双击 run_windows.bat

云端 Streamlit：
只需要上传 app.py 和 requirements.txt 到 GitHub；如需保留本地双击运行，同时上传 run.command 和 run_windows.bat。

V16.6 重点：
- 修复系列名 SUNSET 被误删导致英文标题出现 “with -Effect Glass Globe” 的问题。
- 修复德语/多语言标题和描述中类似 “mit -Leuchtmitteln” 的残缺片段。
- 多语言标题继续使用 ES 最终标题语义骨架本地化，减少自由翻译翻车。
- 中文标题解释改为规则同步生成，避免出现“此标题按要求原样保留”等误导内容。
- 五点卖点标签更自然，避免机器味的两词硬标签，例如 Montaje Ordenado / Vidrio Trabajado。
- ZIP 默认只导出 listing 文件夹，quality / tech_specs 仍在高级导出设置中可选。

建议流程：
1. 上传主图、尺寸图、关键细节图。
2. AI识别/更新产品事实卡。
3. 生成 ES 标题候选。
4. 在标题聊天工作台用中文修改标题，直到满意。
5. 生成 ES 母版并检查事实。
6. 锁定 ES 母版。
7. 批量生成多语言。
8. 下载 ZIP。
