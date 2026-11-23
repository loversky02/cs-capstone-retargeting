"""Build outputs/index.html: one offline page with both MuJoCo demos, their videos and metrics.

Run after `python -m sim.teleguide` and `python -m sim.retarget`.
"""

import json
from pathlib import Path

PAGE = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<title>CS capstone · MuJoCo demos</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
 main{max-width:1150px;margin:auto;padding:24px}
 h1{margin:0 0 4px;font-size:26px} h2{font-size:20px;margin:28px 0 6px}
 .note{color:#94a3b8;font-size:13px;line-height:1.5}
 .grid{display:grid;grid-template-columns:1.25fr 1fr;gap:16px}
 .card{background:#1e293b;border-radius:12px;padding:14px}
 video{width:100%;border-radius:8px;background:#000}
 table{width:100%;border-collapse:collapse;font-size:13px} td,th{padding:5px;border-bottom:1px solid #334155;text-align:left}
 td.v{text-align:right;font-variant-numeric:tabular-nums}
 .warn{color:#fbbf24} svg{width:100%;height:auto}
 .pill{display:inline-block;background:#334155;border-radius:999px;padding:2px 10px;font-size:12px;margin-right:6px}
</style></head><body><main>
<h1>Hai demo MuJoCo cho hai hướng capstone</h1>
<p class="note"><span class="pill">Panda + UR5e · mujoco_menagerie</span><span class="pill">chỉ mô phỏng</span>
"Người" trong TeleGuide là oracle biết pose thật. Kết quả không đo lợi ích với người vận hành thật hay robot thật.</p>

<h2>1 · TeleGuide: dự đoán thất bại trước khi gắp, hỏi người khi rủi ro cao</h2>
<div class="grid">
 <div class="card"><video src="teleguide/highlights.mp4" controls autoplay muted loop playsinline></video>
 <p class="note">Ba episode test: tự làm thành công · rủi ro cao → dừng, hỏi người · rủi ro bị bỏ sót.
 Hộp xanh mờ là vị trí robot <i>tin</i>; hộp đỏ là vị trí thật.</p></div>
 <div class="card">
  <table id="tg"></table>
  <svg id="curve" viewBox="0 0 320 210"></svg>
  <p class="note">Tỷ lệ thành công khi robot hỏi người ở top-k% episode rủi ro nhất. Đường càng sát góc trên trái càng tốt.
  Phát hiện thật: MLP <b>không</b> vượt heuristic khi dùng cùng đặc trưng. Bước tiếp theo đáng thử là độ bất định
  của chính policy/VLA (xem next-steps).</p>
 </div>
</div>

<h2>2 · Cross-embodiment: retarget quỹ đạo Panda sang UR5e</h2>
<div class="grid">
 <div class="card"><video src="retarget/panda_to_ur5e.mp4" controls autoplay muted loop playsinline></video>
 <p class="note">Bước 1 của pipeline kiểu DemoDiffusion: retarget động học (IK theo từng frame). Chưa có gripper
 và vật lý tiếp xúc cho UR5e, nên đây không phải bằng chứng gắp thành công.</p></div>
 <div class="card">
  <table id="rt"></table>
  <svg id="heat" viewBox="0 0 320 250"></svg>
  <p class="note">Sai số TCP lớn nhất (mm) khi retarget tư thế gắp cho hộp đặt khắp bàn. Ô vàng/đỏ:
  UR5e không theo được, là chỗ cần bước "denoise/refine" thay cho copy động học thuần.</p>
 </div>
</div>
</main><script>
const TG = __TG__, RT = __RT__, ns = "http://www.w3.org/2000/svg";
const el = (t, a, txt) => { const e = document.createElementNS(ns, t); for (const k in a) e.setAttribute(k, a[k]);
  if (txt !== undefined) e.textContent = txt; return e; };
const row = (k, v) => `<tr><td>${k}</td><td class="v">${v}</td></tr>`;
const pct = x => (100 * x).toFixed(1) + "%";
document.getElementById("tg").innerHTML = row("Episode test", TG.test) + row("Robot tự làm", pct(TG.auto_success_rate_test))
 + row("Oracle-human làm hết", pct(TG.human_success_rate_test))
 + Object.entries(TG.failure_auroc).map(([k, v]) => row("AUROC dự đoán fail · " + k, v.toFixed(3))).join("");
const colors = {random: "#64748b", heuristic_spread: "#fbbf24", risk_net: "#38bdf8", oracle_hindsight: "#22c55e"};
const c = document.getElementById("curve"), lo = Math.min(...Object.values(TG.curves).flat()) - 0.02;
const X = r => 40 + r * 260, Y = s => 180 - (s - lo) / (1 - lo) * 165;
c.append(el("line", {x1: 40, y1: 180, x2: 300, y2: 180, stroke: "#475569"}));
c.append(el("text", {x: 170, y: 205, fill: "#94a3b8", "font-size": 10, "text-anchor": "middle"}, "tỷ lệ hỏi người"));
[lo, 1].forEach(s => c.append(el("text", {x: 34, y: Y(s) + 3, fill: "#94a3b8", "font-size": 9, "text-anchor": "end"}, pct(s))));
Object.entries(TG.curves).forEach(([k, ys], j) => {
  c.append(el("path", {d: ys.map((s, i) => (i ? "L" : "M") + X(TG.ask_rates[i]) + "," + Y(s)).join(""),
    stroke: colors[k], fill: "none", "stroke-width": 2}));
  c.append(el("text", {x: 200, y: 120 + j * 13, fill: colors[k], "font-size": 10}, k)); });
const v = RT.variants;
document.getElementById("rt").innerHTML = "<tr><th></th><th>pos+orient</th><th>chỉ pos</th></tr>" +
 [["Sai số TCP TB (mm)", "tcp_err_mean_mm", 2], ["Sai số TCP max (mm)", "tcp_err_max_mm", 2],
  ["Frame chạm giới hạn khớp", "frames_at_joint_limit", 0], ["Jerk khớp RMS (rad/s³)", "joint_jerk_rms_rad_s3", 1]]
 .map(([n, k, d]) => `<tr><td>${n}</td><td class="v">${v.position_and_orientation[k].toFixed(d)}</td><td class="v">${v.position_only[k].toFixed(d)}</td></tr>`).join("");
const h = document.getElementById("heat"), S = RT.reach_sweep, cw = 250 / S.ys.length, ch = 210 / S.xs.length;
S.max_err_mm.forEach((r, i) => r.forEach((e, j) => {
  const col = e < 5 ? "#16a34a" : e < 50 ? "#ca8a04" : "#dc2626";
  h.append(el("rect", {x: 50 + j * cw, y: 10 + i * ch, width: cw - 2, height: ch - 2, fill: col, rx: 3}));
  h.append(el("text", {x: 50 + j * cw + cw / 2 - 1, y: 10 + i * ch + ch / 2 + 3, fill: "#fff", "font-size": 9,
    "text-anchor": "middle"}, e < 1 ? "0" : e.toFixed(0))); }));
S.xs.forEach((x, i) => h.append(el("text", {x: 46, y: 10 + i * ch + ch / 2 + 3, fill: "#94a3b8", "font-size": 9, "text-anchor": "end"}, "x=" + x.toFixed(2))));
S.ys.forEach((y, j) => h.append(el("text", {x: 50 + j * cw + cw / 2, y: 238, fill: "#94a3b8", "font-size": 9, "text-anchor": "middle"}, y.toFixed(1))));
</script></body></html>
"""


def main(out=Path("outputs")):
    tg = json.loads((out / "teleguide" / "report.json").read_text())
    rt = json.loads((out / "retarget" / "report.json").read_text())
    page = PAGE.replace("__TG__", json.dumps(tg)).replace("__RT__", json.dumps(rt))
    (out / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote {out / 'index.html'}")


if __name__ == "__main__":
    main()
