// 提取每个内容文件的 milestones + edges(question/detail)，供翻译脚本使用。
// 用 gray-matter 解析，保证与前端运行时的解析顺序完全一致。
// 输出: scripts/ui_strings.json = [{ path, milestones: [], edges: [{question, detail}] }]
import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";

const ROOT = path.resolve(new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const CONTENT = path.join(ROOT, "content");

const out = [];
for (const zone of fs.readdirSync(CONTENT, { withFileTypes: true })) {
  if (!zone.isDirectory() || zone.name === "aiops") continue;
  const zoneDir = path.join(CONTENT, zone.name);
  for (const f of fs.readdirSync(zoneDir)) {
    if (!f.endsWith(".md")) continue;
    const p = path.join(zoneDir, f);
    const raw = fs.readFileSync(p, "utf-8");
    const fm = matter(raw).data;
    out.push({
      path: p,
      milestones: Array.isArray(fm.milestones) ? fm.milestones : [],
      edges: (fm.edges?.to ?? []).map((e) => ({
        question: e.question ?? "",
        detail: e.detail ?? "",
      })),
    });
  }
}
fs.writeFileSync(path.join(ROOT, "scripts", "ui_strings.json"), JSON.stringify(out, null, 1), "utf-8");
console.log("extracted", out.length, "files");
