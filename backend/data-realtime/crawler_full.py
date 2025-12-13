import asyncio
import os
import time
from typing import Any, AsyncGenerator, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from clients import Clients
from configs import match_config
from momentum.calculate import MomentumUsedStats, TeamMomentumStats
from mongo.schemas import (
    MatchAttackStats,
    MatchDefenceStats,
    MatchDisciplineStats,
    MatchDistributionStats,
    MatchGeneralStats,
)

mongo_client = Clients.get_mongo_client()


def make_driver() -> webdriver.Chrome:
    options = Options()
    # Headless mới + tối ưu cho Docker
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # tránh shm nhỏ
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--disable-accelerated-2d-canvas")
    options.add_argument("--disable-features=Translate,BackForwardCache")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--single-process")

    # Chỉ ra đúng binary Chromium trong container
    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    options.binary_location = chrome_bin

    # Dùng chromedriver đã cài sẵn
    service = Service(os.getenv("CHROMEDRIVER", "/usr/bin/chromedriver"))

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def _to_num(x: str):
    """Chuyển text số thành int hoặc float, hoặc 0 nếu rỗng."""
    try:
        return int(x)
    except Exception:
        try:
            return float(x)
        except Exception:
            return 0


def _extract_tab_stats(driver: webdriver.Chrome, tab_name: str) -> Dict[str, Any]:
    """Đọc dữ liệu từng tab (Attack, Defence, Discipline, v.v.)."""
    rows = driver.find_elements(By.CSS_SELECTOR, f"[class^='Opta-{tab_name.lower()}_']")
    stats = {}
    for row in rows:
        try:
            cls = row.get_attribute("class")
            key = cls.split("_", 1)[1]
            left = _to_num(
                row.find_element(By.CSS_SELECTOR, "td.Opta-Outer:first-of-type").text
            )
            right = _to_num(
                row.find_element(By.CSS_SELECTOR, "td.Opta-Outer:last-of-type").text
            )
            stats[key] = (left, right)
        except Exception:
            continue
    return stats


async def save_stats_to_mongo(time_text: str, stats_all: Dict[str, Any]):
    """Lưu dữ liệu của 5 tab vào MongoDB (chạy song song với xuất dữ liệu)."""
    try:
        attack = stats_all["Attack"]
        defence = stats_all["Defence"]
        discipline = stats_all["Discipline"]
        distribution = stats_all["Distribution"]
        general = stats_all["General"]

        # insert concurrent
        await asyncio.gather(
            MatchAttackStats(time_in_match=time_text, **attack).insert(),
            MatchDefenceStats(time_in_match=time_text, **defence).insert(),
            MatchDisciplineStats(time_in_match=time_text, **discipline).insert(),
            MatchDistributionStats(time_in_match=time_text, **distribution).insert(),
            MatchGeneralStats(time_in_match=time_text, **general).insert(),
        )
        print(f"[Mongo] ✅ Inserted stats at {time_text}", flush=True)
    except Exception as e:
        print(f"[Mongo] ⚠️ Failed to insert {time_text}: {e}")


