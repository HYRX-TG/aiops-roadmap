import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

zh_q = "我知道我在使用托管集群"
next_dir = r"D:\aiops-roadmap\.next\server\app"
hits = []
for dp, _, fs in os.walk(next_dir):
    for f in fs:
        if not f.endswith(".html"):
            continue
        p = os.path.join(dp, f)
        txt = open(p, encoding="utf-8", errors="replace").read()
        if zh_q in txt:
            hits.append(p)
print("ZH question found in built HTML files:", len(hits))
for h in hits[:8]:
    print("  ", h)
