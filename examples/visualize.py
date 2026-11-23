"""Write a self-contained, offline HTML demo of the synthetic 2R benchmark.

The page animates the arm for every correction budget, overlays the reference,
corrupted target and achieved TCP paths, and plots RMSE against budget.
It uses only the standard library and needs no network when opened.
"""

import argparse
import json
from pathlib import Path

try:
    from examples.retarget import LINKS, LIMITS, SEGMENTS, simulate
except ImportError:  # executed as a script from the examples/ directory
    from retarget import LINKS, LIMITS, SEGMENTS, simulate

TEMPLATE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<title>Retargeting 2R · demo tương tác</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
 main{max-width:1100px;margin:auto;padding:20px}
 h1{font-size:22px;margin:0 0 4px} p.note{color:#94a3b8;font-size:13px;margin:4px 0 16px}
 .grid{display:grid;grid-template-columns:1.4fr 1fr;gap:16px}
 .card{background:#1e293b;border-radius:12px;padding:14px}
 svg{width:100%;height:auto;background:#0b1220;border-radius:8px}
 label{font-size:13px;color:#cbd5e1} input[type=range]{width:100%}
 table{width:100%;font-size:13px;border-collapse:collapse} td{padding:4px 2px;border-bottom:1px solid #334155}
 td.v{text-align:right;font-variant-numeric:tabular-nums}
 .legend span{display:inline-block;margin-right:12px;font-size:12px}
 .sw{display:inline-block;width:12px;height:3px;margin-right:4px;vertical-align:middle}
 button{background:#38bdf8;border:0;border-radius:6px;padding:6px 12px;font-weight:600;cursor:pointer}
 .warn{color:#fbbf24}
</style></head><body><main>
<h1>Retargeting tay máy phẳng 2R</h1>
<p class="note">Benchmark tổng hợp. Hiệu chỉnh dùng oracle biết bias đã cấy vào, nên kết quả chỉ mô tả benchmark này,
không đo lợi ích với người dùng hay robot thật. Hướng TCP nằm ngoài mô hình.</p>
<div class="grid">
 <div class="card">
  <svg id="scene" viewBox="-0.15 -0.75 1.05 1.3"></svg>
  <div class="legend">
   <span><i class="sw" style="background:#22c55e"></i>tham chiếu</span>
   <span><i class="sw" style="background:#f43f5e"></i>mục tiêu quan sát</span>
   <span><i class="sw" style="background:#38bdf8"></i>TCP đạt được</span>
   <span><i class="sw" style="background:#fbbf24"></i>đoạn đã sửa</span>
  </div>
  <label>Frame <b id="fl">0</b></label><input id="frame" type="range" min="0" value="0">
  <button id="play">▶ Chạy</button>
 </div>
 <div class="card">
  <label>Ngân sách hiệu chỉnh: <b id="bl">0</b> đoạn</label>
  <input id="budget" type="range" min="0" value="0">
  <table id="metrics"></table>
  <p class="note" id="framestate"></p>
  <svg id="chart" viewBox="0 0 300 160"></svg>
  <p class="note">RMSE vị trí (mm) theo ngân sách. Câu hỏi mở cho nhóm: thay oracle bằng một tín hiệu
  không biết đáp án (ví dụ độ bất định quan sát) thì đường này còn dốc như vậy không?</p>
 </div>
</div>
</main>
<script>
const DATA = __DATA__;
const $ = id => document.getElementById(id);
const ns = "http://www.w3.org/2000/svg";
const el = (tag, attrs) => { const e = document.createElementNS(ns, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };
const flip = p => [p[0], -p[1]];
const path = pts => pts.map((p, i) => (i ? "L" : "M") + flip(p).join(",")).join(" ");
let budget = 0, frame = 0, timer = null;
const n = DATA.runs[0].frames.length;
$("frame").max = n - 1; $("budget").max = DATA.runs.length - 1;

function drawScene() {
  const run = DATA.runs[budget], s = $("scene"); s.innerHTML = "";
  const reach = DATA.links[0] + DATA.links[1];
  s.append(el("circle", {cx: 0, cy: 0, r: reach, fill: "none", stroke: "#334155", "stroke-width": 0.004, "stroke-dasharray": "0.015"}));
  for (const [a, b] of run.result.corrected_frame_ranges_half_open)
    s.append(el("path", {d: path(run.frames.slice(a, b).map(f => f.reference)), stroke: "#fbbf24",
      "stroke-width": 0.03, fill: "none", opacity: 0.35}));
  const line = (key, color, dash) => s.append(el("path", {d: path(run.frames.map(f => f[key])),
    stroke: color, "stroke-width": 0.006, fill: "none", "stroke-dasharray": dash || ""}));
  line("reference", "#22c55e"); line("target", "#f43f5e", "0.012"); line("achieved", "#38bdf8");
  const f = run.frames[frame], [q1, q2] = f.joints, [l1, l2] = DATA.links;
  const elbow = [l1 * Math.cos(q1), l1 * Math.sin(q1)];
  s.append(el("polyline", {points: [[0, 0], elbow, f.achieved].map(p => flip(p).join(",")).join(" "),
    stroke: "#e2e8f0", "stroke-width": 0.02, fill: "none", "stroke-linecap": "round"}));
  for (const p of [[0, 0], elbow]) s.append(el("circle", {cx: flip(p)[0], cy: flip(p)[1], r: 0.018, fill: "#e2e8f0"}));
  s.append(el("circle", {cx: flip(f.target)[0], cy: flip(f.target)[1], r: 0.015, fill: "#f43f5e"}));
  s.append(el("circle", {cx: flip(f.achieved)[0], cy: flip(f.achieved)[1], r: 0.013, fill: "#38bdf8"}));
  const err = Math.hypot(f.achieved[0] - f.reference[0], f.achieved[1] - f.reference[1]) * 1000;
  $("framestate").innerHTML = `Frame ${frame}: sai số ${err.toFixed(1)} mm · q1=${q1.toFixed(2)} q2=${q2.toFixed(2)} rad`
    + (f.outside ? ' · <span class="warn">mục tiêu ngoài tầm với</span>' : "");
  $("fl").textContent = frame;
}
function drawMetrics() {
  const r = DATA.runs[budget].result;
  $("bl").textContent = budget;
  $("metrics").innerHTML = [["RMSE vị trí", (r.position_rmse_m * 1000).toFixed(1) + " mm"],
    ["Frame vi phạm giới hạn khớp (góc thô)", r.joint_limit_violation_frames],
    ["Frame mục tiêu ngoài tầm với", r.geometrically_unreachable_target_frames],
    ["Đoạn đã dùng", r.used_segments]].map(([k, v]) => `<tr><td>${k}</td><td class="v">${v}</td></tr>`).join("");
  const c = $("chart"); c.innerHTML = "";
  const vals = DATA.runs.map(x => x.result.position_rmse_m * 1000), max = Math.max(...vals) || 1;
  const xy = (v, i) => [30 + i * 250 / (vals.length - 1), 140 - v / max * 120];
  c.append(el("path", {d: vals.map((v, i) => (i ? "L" : "M") + xy(v, i).join(",")).join(" "),
    stroke: "#38bdf8", "stroke-width": 2, fill: "none"}));
  vals.forEach((v, i) => { const [x, y] = xy(v, i);
    c.append(el("circle", {cx: x, cy: y, r: i === budget ? 6 : 4, fill: i === budget ? "#fbbf24" : "#38bdf8"}));
    const t = el("text", {x, y: y - 9, fill: "#cbd5e1", "font-size": 10, "text-anchor": "middle"});
    t.textContent = v.toFixed(1); c.append(t);
    const b = el("text", {x, y: 155, fill: "#64748b", "font-size": 10, "text-anchor": "middle"});
    b.textContent = "B=" + i; c.append(b); });
}
$("budget").oninput = e => { budget = +e.target.value; drawMetrics(); drawScene(); };
$("frame").oninput = e => { frame = +e.target.value; drawScene(); };
$("play").onclick = () => {
  if (timer) { clearInterval(timer); timer = null; $("play").textContent = "▶ Chạy"; return; }
  $("play").textContent = "⏸ Dừng";
  timer = setInterval(() => { frame = (frame + 1) % n; $("frame").value = frame; drawScene(); }, 120);
};
drawMetrics(); drawScene();
</script></body></html>
"""


def build_payload():
    return {
        "links": LINKS,
        "limits": LIMITS,
        "segments": SEGMENTS,
        "runs": [simulate(budget) for budget in range(len(SEGMENTS) + 1)],
    }


def render(payload):
    return TEMPLATE.replace("__DATA__", json.dumps(payload, separators=(",", ":")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("demo.html"))
    args = parser.parse_args()
    args.out.write_text(render(build_payload()), encoding="utf-8")
    print(f"wrote {args.out} — open it in any browser")


if __name__ == "__main__":
    main()