async def crawl_match_data_stream() -> AsyncGenerator[
    tuple[TeamMomentumStats, TeamMomentumStats], None
]:
    """Cào dữ liệu trận đấu theo thời gian thực và lưu vào MongoDB."""
    await mongo_client.initialize()

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    # driver = make_driver()
    driver.get(match_config.url)

    tabs = ["Attack", "Defence", "Discipline", "Distribution", "General"]
    wait = WebDriverWait(driver, 30)

    # click 1 lần để load tất cả tab
    for tab in tabs:
        el = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, tab)))
        el.click()
        await asyncio.sleep(0.8)

    print("[Crawler] ✅ Tabs loaded, starting realtime updates...", flush=True)

    try:
        while True:
            start_time = time.time()
            try:
                time_el = driver.find_element(
                    By.CSS_SELECTOR, ".Opta-TimeBox.Opta-end text"
                )
                time_text = time_el.text.strip()
                if not time_text:
                    await asyncio.sleep(2)
                    continue
            except Exception:
                await asyncio.sleep(2)
                continue

            # đọc dữ liệu 5 tab
            stats_all = {}
            for tab in tabs:
                stats_all[tab] = await asyncio.to_thread(
                    _extract_tab_stats, driver, tab
                )

            attack = stats_all["Attack"]
            defence = stats_all["Defence"]
            discipline = stats_all["Discipline"]
            distribution = stats_all["Distribution"]
            general = stats_all["General"]

            # gửi lưu Mongo (chạy nền, không block)
            asyncio.create_task(save_stats_to_mongo(time_text, stats_all))

            # tạo cấu trúc dữ liệu cho momentum
            home = MomentumUsedStats(
                goals=attack.get("goals", (0, 0))[0],
                shots_on_target=attack.get("shots_on_target", (0, 0))[0],
                shots_inside_box=attack.get("shots_inside_box", (0, 0))[0],
                shots_headed=attack.get("shots_headed", (0, 0))[0],
                shots_outside_box=attack.get("shots_outside_box", (0, 0))[0],
                shots_blocked=attack.get("shots_blocked", (0, 0))[0],
                key_passes=attack.get("key_passes", (0, 0))[0],
                through_balls=distribution.get("through_balls", (0, 0))[0],
                penalty_area_entries=distribution.get("penalty_area_entries", (0, 0))[
                    0
                ],
                open_play_crosses=distribution.get("open_play_crosses", (0, 0))[0],
                final_thirds_entries=distribution.get("final_thirds_entries", (0, 0))[
                    0
                ],
                dribbles_success=general.get("dribbles_success", (0, 0))[0],
                corners_won=general.get("corners_won", (0, 0))[0],
                possession_lost_defensive=general.get(
                    "possession_lost_defensive", (0, 0)
                )[0],
                possession_lost_midfield=general.get(
                    "possession_lost_midfield", (0, 0)
                )[0],
                offsides=general.get("offsides", (0, 0))[0],
                ball_recoveries_attacking=defence.get(
                    "ball_recoveries_attacking", (0, 0)
                )[0],
                interceptions=defence.get("interceptions", (0, 0))[0],
                tackles=defence.get("tackles", (0, 0))[0],
                ball_recoveries_midfield=defence.get(
                    "ball_recoveries_midfield", (0, 0)
                )[0],
                ball_recoveries_defensive=defence.get(
                    "ball_recoveries_defensive", (0, 0)
                )[0],
                clearances=defence.get("clearances", (0, 0))[0],
                fouls_conceded=discipline.get("fouls_conceded", (0, 0))[0],
                fouls_won=general.get("fouls_won", (0, 0))[0],
                cards_yellow=discipline.get("cards_yellow", (0, 0))[0],
                cards_red=discipline.get("cards_red", (0, 0))[0],
            )

            away = MomentumUsedStats(
                goals=attack.get("goals", (0, 0))[1],
                shots_on_target=attack.get("shots_on_target", (0, 0))[1],
                shots_inside_box=attack.get("shots_inside_box", (0, 0))[1],
                shots_headed=attack.get("shots_headed", (0, 0))[1],
                shots_outside_box=attack.get("shots_outside_box", (0, 0))[1],
                shots_blocked=attack.get("shots_blocked", (0, 0))[1],
                key_passes=attack.get("key_passes", (0, 0))[1],
                through_balls=distribution.get("through_balls", (0, 0))[1],
                penalty_area_entries=distribution.get("penalty_area_entries", (0, 0))[
                    1
                ],
                open_play_crosses=distribution.get("open_play_crosses", (0, 0))[1],
                final_thirds_entries=distribution.get("final_thirds_entries", (0, 0))[
                    1
                ],
                dribbles_success=general.get("dribbles_success", (0, 0))[1],
                corners_won=general.get("corners_won", (0, 0))[1],
                possession_lost_defensive=general.get(
                    "possession_lost_defensive", (0, 0)
                )[1],
                possession_lost_midfield=general.get(
                    "possession_lost_midfield", (0, 0)
                )[1],
                offsides=general.get("offsides", (0, 0))[1],
                ball_recoveries_attacking=defence.get(
                    "ball_recoveries_attacking", (0, 0)
                )[1],
                interceptions=defence.get("interceptions", (0, 0))[1],
                ball_recoveries_midfield=defence.get(
                    "ball_recoveries_midfield", (0, 0)
                )[1],
                ball_recoveries_defensive=defence.get(
                    "ball_recoveries_defensive", (0, 0)
                )[1],
                tackles=defence.get("tackles", (0, 0))[1],
                clearances=defence.get("clearances", (0, 0))[1],
                fouls_conceded=discipline.get("fouls_conceded", (0, 0))[1],
                fouls_won=general.get("fouls_won", (0, 0))[1],
                cards_yellow=discipline.get("cards_yellow", (0, 0))[1],
                cards_red=discipline.get("cards_red", (0, 0))[1],
            )

            yield (
                TeamMomentumStats(time_in_match=time_text, stats=home),
                TeamMomentumStats(time_in_match=time_text, stats=away),
            )

            elapsed = time.time() - start_time
            print(f"[Crawler] ⏱️ Cycle completed in {elapsed:.2f}s", flush=True)
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        print("[Crawler] Stream cancelled.")
    finally:
        driver.quit()
        print("[Crawler] Chrome driver closed.")
