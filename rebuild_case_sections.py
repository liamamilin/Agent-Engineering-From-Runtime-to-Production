# -*- coding: utf-8 -*-
"""维护工具：重建 M0-M11 + Capstone 章节的"完整案例"小节（用 code/ 最新代码）。

gen_case_sections.py 只在旧小节不存在时注入；本工具用于【替换】已有小节，
供代码更新（如加注释）后同步章节快照。节选输出 OUTPUTS 不变（注释不影响运行输出）。

用法（在本书根目录运行）：
    python rebuild_case_sections.py
"""
import os

import gen_case_sections as G


def rebuild():
    for qmd, anchor, case_title, code_file, points in G.CASES:
        path = os.path.join(G.CH, qmd)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        sec_anchor = "{#sec-%s-case}" % qmd.split(".")[0].lower()
        title_line = f"{case_title} {sec_anchor}"

        start = content.find(title_line)
        if start == -1:
            print(f"!! {qmd}: 找不到案例标题行，跳过")
            continue
        end = content.find(anchor, start)
        if end == -1:
            print(f"!! {qmd}: 找不到结束锚点 {anchor!r}，跳过")
            continue
        section = G.build_section(case_title, code_file, points, sec_anchor)
        content = content[:start] + section + content[end:]
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"OK {qmd}: 案例小节已重建（{code_file}）")


if __name__ == "__main__":
    rebuild()
