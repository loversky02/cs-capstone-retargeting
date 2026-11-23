# Nguồn

Đối chiếu 2026-11-23.

| Nguồn | Dùng cho |
|---|---|
| [Modern Robotics, chương 6](https://modernrobotics.northwestern.edu/chapters/chapter6/) và [code tác giả](https://github.com/NxRLab/ModernRobotics) | IK giải tích và số |
| [Franka Robotics robot descriptions](https://github.com/frankarobotics/franka_description) | Mô tả robot Franka, cần chọn đúng biến thể Panda |
| [Universal Robots ROS 2 Description](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description) | Mô tả UR5e, cấu hình và giới hạn khớp |
| [OpenCV ArUco](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html) | Ước lượng pose có marker và hiệu chuẩn camera |
| [Self-Improvement Memory](https://arxiv.org/abs/2611.18856) | Cấu trúc lưu nguyên nhân, dự đoán và quan sát |
| [DAIR wiki-builder, revision 0abffdc](https://github.com/dair-ai/dair-academy-plugins/tree/0abffdcb374644c77b2aabf02f694e15f85ebc16/plugins/wiki-builder) | Scaffold wiki và quy trình bảo trì |
| [GMR: General Motion Retargeting](https://github.com/YanjieZe/GMR) và [bài báo](https://arxiv.org/abs/2510.02252) | Retarget chuyển động người sang humanoid (có Unitree G1) trên CPU, xem trong MuJoCo; có đường từ video một camera qua GVHMR |
| [LeRobotDataset v3.0](https://huggingface.co/blog/lerobot-datasets-v3) và [tài liệu](https://huggingface.co/docs/lerobot/lerobot-dataset-v3) | Định dạng dữ liệu học robot: Parquet cho khớp/hành động, MP4 cho camera, metadata episode |
| [lerobot-mujoco-tutorial](https://github.com/jeongeun980906/lerobot-mujoco-tutorial) | Notebook thu demo bằng bàn phím trong MuJoCo rồi huấn luyện ACT |
| [mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie) | Mô hình Panda và UR5e dùng trong demo `sim/` |
| [DemoDiffusion](https://arxiv.org/abs/2506.20668) | Retarget động học rồi thêm nhiễu và denoise bằng diffusion policy đã huấn luyện |
| [Confidence calibration in VLA models](https://arxiv.org/abs/2507.17383) | Đo độ tin cậy của VLA có khớp tỷ lệ thành công không |
| [SAFE: multitask failure detection for VLA](https://arxiv.org/abs/2506.09937) | Dự đoán thất bại từ đặc trưng nội tại của VLA |
| [Failure prediction at runtime for generative policies](https://arxiv.org/abs/2510.09459) | Phát hiện thất bại sớm khi policy đang chạy |
| [When to Act, Ask, or Learn](https://arxiv.org/abs/2602.22474) | Khung quyết định tự làm, hỏi người hay học thêm |
