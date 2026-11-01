import os, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 1) Inspect the managed-cluster node in kubernetes zone
root = r"D:\aiops-roadmap\content\kubernetes"
target = None
for f in sorted(os.listdir(root)):
    if not f.endswith(".md"):
        continue
    t = open(os.path.join(root, f), encoding="utf-8").read()
    if "managed cluster" in t and "ZH_UI" in t:
        target = (f, t)
        break

if target:
    f, t = target
    print("FILE:", f)
    fm = t.split("---")[1]
    for m in re.finditer(r'question:\s*"(.{0,90})', fm):
        print("  EN-Q:", m.group(1)[:90])
    idx = t.find("<!-- ZH_UI -->")
    print("--- ZH_UI block (first 900 chars) ---")
    print(t[idx:idx+900])
else:
    print("No kubernetes file with 'managed cluster' + ZH_UI found")

# 2) Simulate the content.ts parse: count numbered lines vs milestones+edges for ALL files
print("\n=== Coverage check (milestones + edges-questions + edge-details vs ZH_UI numbered lines) ===")
content_root = r"D:\aiops-roadmap\content"
mismatch = 0
checked = 0
for z in sorted(os.listdir(content_root)):
    zp = os.path.join(content_root, z)
    if not os.path.isdir(zp) or z == "aiops":
        continue
    for f in sorted(os.listdir(zp)):
        if not f.endswith(".md"):
            continue
        t = open(os.path.join(zp, f), encoding="utf-8").read()
        if "ZH_UI" not in t:
            continue
        checked += 1
        fm = t.split("---")[1]
        n_ms = len(re.findall(r"^\s*-\s+", fm.split("milestones:")[1].split("edges:")[0], re.M)) if "milestones:" in fm else 0
        n_edges = len(re.findall(r"- id:", fm.split("edges:")[1])) if "edges:" in fm else 0
        n_details = len(re.findall(r"detail:", fm.split("edges:")[1])) if "edges:" in fm else 0
        expected = n_ms + n_edges + n_details
        idx = t.find("<!-- ZH_UI -->")
        ui_text = t[idx + len("<!-- ZH_UI -->"):]
        n_ui = len(re.findall(r"^\s*\d+\s*[.、)．:：]", ui_text, re.M))
        if n_ui != expected:
            mismatch += 1
            print(f"  MISMATCH {z}/{f}: expected {expected} (ms={n_ms} edges={n_edges} details={n_details}) got {n_ui}")
print(f"checked {checked} files with ZH_UI, mismatches: {mismatch}")
