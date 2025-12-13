import asyncio
import os
import re
import time
from typing import Any, AsyncGenerator, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from clients import Clients
from detect_halftime import MatchState
from momentum.calculate import MomentumUsedStats, TeamMomentumStats
from mongo.schemas import (
    MatchAttackStats,
    MatchDefenceStats,
    MatchDisciplineStats,
    MatchDistributionStats,
    MatchGeneralStats,
)

mongo_client = Clients.get_mongo_client()


# ============================================================
#  CHROME DRIVER
# ============================================================
def make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--hide-scrollbars")

    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    options.binary_location = chrome_bin
    service = Service(os.getenv("CHROMEDRIVER", "/usr/bin/chromedriver"))

    return webdriver.Chrome(service=service, options=options)


def _to_num(x: str) -> float | int:
    x = x.strip()
    if not x:
        return 0
    try:
        return int(x)
    except Exception:
        try:
            return float(x)
        except Exception:
            return 0


def _extract_first_number(td) -> float | int:
    """
    Lấy số từ 1 ô <td>:
    - ưu tiên innerText
    - fallback innerHTML
    - regex tìm số đầu tiên
    """
    text = td.get_attribute("innerText") or td.text or ""
    if not text.strip():
        text = td.get_attribute("innerHTML") or ""

    m = re.search(r"[-+]?\d*\.?\d+", text.replace(",", ""))
    if not m:
        return 0
    return _to_num(m.group(0))


# ============================================================
#  TAB INDEX
# ============================================================
TAB_INDEX: Dict[str, int] = {
    "General": 0,
    "Distribution": 1,
    "Attack": 2,
    "Defence": 3,
    "Discipline": 4,
}

TAB_FIELDS: Dict[str, list[str]] = {
    "Attack": [
        "goals",
        "shots",
        "shots_on_target",
        "shots_blocked",
        "shots_headed",
        "shots_outside_box",
        "shots_inside_box",
        "shots_accuracy_excluding_blocked_shots",
        "shots_accuracy",
        "key_passes",
    ],
    "Defence": [
        "interceptions",
        "tackles",
        "clearances",
        "ball_recoveries",
        "ball_recoveries_attacking",
        "ball_recoveries_midfield",
        "ball_recoveries_defensive",
    ],
    "Discipline": ["fouls_conceded", "cards_yellow", "cards_red"],
    "Distribution": [
        "passes",
        "passes_long",
        "passes_long_proportion",
        "passes_accuracy",
        "passes_opponents_half",
        "through_balls",
        "penalty_area_entries",
        "open_play_crosses",
        "final_thirds_entries",
        "crosses",
        "crosses_accuracy",
    ],
    "General": [
        "possession",
        "possession_lost_defensive",
        "possession_lost_midfield",
        "duels",
        "aerial_duels",
        "aerial_duels_accuracy",
        "dribbles_success",
        "fouls_won",
        "offsides",
        "corners_won",
    ],
}


# ============================================================
#  CLOCK READER
# ============================================================
def get_time_text(driver: webdriver.Chrome) -> str:
    # 1) Stoppage time
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".Opta-ClockContainer .Opta-Stoppage")
        txt = el.text.strip()
        if txt:
            return txt
    except Exception:
        pass

    # 2) Normal clock
    try:
        el = driver.find_element(
            By.CSS_SELECTOR, ".Opta-ClockContainer .Opta-Clock span"
        )
        txt = el.text.strip()
        if txt:
            return txt
    except Exception:
        pass

    # 3) HT / FT (abbr)
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".Opta-ClockContainer abbr")
        txt = el.text.strip()
        if txt:
            return txt
    except Exception:
        pass

    return ""


