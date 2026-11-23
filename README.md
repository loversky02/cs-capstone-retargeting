# Capstone CS · Thử nghiệm robot retargeting

Bộ tài liệu để các nhóm CS tự khám phá độ khả thi của bài toán chuyển quỹ đạo từ dữ liệu quan sát sang robot. Nhóm tự chọn câu hỏi và phạm vi capstone.

## Chạy thử trong 5 phút

Cần Python 3.10 trở lên. Ví dụ chỉ dùng thư viện chuẩn, tự sinh dữ liệu và chạy offline.

```sh
python3 examples/retarget.py --budget 0
python3 examples/retarget.py --budget 1
python3 -m unittest discover -s tests -v
```

Mỗi lần chạy in một bản ghi JSON. So `position_rmse_m`, `joint_limit_violation_frames` và `used_segments` giữa hai lần chạy. `position_rmse_m` là thành phần vị trí của sai số pose. Hướng TCP nằm ngoài mô hình 2R này. Hiệu chỉnh dùng oracle tổng hợp nên kết quả chỉ mô tả benchmark, chưa đo lợi ích với người dùng hay robot thật.

## Demo tương tác

```sh
python3 examples/visualize.py --out demo.html
```

Mở `demo.html` bằng trình duyệt bất kỳ, không cần mạng. Kéo thanh ngân sách để xem RMSE thay đổi, bấm Chạy để xem tay 2R bám quỹ đạo. Đoạn vàng là đoạn oracle đã sửa, chấm đỏ là mục tiêu ngoài tầm với.

## Demo MuJoCo: TeleGuide và retarget Panda → UR5e

Hai demo 3D bám hai hướng nhóm đang theo. Cần cài thêm thư viện; lần chạy đầu tải mô hình Panda và UR5e từ
mujoco_menagerie (commit cố định) vào `.cache/`.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements-sim.txt
.venv/bin/python -m sim.teleguide     # ~30 s, 1200 episode, ghi outputs/teleguide/
.venv/bin/python -m sim.retarget      # ~5 s, ghi outputs/retarget/
.venv/bin/python -m sim.report        # gom thành outputs/index.html
```

Mở `outputs/index.html` qua một web server cục bộ (`python3 -m http.server -d outputs`) để xem video và biểu đồ.

- **TeleGuide.** Panda gắp hộp theo pose ước lượng từ 5 lần phát hiện có nhiễu. Trước khi gắp, một bộ dự đoán thất bại
  quyết định có dừng lại hỏi người hay không. So sánh ngẫu nhiên, heuristic độ phân tán và MLP numpy bằng AUROC cùng
  đường cong thành công theo tỷ lệ hỏi. Với cùng đặc trưng, MLP (AUROC 0.75) không hơn heuristic (0.74) có ý nghĩa.
  "Người" là oracle biết pose thật.
- **Retarget.** Quỹ đạo TCP của Panda được chuyển sang UR5e bằng IK từng frame, kèm sai số, số frame chạm giới hạn
  khớp, jerk và bản đồ tầm với trên toàn bàn. Đây chỉ là retarget động học, chưa có gripper hay vật lý tiếp xúc cho UR5e.

- [Bậc thang từ 2R lên humanoid và dữ liệu học robot](docs/research/wiki/next-steps.md)
- [Lộ trình đọc và code tham khảo](docs/research/wiki/index.md)
- [Đầu vào và mức tái lập của từng hướng](docs/research/wiki/reproducibility.md)
- [Nhật ký SIM và cách ghi lần thử mới](docs/research/wiki/sim.md)
