# -*- coding: utf-8 -*-
path = r"e:\3311 AI\generate_community_doc.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    for func in ("add_para", "add_bullet"):
        key = func + "(doc, "
        if stripped.startswith(key):
            body = stripped[len(key) :]
            if body.startswith('"'):
                if ", indent=True)" in body:
                    end_marker = ", indent=True)"
                    end_q = body.rindex('"', 0, body.index(end_marker))
                    text = body[1:end_q]
                    line = indent + key + "'" + text + "'" + end_marker + "\n"
                elif ", bold=True)" in body:
                    end_marker = ", bold=True)"
                    end_q = body.rindex('"', 0, body.index(end_marker))
                    text = body[1:end_q]
                    line = indent + key + "'" + text + "'" + end_marker + "\n"
                elif body.rstrip().endswith(")"):
                    end_q = body.rindex('"')
                    text = body[1:end_q]
                    tail = body[end_q + 1 :]
                    line = indent + key + "'" + text + "'" + tail
                    if not line.endswith("\n"):
                        line += "\n"
            break
    new_lines.append(line)

# Fix table rows: replace inner "..." with 「...」 in lines that look like table rows
import re
final = []
for line in new_lines:
    s = line.strip()
    if s.startswith("[") and s.endswith("],") or s.endswith("]"):
        def fix_inner(m):
            return "「" + m.group(1) + "」"
        # only replace quotes that appear inside a cell (second+ quote pairs in complex cells)
        if s.count('"') > 2:
            parts = line.split('"')
            rebuilt = parts[0]
            for idx in range(1, len(parts)):
                if idx % 2 == 1 and len(parts[idx]) < 40 and any("\u4e00" <= c <= "\u9fff" for c in parts[idx]):
                    # likely Chinese quoted term inside table cell
                    if parts[idx - 1].endswith("作为") or parts[idx - 1].endswith("是") or "「" not in parts[idx]:
                        # check if this is a table key vs inner quote
                        if idx > 1 and parts[idx - 1][-1] not in (",", "[", " "):
                            rebuilt += "「" + parts[idx] + "」"
                        else:
                            rebuilt += '"' + parts[idx] + '"'
                    else:
                        rebuilt += '"' + parts[idx] + '"'
                elif idx % 2 == 1:
                    rebuilt += '"' + parts[idx]
                else:
                    rebuilt += parts[idx]
            line = rebuilt
    final.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(final)
print("done")