# ============================================================
#  CLICK TAB + PARSE DATA
# ============================================================
def _activate_and_extract_tab_stats(
    driver: webdriver.Chrome, tab_name: str
) -> Dict[str, Any]:
    stats: Dict[str, Any] = {}

    try:
        # 1) Click đúng tab trong nav (General / Distribution / ...)
        nav_ul = driver.find_element(By.CSS_SELECTOR, "div.Opta-Nav ul.Opta-Cf")
        nav_items = nav_ul.find_elements(By.TAG_NAME, "li")

        idx = TAB_INDEX[tab_name]
        if idx >= len(nav_items):
            print(f"[Crawler] ⚠️ Nav index out of range for {tab_name}")
            return stats

        nav_items[idx].click()
        time.sleep(0.3)  # cho JS render

        # 2) Tìm li.Opta-On trong Opta-TabbedContent (tab đang active)
        ul_tabs = driver.find_element(By.CSS_SELECTOR, "ul.Opta-TabbedContent")
        active_li = ul_tabs.find_element(By.CSS_SELECTOR, "li.Opta-On")

        tbody = active_li.find_element(By.CSS_SELECTOR, "table.Opta-Stats-Bars tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            cls = row.get_attribute("class") or ""
            if not cls.startswith("Opta-"):
                continue

            parts = cls.split("_", 1)
            key = parts[1] if len(parts) == 2 else cls.replace("Opta-", "")

            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 2:
                continue

            left = _extract_first_number(tds[0])
            right = _extract_first_number(tds[-1])

            stats[key] = (left, right)

        print(f"[SNAPSHOT] {tab_name}: {stats}")

        # cảnh báo nếu thiếu field quan trọng theo schema
        for f in TAB_FIELDS.get(tab_name, []):
            if f not in stats:
                print(f"[Crawler] ⚠️ Missing field in DOM for {tab_name}: {f}")

    except Exception as e:
        print(f"[Crawler] ❌ extract {tab_name}: {e}")

    return stats


# ============================================================
#  SAVE MONGO
# ============================================================
async def save_stats_to_mongo(time_text: str, stats_all: Dict[str, Any]):
    try:
        await asyncio.gather(
            MatchAttackStats(time_in_match=time_text, **stats_all["Attack"]).insert(),
            MatchDefenceStats(time_in_match=time_text, **stats_all["Defence"]).insert(),
            MatchDisciplineStats(
                time_in_match=time_text, **stats_all["Discipline"]
            ).insert(),
            MatchDistributionStats(
                time_in_match=time_text, **stats_all["Distribution"]
            ).insert(),
            MatchGeneralStats(time_in_match=time_text, **stats_all["General"]).insert(),
        )
        print(f"[Mongo] ✅ Insert OK at {time_text}")
    except Exception as e:
        print(f"[Mongo] ❌ Insert failed at {time_text}: {e}")


# ============================================================
#  MAIN STREAM
# ============================================================
async def crawl_match_data_stream(
    match_url: str,
    db_name: str,
) -> AsyncGenerator[tuple[TeamMomentumStats, TeamMomentumStats], None]:
    await mongo_client.initialize(db_name=db_name)

    driver = make_driver()
    driver.get(match_url)

    tabs = ["General", "Distribution", "Attack", "Defence", "Discipline"]
    print("[Crawler] ⚡ Start loop")
    state = MatchState()

    try:
        while True:
            cycle_start = time.time()

            time_text = get_time_text(driver)
            if not time_text:
                print("[Crawler] ⚠️ Cannot read time text")
                await asyncio.sleep(1)
                continue

            if time_text == "HT":
                time_text = "45:00"
            elif time_text == "FT":
                time_text = "90:00"

            print(f"\n=== CLOCK: {time_text} ===")

            # đọc từng tab bằng cách CLICK
            stats_all: Dict[str, Dict[str, Any]] = {
                tab: _activate_and_extract_tab_stats(driver, tab) for tab in tabs
            }

            # print snapshot gọn
            print("=========== SNAPSHOT ===========")
            for tab_name, data in stats_all.items():
                print(f"[{tab_name}]")
                for k, (h, a) in data.items():
                    print(f"  {k}: {h} – {a}")
            print("================================\n")

            await save_stats_to_mongo(time_text, stats_all)

            attack = stats_all["Attack"]
            defence = stats_all["Defence"]
            discipline = stats_all["Discipline"]
            distribution = stats_all["Distribution"]
            general = stats_all["General"]

            def build(idx: int) -> MomentumUsedStats:
                return MomentumUsedStats(
                    goals=attack.get("goals", (0, 0))[idx],
                    shots_on_target=attack.get("shots_on_target", (0, 0))[idx],
                    shots_inside_box=attack.get("shots_inside_box", (0, 0))[idx],
                    shots_headed=attack.get("shots_headed", (0, 0))[idx],
                    shots_outside_box=attack.get("shots_outside_box", (0, 0))[idx],
                    shots_blocked=attack.get("shots_blocked", (0, 0))[idx],
                    key_passes=attack.get("key_passes", (0, 0))[idx],
                    through_balls=distribution.get("through_balls", (0, 0))[idx],
                    penalty_area_entries=distribution.get(
                        "penalty_area_entries", (0, 0)
                    )[idx],
                    open_play_crosses=distribution.get("open_play_crosses", (0, 0))[
                        idx
                    ],
                    final_thirds_entries=distribution.get(
                        "final_thirds_entries", (0, 0)
                    )[idx],
                    dribbles_success=general.get("dribbles_success", (0, 0))[idx],
                    corners_won=general.get("corners_won", (0, 0))[idx],
                    possession_lost_defensive=general.get(
                        "possession_lost_defensive", (0, 0)
                    )[idx],
                    possession_lost_midfield=general.get(
                        "possession_lost_midfield", (0, 0)
                    )[idx],
                    offsides=general.get("offsides", (0, 0))[idx],
                    ball_recoveries_attacking=defence.get(
                        "ball_recoveries_attacking", (0, 0)
                    )[idx],
                    interceptions=defence.get("interceptions", (0, 0))[idx],
                    tackles=defence.get("tackles", (0, 0))[idx],
                    ball_recoveries_midfield=defence.get(
                        "ball_recoveries_midfield", (0, 0)
                    )[idx],
                    ball_recoveries_defensive=defence.get(
                        "ball_recoveries_defensive", (0, 0)
                    )[idx],
                    clearances=defence.get("clearances", (0, 0))[idx],
                    fouls_conceded=discipline.get("fouls_conceded", (0, 0))[idx],
                    fouls_won=general.get("fouls_won", (0, 0))[idx],
                    cards_yellow=discipline.get("cards_yellow", (0, 0))[idx],
                    cards_red=discipline.get("cards_red", (0, 0))[idx],
                )

            home = build(0)
            away = build(1)

            yield (
                TeamMomentumStats(time_in_match=time_text, stats=home),
                TeamMomentumStats(time_in_match=time_text, stats=away),
            )

            print(f"[Crawler] ⏱ Cycle {time.time() - cycle_start:.2f}s")
            await asyncio.sleep(0.5)

    finally:
        driver.quit()
        print("[Crawler] Chrome closed.")
