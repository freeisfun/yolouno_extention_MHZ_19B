# yolobit_extension_mhz19b

Mục mở rộng cho **OhStem App (Yolo:Bit)** để đọc nồng độ CO2 từ cảm biến **MH-Z19B** (giao tiếp UART) bằng khối kéo thả.

Thư viện Python `mhz19b.py` được phát triển từ thư viện MicroPython gốc
[overflo23/MH-Z19_MicroPython](https://github.com/overflo23/MH-Z19_MicroPython)
(Florian "overflo" Bittner, giấy phép MIT). Khi đưa lên GitHub, hãy giữ nguyên phần ghi công ở đầu file `mhz19b.py`
và thêm file `LICENSE` (MIT) của tác giả gốc.

## Cách nạp vào OhStem App

1. Tạo repository GitHub (công khai), ví dụ `yolobit_extension_mhz19b`, rồi tải **toàn bộ** các file trong thư mục này lên (nhánh `main`).
2. Mở OhStem App → chọn Yolo:Bit → Lập trình → **MỞ RỘNG**.
3. Dán đường dẫn vào ô tìm kiếm thư viện rồi nhấn kính lúp:
   `https://github.com/<tên-github-của-bạn>/yolobit_extension_mhz19b.git`
4. Nhấn vào biểu tượng **MH-Z19B CO2** → OK. Nhóm khối **MH-Z19B** sẽ xuất hiện.

## Đấu nối

| MH-Z19B | Yolo:Bit / mạch mở rộng |
|---|---|
| Vin | 5V |
| GND | GND |
| RX | chân **TX** chọn trong khối khởi tạo |
| TX | chân **RX** chọn trong khối khởi tạo |

Mặc định khối chọn TX = P14, RX = P15. Nếu số đo luôn là `-1`, hãy đổi chỗ TX và RX.

## Các khối lệnh

| Khối | Chức năng |
|---|---|
| khởi tạo cảm biến CO2 MH-Z19B TX … RX … | Khai báo chân UART. Đặt một lần ở đầu chương trình. |
| nồng độ CO2 MH-Z19B (ppm) | Giá trị CO2. Trả về `-1` nếu cảm biến không phản hồi. |
| nhiệt độ cảm biến MH-Z19B (°C) | Nhiệt độ tham khảo (kém chính xác). Trả về `-99` nếu lỗi. |
| MH-Z19B đã làm nóng xong (3 phút) | `đúng` sau 3 phút kể từ lúc khởi tạo. |
| hiệu chuẩn điểm 0 (400 ppm) | Đặt cảm biến ngoài trời ~20 phút rồi chạy **một lần**. |
| bật/tắt tự hiệu chuẩn (ABC) | Bật/tắt tự hiệu chuẩn mỗi 24 giờ. Nên tắt khi đặt trong phòng kín. |
| đặt dải đo MH-Z19B là 2000/5000 ppm | Chọn dải đo tối đa. |

Cảm biến cần khoảng **3 phút** làm nóng sau khi cấp nguồn, số đo trước đó chưa đáng tin.
Thư viện giữ kết quả trong 1 giây, nên đọc CO2 và nhiệt độ trong cùng một vòng lặp chỉ gửi một lệnh xuống cảm biến.

## Chương trình mẫu (tương đương khối)

```python
from yolobit import *
from mhz19b import *
import time

mhz19b_init(pin14, pin15)

while True:
    co2 = mhz19b_co2()
    if co2 == -1:
        print("Không đọc được MH-Z19B")
    else:
        print("CO2:", co2, "ppm")
    time.sleep_ms(2000)
```

## Dùng trực tiếp thư viện Python (tương thích thư viện gốc)

```python
from mhz19b import MHZ19B          # hoặc: from mhz19b import mhz19  (tên của thư viện gốc)
sensor = MHZ19B(1, tx=pin14, rx=pin15)
if sensor.get_data():              # giống thư viện gốc, trả về 1 nếu đọc được
    print(sensor.ppm, sensor.temp, sensor.co2status)
```

## Khác biệt so với thư viện gốc

- Chọn được chân TX/RX (thư viện gốc dùng chân UART mặc định, trên ESP32 là chân nối flash nên không dùng được trên Yolo:Bit).
- Sửa lỗi checksum khi tổng byte chia hết cho 256 (bản gốc cho ra 256 thay vì 0).
- Xóa dữ liệu thừa trong bộ đệm trước mỗi lệnh, tìm đúng phần đầu `0xFF 0x86` và kiểm tra checksum của phản hồi.
- Thêm: hiệu chuẩn điểm 0, tự hiệu chuẩn ABC, đặt dải đo, hiệu chuẩn span, kiểm tra thời gian làm nóng.

## Cấu trúc thư mục

```
config.json      khai báo mục mở rộng
definition.js    định nghĩa khối + sinh mã Python
toolbox.xml      danh mục khối hiển thị trong OhStem App
mhz19b.py        thư viện MicroPython
poster.png       ảnh đại diện (thay bằng ảnh khác tùy ý)
```
