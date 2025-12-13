import asyncio
import time as time_check

from clients import Clients
from configs import match_config
from mongo.schemas import MatchAttackStats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

mongo_client = Clients.get_mongo_client()


async def convert_to_number(text_value: str) -> int | float | str:
    try:
        return int(text_value)
    except ValueError:
        try:
            return float(text_value)
        except ValueError:
            return text_value


async def get_stats_data(
    driver: webdriver.Chrome,
    wait: WebDriverWait[webdriver.Chrome],
    title: str,
    time: str,
):
    print(f"--- BẮT ĐẦU LẤY DỮ LIỆU THỐNG KÊ: {title} ---")
    start_time = time_check.time()
    # 1. Chờ "thông minh" (Đang hoạt động tốt, giữ nguyên)
    loading_selector = ".Opta-Loading-Visible"
    print(f"Đang chờ trình tải '{loading_selector}' biến mất (chờ tối đa 10s)...")
    try:
        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, loading_selector))
        )
        print("Trình tải đã biến mất. Dữ liệu đã được làm mới.")
    except Exception:
        print(
            f"Không tìm thấy trình tải '{loading_selector}' hoặc đã time out. Vẫn tiếp tục cào..."
        )
        # Dự phòng nếu không có trình tải
        await asyncio.sleep(1)  # Giảm thời gian chờ dự phòng

    print("Bắt đầu trích xuất dữ liệu...")

    stat_rows = driver.find_elements(
        By.CSS_SELECTOR, f"[class^='Opta-{title.lower()}_']"
    )
    print(f"Tìm thấy {len(stat_rows)} mục thống kê (hàng) của bảng '{title}'.")
    stats_data_dict = {}

    # 2. SỬA LỖI CỐT LÕI: Thay đổi bộ chọn (selector)
    for row in stat_rows:
        full_class = ""
        try:
            full_class = row.get_attribute("class")
            stat_name = full_class.split("_", 1)[1]

            # --- THAY ĐỔI LOGIC CÀO DỮ LIỆU ---
            # Lấy text từ <td> bên trái (Home)
            val1_str = row.find_element(
                By.CSS_SELECTOR, "td.Opta-Outer:first-of-type"
            ).text
            # Lấy text từ <td> bên phải (Away)
            val2_str = row.find_element(
                By.CSS_SELECTOR, "td.Opta-Outer:last-of-type"
            ).text
            # --- KẾT THÚC THAY ĐỔI ---

            val1 = await convert_to_number(val1_str)
            val2 = await convert_to_number(val2_str)
            stats_data_dict[stat_name] = (val1, val2)
        except Exception as e:
            print(f"    LỖI NHỎ: Không thể trích xuất hàng '{full_class}'. Lý do: {e}")
            pass

    print(
        f"Dữ liệu thống kê của bảng '{title}' tại thời điểm '{time}': {stats_data_dict}"
    )

    try:
        attack_stats_record = MatchAttackStats(
            time_in_match=time,
            goals=(stats_data_dict["goals"][0], stats_data_dict["goals"][1]),
            shots=(stats_data_dict["shots"][0], stats_data_dict["shots"][1]),
            shots_on_target=(
                stats_data_dict["shots_on_target"][0],
                stats_data_dict["shots_on_target"][1],
            ),
            shots_blocked=(
                stats_data_dict["shots_blocked"][0],
                stats_data_dict["shots_blocked"][1],
            ),
            shots_headed=(
                stats_data_dict["shots_headed"][0],
                stats_data_dict["shots_headed"][1],
            ),
            shots_outside_box=(
                stats_data_dict["shots_outside_box"][0],
                stats_data_dict["shots_outside_box"][1],
            ),
            shots_inside_box=(
                stats_data_dict["shots_inside_box"][0],
                stats_data_dict["shots_inside_box"][1],
            ),
            shots_accuracy=(
                stats_data_dict["shots_accuracy"][0],
                stats_data_dict["shots_accuracy"][1],
            ),
            key_passes=(
                stats_data_dict["key_passes"][0],
                stats_data_dict["key_passes"][1],
            ),
            shots_accuracy_excluding_blocked_shots=(
                stats_data_dict["shots_accuracy_excluding_blocked_shots"][0],
                stats_data_dict["shots_accuracy_excluding_blocked_shots"][1],
            ),
        )
        await attack_stats_record.insert()
        print(f"Đã lưu MatchAttackStats cho thời điểm '{time}' vào MongoDB.")
        end_time = time_check.time()
        print("--- KẾT THÚC LẤY DỮ LIỆU THỐNG KÊ ---")
        print(f"Thời gian lấy dữ liệu: {end_time - start_time:.2f} giây.\n")
    except Exception as e:
        print(f"LỖI khi lưu MatchAttackStats cho thời điểm '{time}': {e}")

    return stats_data_dict


