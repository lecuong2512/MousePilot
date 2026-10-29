# 🖱️ MousePilot — Bộ Điều Khiển & Tùy Biến Nút Chuột Windows

**MousePilot** là ứng dụng Desktop chuyên nghiệp (xây dựng bằng **PySide6 / Qt 6** theo chuẩn kiến trúc **Tier-1 Hardened Python Desktop** và phong cách giao diện **Apple HIG Dark Theme**), phụ trách nhận diện các chuột đang kết nối và tùy biến (remap) chức năng từng nút bấm.

---

## 📦 Bộ Cài Đặt Ứng Dụng Hệ Thống (Single-File Installer)

Ứng dụng đã được đóng gói thành file cài đặt độc lập duy nhất:
👉 **[`MousePilot_Setup.exe`](MousePilot_Setup.exe)** (dung lượng ~82 MB, tự động giải nén, không cần cài đặt Python).

### Khi chạy `MousePilot_Setup.exe`, ứng dụng sẽ tự động trở thành ỨNG DỤNG HỆ THỐNG:
1. **Cài đặt vào thư mục hệ thống Windows**:
   - Mặc định: `C:\Program Files\MousePilot` (hoặc `%LOCALAPPDATA%\Programs\MousePilot`).
2. **Tạo lối tắt thông minh (Shortcuts)**:
   - Tạo biểu tượng trên màn hình **Desktop**.
   - Tạo thư mục và lối tắt trong **Start Menu** (`Start Menu\Programs\MousePilot`).
3. **Đăng ký chính thức vào hệ điều hành Windows (Apps & Features)**:
   - Xuất hiện trong danh sách **Windows Settings -> Apps -> Installed Apps** và **Control Panel -> Programs and Features**.
   - Có đầy đủ thông tin: Tên ứng dụng, Nhà phát triển, Phiên bản 1.0.0, Icon chuột cao cấp và dung lượng.
4. **Tự động khởi động cùng Windows (Run in Tray)**:
   - Tự động chạy ngầm trong khay hệ thống (System Tray) khi bật máy tính, sẵn sàng can thiệp các nút chuột liên tục và ổn định.
5. **Bộ gỡ cài đặt hoàn chỉnh (`uninstall.exe`)**:
   - Bạn có thể gỡ bỏ sạch sẽ phần mềm bất cứ lúc nào từ Windows Settings hoặc Start Menu.

---

## ✨ Tính Năng Nổi Bật

1. **Nhận diện thiết bị phần cứng kết nối:**
   - Tự động quét và liệt kê thông tin chi tiết các chuột vật lý và touchpad đang kết nối (Tên thiết bị, VID, PID, Chuẩn kết nối USB / Wireless 2.4G / Bluetooth / Dell Precision Touchpad).
2. **Hỗ trợ tùy biến đầy đủ mọi nút chuột:**
   - **Nút Hông 1 (XButton 1 / Back)** — Phím hông dưới.
   - **Nút Hông 2 (XButton 2 / Forward)** — Phím hông trên.
   - **Nút Cuộn Giữa (Middle Click / Wheel Click)**.
   - **Chuột Phải (Right Click)**.
   - **Chuột Trái (Left Click)** — Có cơ chế cảnh báo an toàn.
   - **Cuộn Lên (Scroll Up) & Cuộn Xuống (Scroll Down)**.
   - **Nghiêng Bánh Xe Trái / Phải (Tilt Left / Right)**.
3. **Kho hành động phong phú để gán vào nút:**
   - ⌨️ **Phím tắt Windows & Văn phòng:** Copy (`Ctrl+C`), Paste (`Ctrl+V`), Cut (`Ctrl+X`), Undo (`Ctrl+Z`), Redo (`Ctrl+Y`), Save (`Ctrl+S`), Close Tab (`Ctrl+W`), Reopen Tab (`Ctrl+Shift+T`), Switch Window (`Alt+Tab`), Task View (`Win+Tab`), Desktop (`Win+D`), Snipping Tool (`Win+Shift+S`), Lock PC (`Win+L`)...
   - ⌨️ **Tổ hợp phím tự do (Custom Key Recorder):** Bấm bất kỳ tổ hợp phím nào trên bàn phím (như `Alt + X`) để gán trực tiếp.
   - 🖱️ **Hành động chuột:** Double click chuột trái, nhấp chuột giữa, nhấp chuột phải...
   - 🎵 **Điều khiển Âm lượng & Media:** Tăng/Giảm âm lượng, Mute tiếng, Phát/Dừng bài hát (Play/Pause), Chuyển bài kế tiếp/trước đó (Next/Prev).
   - 🚀 **Khởi chạy ứng dụng hoặc Website:** Mở nhanh file `.exe` hoặc link trang Web.
   - 📝 **Tự động gõ văn bản (Text Snippet):** Tự động điền email, mật khẩu hoặc đoạn tin nhắn mẫu.
   - ⚙️ **Chỉnh độ nhạy chuột (DPI / Windows Pointer Speed):** Điều chỉnh tốc độ con trỏ từ 1 đến 20.
   - 🚫 **Vô hiệu hóa (Disable):** Tắt hoàn toàn nút chuột nếu bạn hay bấm nhầm nút hông.
4. **Mô hình trực quan & Live Click Monitor:**
   - Hình vẽ chuột 2D tương tác: Bấm trực tiếp lên nút chuột trên màn hình để cấu hình.
   - Đèn phản hồi thời gian thực: Khi bạn bấm chuột thật bên ngoài, mô hình trên app sẽ sáng đèn xanh lá ngay lập tức kèm bảng nhật ký sự kiện và tọa độ `(X, Y)`.
5. **Cơ chế an toàn bọc thép (Fail-Safe & Anti-Lockout):**
   - 🛡️ **Phím tắt khẩn cấp (Emergency Panic Hotkey):** Bấm `Ctrl + Shift + Alt + M` ở bất kỳ đâu trên Windows để tạm dừng hoặc bật lại can thiệp chuột ngay tức thì.
   - 🛡️ **Bảo vệ chuột trái (Left Click Guard):** Cảnh báo xác nhận trước khi cho phép đổi nút chuột trái để chống vô tình mất click.
   - 🛡️ **Chuẩn 64-bit ABI**: Bỏ qua sự kiện di chuyển con trỏ chuột trong 1 micro-giây, chống giật lag và không bao giờ làm đứng hình chuột/touchpad.

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Cài đặt thành app hệ thống (Khuyên dùng)
- Nhấp đúp vào file **[`MousePilot_Setup.exe`](MousePilot_Setup.exe)**.
- Bấm **Tiếp tục** -> **Cài đặt**.
- Quá trình cài đặt sẽ tự động diễn ra và mở app ngay khi hoàn tất.

### 2. Chạy trực tiếp từ mã nguồn (Dành cho nhà phát triển)
- Nhấp đúp vào file **`run_silent.vbs`** hoặc **`run.bat`**.

### 3. Tự động đóng gói lại sau khi sửa code
- Nhấp đúp vào file **`build_installer.bat`** để tự động biên dịch lại mã nguồn và sinh ra file cài đặt `MousePilot_Setup.exe` mới nhất.
