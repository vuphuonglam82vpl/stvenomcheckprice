import requests
import json
import time
import datetime
import tkinter as tk
import winsound  # Dành cho Windows
import threading  # Để chạy âm thanh và API trong luồng riêng

# Biến kiểm soát cảnh báo và âm thanh
is_playing = False
alert_open = False

# Hàm hiển thị cảnh báo với tiêu đề, thông báo và màu sắc tùy chọn
def show_alert(title, message, color, root):
    global is_playing, alert_open
    if alert_open:
        return  # Không mở lại nếu cảnh báo đã mở

    alert_open = True
    alert = tk.Toplevel(root)
    alert.title(title)
    alert.geometry("300x150")

    frame = tk.Frame(alert, bg=color)
    frame.pack(fill='both', expand=True)

    label = tk.Label(frame, text=message, bg=color, fg='white', font=("Arial", 12))
    label.pack(pady=20)

    button = tk.Button(frame, text="Đóng", command=lambda: close_alert(alert))
    button.pack(pady=10)

    # Khởi động luồng phát âm thanh không chặn giao diện chính
    threading.Thread(target=play_alert_sound, args=("alert.wav",)).start()

    alert.protocol("WM_DELETE_WINDOW", lambda: close_alert(alert))

def play_alert_sound(sound):
    global is_playing
    is_playing = True
    while is_playing:
        winsound.PlaySound(sound, winsound.SND_FILENAME)

def close_alert(alert=None):
    global is_playing, alert_open
    is_playing = False
    alert_open = False
    if alert:
        alert.destroy()

def check_price(root):
    global alert_open
    x = '{"ohlcvKind":"Price","timeframe":"D1","poolAddress":"0:594bae5c976f0d2e6f6386b390870b3f9a46e6c7829cdf122dcd7f1da8ab7cb1","from":0,"to":0}'
    data = json.loads(x)

    while True:
        now = datetime.datetime.utcnow()
        now_utc7 = now + datetime.timedelta(hours=7)
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(hours=7)

        today_midnight_ms = int(today_midnight.timestamp() * 1000)
        now_timestamp_ms = int(now_utc7.timestamp() * 1000)

        data["from"] = today_midnight_ms
        data["to"] = now_timestamp_ms

        try:
            r = requests.post('https://api.web3.world/v2/pools/ohlcv', json=data, timeout=10)
            r.raise_for_status()
            response_json = r.json()

            if response_json:
                first_item = response_json[0]
                close_price = float(first_item["close"])

                # Định dạng in ra close_price với màu sắc tùy thuộc vào giá trị của nó
                if close_price > 1:
                    print(f"{now_utc7.strftime('%Y-%m-%d %H:%M:%S')}, {GREEN}{close_price:.6f}{RESET}")
                else:
                    print(f"{now_utc7.strftime('%Y-%m-%d %H:%M:%S')}, {RED}{close_price:.6f}{RESET}")

                # Kiểm tra giá trị để hiển thị thông báo
                if close_price > 1.03 and not alert_open:
                    root.after(0, show_alert, "Cảnh báo", "Bán", "red", root)
                elif close_price < 0.97 and not alert_open:
                    root.after(0, show_alert, "Cảnh báo", "Mua", "green", root)
            else:
                print("Response trống hoặc không có dữ liệu")

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi kết nối: {e}")
            root.after(0, close_alert)

        except ValueError:
            print("Response không phải là JSON hoặc không hợp lệ:")
            print(r.text)

        time.sleep(5)

# Khởi tạo Tkinter và bắt đầu chương trình
root = tk.Tk()
root.withdraw()  # Ẩn cửa sổ chính
threading.Thread(target=check_price, args=(root,), daemon=True).start()
root.mainloop()
