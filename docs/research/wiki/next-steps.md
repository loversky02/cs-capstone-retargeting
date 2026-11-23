# Bậc thang mở rộng

Mỗi bậc là một hướng nhóm có thể tự chọn, không phải yêu cầu. Bậc sau cần nhiều phụ thuộc hơn bậc trước. Đối chiếu nguồn ngày 2026-11-23 trong [danh sách nguồn](../sources.md).

| Bậc | Câu hỏi khám phá | Công cụ gợi ý | Bằng chứng cần báo |
|---|---|---|---|
| 0. Benchmark 2R | Thay oracle bằng tín hiệu không biết đáp án (độ bất định, độ lệch vận tốc) thì chọn đoạn có còn tốt hơn chia đều? | Repo này, chỉ thư viện chuẩn | Nhiều seed/kịch bản, có cả ca không cải thiện |
| 1. Tay 6 bậc | IK số với giới hạn khớp và hướng TCP khác gì nghiệm giải tích 2R? | Modern Robotics, URDF Panda/UR5e | Sai số vị trí và hướng riêng, số frame vi phạm giới hạn |
| 2. Pose từ video có marker | Sai số hiệu chuẩn camera lan sang quỹ đạo robot bao nhiêu? | OpenCV ArUco | Intrinsics, kích thước marker, sai số tái chiếu |
| 3. Người sang humanoid | Retargeting tạo trượt chân, xuyên vật hay tư thế bất khả thi ở đâu? | GMR + MuJoCo, dữ liệu BVH/SMPL | Chỉ là động học trong mô phỏng, chưa phải robot bám được |
| 4. Dữ liệu học robot | Có thể đóng gói quỹ đạo và đoạn đã sửa thành dataset huấn luyện chính sách không? | LeRobotDataset v3.0, tutorial MuJoCo | Ghi rõ dữ liệu tổng hợp hay thu thật, ai/cái gì tạo nhãn |

Giữ ba ranh giới khi báo kết quả: hiệu chỉnh oracle không phải hiệu chỉnh của người; retarget động học không phải thao tác vật lý thành công; video có marker không phải trích xuất markerless.

## Gợi ý nối tiếp hai demo MuJoCo

| Hướng | Câu hỏi khám phá | Điểm xuất phát trong repo | Bằng chứng cần báo |
|---|---|---|---|
| TeleGuide | Độ bất định do chính policy/VLA đo được (entropy token hành động, độ phân tán khi lấy mẫu nhiều lần) có dự đoán thất bại tốt hơn heuristic độ phân tán phát hiện không? | `sim/teleguide.py`, thay `features` | AUROC và đường cong hỏi người trên cùng tập test, kể cả khi không cải thiện |
| TeleGuide | Ngưỡng hỏi người được chọn thế nào khi chi phí làm phiền người khác chi phí thất bại? | `ask_curve` | Đường chi phí theo ngưỡng; ghi rõ người là oracle mô phỏng |
| Retarget | Thay nhiễu Gaussian bằng nhiễu lấy từ phân phối hành động của robot nguồn (Panda) có giúp bước denoise kiểu DemoDiffusion? | `sim/retarget.py`, vùng vàng/đỏ trên bản đồ tầm với | Tỷ lệ thành công vật lý sau khi có gripper UR5e, nhiều seed; ghi rõ policy dùng để denoise |