async def hold_and_slowly_drag_end(
    driver: webdriver.Chrome,
    wait: WebDriverWait[webdriver.Chrome],
    title: str,
    pixel_per_step: int = -1,
    delay_per_step: float = 0.5,
):
    match_stats_data = []
    try:
        # 1. Định nghĩa các selector (như cũ)
        end_selector = ".Opta-Dragger.Opta-Dragger-end"
        start_selector = ".Opta-Dragger.Opta-Dragger-start"
        end_text_selector = ".Opta-TimeBox.Opta-end text"

        # 2. Tìm phần tử START (chỉ cần lấy 1 lần)
        start_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, start_selector))
        )
        target_x = start_element.location["x"]
        print(f"THÀNH CÔNG! Đã tìm thấy phần tử START (Mục tiêu X: {target_x}).")

        # 3. Lấy dữ liệu tại vị trí BAN ĐẦU (trước khi kéo)
        try:
            # Tìm nút END ban đầu
            end_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, end_selector))
            )
            current_x = end_element.location["x"]
            print(
                f"Vị trí X ban đầu (End): {current_x} | Vị trí X mục tiêu (Start): {target_x}"
            )

            current_time_text = driver.find_element(
                By.CSS_SELECTOR, end_text_selector
            ).text
            print(f"    -> Thời gian END ban đầu: {current_time_text}")

            # Lấy dữ liệu lần đầu
            match_stats_data.append(
                {
                    current_time_text: await get_stats_data(
                        driver=driver, wait=wait, title=title, time=current_time_text
                    )
                }
            )
        except Exception as e:
            print(f"    -> Không thể đọc text thời gian ban đầu: {e}")

        # 4. Vòng lặp WHILE mới
        loop_count = 0
        max_loops = 2000

        # Cập nhật current_x một lần nữa để đảm bảo vòng lặp chạy đúng
        current_x = driver.find_element(By.CSS_SELECTOR, end_selector).location["x"]

        while current_x > target_x and loop_count < max_loops:
            loop_count += 1
            print(
                f"\n  Bước kéo {loop_count} (current_x: {current_x}, target_x: {target_x}):"
            )

            # --- PHẦN SỬA LỖI QUAN TRỌNG ---
            try:
                # 5. TÌM LẠI nút END ở mỗi vòng lặp
                # (Vì sau khi thả chuột, trang web có thể render lại phần tử)
                end_element_to_drag = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, end_selector))
                )

                # 6. Thực hiện một hành động KÉO-THẢ HOÀN CHỈNH
                print(
                    f"    -> Đang thực hiện: click-hold -> move({pixel_per_step}px) -> release..."
                )
                actions = ActionChains(driver)
                actions.click_and_hold(end_element_to_drag)
                actions.move_by_offset(pixel_per_step, 0)
                actions.release()
                actions.perform()
                print(f"    -> Đã kéo và thả {pixel_per_step}px.")

                # 7. Chờ (cho JS xử lý sự kiện 'release' và gọi API)
                await asyncio.sleep(delay_per_step)

                # 8. Cập nhật VỊ TRÍ X MỚI
                current_x = driver.find_element(By.CSS_SELECTOR, end_selector).location[
                    "x"
                ]

                # 9. Lấy dữ liệu MỚI
                current_time_text = driver.find_element(
                    By.CSS_SELECTOR, end_text_selector
                ).text
                print(
                    f"    -> Thời gian END hiện tại: {current_time_text} (X: {current_x})"
                )
                match_stats_data.append(
                    {
                        current_time_text: await get_stats_data(
                            driver=driver,
                            wait=wait,
                            title=title,
                            time=current_time_text,
                        )
                    }
                )

            except Exception as e:
                print(f"    -> LỖI trong vòng lặp kéo: {e}")
                print("    -> Bỏ qua bước này và thử lại.")
                # Thêm một chút thời gian chờ nếu có lỗi
                await asyncio.sleep(1)
            # --- KẾT THÚC PHẦN SỬA LỖI ---

        # 10. Thả chuột (Dù đã release, gọi lại 1 lần nữa cho chắc)
        ActionChains(driver).release().perform()
        print("\nĐã thả chuột (lần cuối). Hoàn thành kéo chậm.")

        if loop_count >= max_loops:
            print("CẢNH BÁO: Đã đạt số vòng lặp tối đa. Buộc dừng.")
        else:
            print(f"Đã kéo đến vị trí mong muốn. (X cuối cùng: {current_x})")

        print("--- KẾT THÚC HÀM: ham_keo_thanh_end ---\n")

    except Exception as e:
        print(f"LỖI trong hàm ham_keo_thanh_end: {e}")
        raise
    finally:
        # (Phần ghi file JSON của bạn được giữ nguyên)
        print(
            f"Đang lưu tất cả dữ liệu thống kê trận đấu vào 'match_stats_data_{title}.json'..."
        )
        # with open(f"match_stats_data_{title}.json", "w", encoding="utf-8") as f:
        #     json.dump(match_stats_data, f, ensure_ascii=False, indent=4)
        print("Đã lưu dữ liệu thành công.")


async def main():
    # 1. Thiết lập trình duyệt
    options = Options()
    # options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    print("Đang khởi động trình duyệt Chrome (chế độ toàn màn hình)...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("Đã khởi động thành công.")

    url = match_config.url

    await mongo_client.initialize()

    try:
        # 2. Mở trang web
        print(f"Đang truy cập trang web: {url}")
        driver.get(url)

        # 3. Khởi tạo WebDriverWait
        timeout = 30
        wait = WebDriverWait(driver, timeout)

        try:
            print("\n--- BẮT ĐẦU: Click tab 'Attack' ---")
            # Chờ cho đến khi tab có thể click được
            tab = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Attack")))

            # Click vào tab
            tab.click()

            # In ra xác nhận
            print(f"Đã click vào tab: '{tab.text}'")

            # Chờ 1 giây để ổn định (nếu có JS)
            time_check.sleep(1)

        except Exception as e:
            print(f"LỖI: Không thể click vào tab 'Attack'. {e}")
            raise  # Dừng script nếu không click được
        print("--- KẾT THÚC: Click tab 'Attack' ---\n")
        # --- KẾT THÚC BƯỚC MỚI ---

        await hold_and_slowly_drag_end(driver=driver, wait=wait, title="Attack")

        print("--- KẾT THÚC HÀM: main ---\n")
    except Exception as e:
        print(f"LỖI trong hàm main: {e}")
    finally:
        driver.quit()
        print("Đã đóng trình duyệt.")


if __name__ == "__main__":
    asyncio.run(main())
    print("Trích xuất dữ liệu hoàn tất.")
