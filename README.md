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

- [Lộ trình đọc và code tham khảo](docs/research/wiki/index.md)
- [Đầu vào và mức tái lập của từng hướng](docs/research/wiki/reproducibility.md)
- [Nhật ký SIM và cách ghi lần thử mới](docs/research/wiki/sim.md)
