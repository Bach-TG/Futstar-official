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
    text = td.get_attribute("innerText") or td.text or ""
    if not text.strip():
        text = td.get_attribute("innerHTML") or ""

    m = re.search(r"[-+]?\d*\.?\d+", text.replace(",", ""))
    if not m:
        return 0
    return _to_num(m.group(0))


# ============================================================
#  TAB CONFIG
# ============================================================
TAB_INDEX: Dict[str, int] = {
    "General": 0,
    "Distribution": 1,
    "Attack": 2,
    "Defence": 3,
    "Discipline": 4,
}


# ============================================================
#  CLOCK READER
# ============================================================
def get_time_text(driver: webdriver.Chrome) -> str:
    # try:
    #     el = driver.find_element(By.CSS_SELECTOR, ".Opta-ClockContainer .Opta-Stoppage")
    #     if el.text.strip():
    #         return el.text.strip()
    # except:
    #     pass

    try:
        el = driver.find_element(
            By.CSS_SELECTOR, ".Opta-ClockContainer .Opta-Clock span"
        )
        if el.text.strip():
            return el.text.strip()
    except:
        pass

    try:
        el = driver.find_element(By.CSS_SELECTOR, ".Opta-ClockContainer abbr")
        if el.text.strip():
            return el.text.strip()
    except:
        pass

    return ""


# ============================================================
#  DIRECT DOM PARSER (KHÔNG CLICK TAB)
# ============================================================
def _activate_and_extract_tab_stats(
    driver: webdriver.Chrome, tab_name: str
) -> Dict[str, Any]:
    stats: Dict[str, Any] = {}

    try:
        idx = TAB_INDEX[tab_name] + 1  # nth-child dùng index 1-based

        selector = (
            f"ul.Opta-TabbedContent > li:nth-child({idx}) table.Opta-Stats-Bars tbody"
        )
        tbody = driver.find_element(By.CSS_SELECTOR, selector)
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

    try:
        while True:
            cycle_start = time.time()

            time_text = get_time_text(driver)
            if not time_text:
                await asyncio.sleep(0.2)
                continue

            if time_text == "HT":
                time_text = "45:00"
            elif time_text == "FT":
                time_text = "90:00"

            print(f"\n=== CLOCK: {time_text} ===")

            # đọc nhanh các tab (không click)
            stats_all: Dict[str, Dict[str, Any]] = {
                tab: _activate_and_extract_tab_stats(driver, tab) for tab in tabs
            }

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

            await save_stats_to_mongo(time_text, stats_all)

            print(f"[Crawler] ⏱ Cycle {time.time() - cycle_start:.2f}s")

            yield (
                TeamMomentumStats(time_in_match=time_text, stats=home),
                TeamMomentumStats(time_in_match=time_text, stats=away),
            )

            await asyncio.sleep(0.3)  # tốc độ tối đa an toàn

    finally:
        driver.quit()
        print("[Crawler] Chrome closed.")
