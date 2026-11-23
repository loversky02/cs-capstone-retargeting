# Dữ liệu và mức tái lập

| Hướng | Dữ liệu và công cụ cần có | Bằng chứng hiện có |
|---|---|---|
| IK phẳng 2R và hiệu chỉnh đoạn | Python 3.10+, quỹ đạo tổng hợp sinh trong code, đơn vị mét/radian | Chạy offline, có kiểm thử và nhật ký mẫu |
| Panda hoặc UR5e | URDF/Xacro đúng biến thể và commit, chuỗi pose 6D theo thời gian, khung tọa độ robot, offset object→TCP, giới hạn khớp, trình giải IK | Có nguồn code/mô hình tham khảo. Chưa tích hợp hoặc chạy hai robot trong repo |
| Pose từ video có ArUco | Video có marker, kích thước marker, intrinsics và distortion camera, phép biến đổi camera→robot, timestamp | Có tài liệu và code OpenCV tham khảo. Chưa chạy trên video trong repo |
| Pose markerless hoặc thao tác vật lý | Video/ground truth phù hợp và đánh giá riêng. Với robot thật cần kiểm tra va chạm, động lực học và an toàn phần cứng | Hướng mở rộng, chưa có kết quả |

Benchmark 2R giữ quỹ đạo tham chiếu cố định và cố ý cộng bias vào ba đoạn quan sát. Oracle thay dữ liệu quan sát bằng tham chiếu trong số đoạn được phép. IK dùng nhánh khuỷu dương nhất quán rồi giới hạn góc. Chỉ số vi phạm đo góc thô trước khi giới hạn để tránh che lỗi bằng clipping. Mọi frame đều tham gia RMSE. Hiệu chỉnh một đoạn có giá một đơn vị ngân sách, cách tính này chỉ dùng trong bài minh họa.

Với ngân sách 1, RMSE giảm từ 89,7 xuống 70,3 mm và số frame vi phạm giới hạn khớp thô giảm từ 4 xuống 0. Số frame có mục tiêu nằm ngoài tầm với hình học vẫn là 4. Hai cột đo hai loại lỗi khác nhau.
