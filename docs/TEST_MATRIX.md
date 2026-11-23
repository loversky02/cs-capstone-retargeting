# Kiểm chứng

- Python unittest: IK thuận/nghịch, mục tiêu ngoài tầm, giới hạn ngân sách và đường cong sai số tổng hợp.
- Demo HTML: nhúng đủ mọi ngân sách, chỉ số trùng CLI, không tải tài nguyên mạng.
- Chạy CLI với ngân sách 0 và 1. JSON của --journal phải trùng với bản ghi kèm theo.
- Kiểm tra liên kết Markdown nội bộ và chạy lại từ ZIP giải nén.
- Demo MuJoCo (`tests/test_sim.py`, tự bỏ qua khi chưa cài `requirements-sim.txt`): gắp đúng pose thì thành công,
  lệch 35 mm thì thất bại; lấy mẫu episode tất định theo seed; AUROC ở hai cực; IK UR5e đạt trong tầm với, vượt tầm thì sai số lớn.
- Chưa kiểm chứng: người vận hành thật, robot thật, gripper và vật lý tiếp xúc trên UR5e.

