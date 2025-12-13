import asyncio
import os
import time
from typing import Any, AsyncGenerator, Dict

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from clients import Clients
from momentum.calculate import MomentumUsedStats, TeamMomentumStats

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


# async def save_stats_to_mongo(time_text: str, stats_all: Dict[str, Any]):
#     """Lưu dữ liệu của 5 tab vào MongoDB (chạy song song với xuất dữ liệu)."""
#     try:
#         attack = stats_all["Attack"]
#         defence = stats_all["Defence"]
#         discipline = stats_all["Discipline"]
#         distribution = stats_all["Distribution"]
#         general = stats_all["General"]

#         # insert concurrent
#         await asyncio.gather(
#             MatchAttackStats(time_in_match=time_text, **attack).insert(),
#             MatchDefenceStats(time_in_match=time_text, **defence).insert(),
#             MatchDisciplineStats(time_in_match=time_text, **discipline).insert(),
#             MatchDistributionStats(time_in_match=time_text, **distribution).insert(),
#             MatchGeneralStats(time_in_match=time_text, **general).insert(),
#         )
#         print(f"[Mongo] ✅ Inserted stats at {time_text}", flush=True)
#     except Exception as e:
#         print(f"[Mongo] ⚠️ Failed to insert {time_text}: {e}")


# ============================================================
# HELPERS
# ============================================================
def _to_num(x: str) -> float | int:
    x = x.strip().replace("%", "")
    if not x:
        return 0

    try:
        return int(x)
    except:
        try:
            return float(x)
        except:
            return 0


TAB_INDEX = {
    "General": 0,
    "Distribution": 1,
    "Attack": 2,
    "Defence": 3,
    "Discipline": 4,
}


# ============================================================
# CLOCK READER
# ============================================================
def get_time_text(driver: webdriver.Chrome) -> str:
    selectors = [
        ".Opta-ClockContainer .Opta-Clock span",
        ".Opta-ClockContainer abbr",
    ]
    for sel in selectors:
        try:
            el = driver.find_element("css selector", sel)
            if el.text.strip():
                return el.text.strip()
        except:
            continue
    return ""


# ============================================================
# PARSE TAB CONTENT
# ============================================================
def _extract_tab_html(driver, tab_name: str) -> str | None:
    idx = TAB_INDEX[tab_name] + 1
    js = f"""
        const node = document.querySelector(
            "ul.Opta-TabbedContent > li:nth-child({idx}) table.Opta-Stats-Bars tbody"
        );
        return node ? node.innerHTML : null;
    """
    return driver.execute_script(js)


def parse_tab_html(html: str) -> dict:
    stats = {}
    if not html:
        return stats

    soup = BeautifulSoup(html, "html.parser")
    for row in soup.select("tr"):
        cls = row.get("class", [])
        if not cls:
            continue
        cls = cls[0]
        if not cls.startswith("Opta-"):
            continue

        key = cls.split("_", 1)[1] if "_" in cls else cls.replace("Opta-", "")
        tds = row.select("td")
        if len(tds) < 2:
            continue

        left = _to_num(tds[0].get_text(strip=True))
        right = _to_num(tds[-1].get_text(strip=True))
        stats[key] = (left, right)

    return stats


def extract_tab(driver, tab_name: str):
    html = _extract_tab_html(driver, tab_name)
    stats = parse_tab_html(html)
    print(f"[SNAPSHOT_JS] {tab_name}: {stats}")
    return stats


# ============================================================
# TIME NORMALIZATION
# ============================================================
def to_seconds(t: str) -> int:
    t = t.strip()
    if t in {"Half Time", "Full Time"}:
        return -1

    if "+" in t:
        base, extra = t.split("+")
        base = base.strip()
        extra = extra.strip()
        m1, s1 = map(int, base.split(":"))
        m2, s2 = map(int, extra.split(":"))
        return m1 * 60 + s1 + m2 * 60 + s2

    m, s = map(int, t.split(":"))
    return m * 60 + s


# ============================================================
# TIME NORMALIZATION (fixed)
# ============================================================
def normalize_time(raw: str, in_second_half: bool) -> str:
    raw = raw.strip()

    if raw == "HT":
        return "Half Time"
    if raw == "FT":
        return "Full Time"

    if ":" not in raw:
        return raw

    try:
        m, s = map(int, raw.split(":"))
    except:
        return raw

    sec = m * 60 + s

    # ======= HIỆP 1 =======
    if not in_second_half:
        if sec > 45 * 60:
            extra = sec - 45 * 60
            return f"45:00 + {extra // 60}:{extra % 60:02d}"
        return f"{m}:{s:02d}"

    # ======= HIỆP 2 =======
    if sec > 90 * 60:
        extra = sec - 90 * 60
        return f"90:00 + {extra // 60}:{extra % 60:02d}"

    return f"{m}:{s:02d}"


# ============================================================
# MAIN CRAWLER STREAM
# ============================================================
async def crawl_match_data_stream(
    match_url: str,
    db_name: str,
) -> AsyncGenerator[tuple[str, bool, TeamMomentumStats, TeamMomentumStats], None]:
    await mongo_client.initialize(db_name=db_name)

    driver = make_driver()
    driver.get(match_url)

    print("[Crawler] ⚡ Start loop")

    tabs = ["General", "Distribution", "Attack", "Defence", "Discipline"]

    is_halftime = False
    in_second_half = False

    try:
        while True:
            raw_time = get_time_text(driver).strip()
            if not raw_time:
                await asyncio.sleep(0.1)
                continue

            print(f"\n[RAW CLOCK] {raw_time}")

            # FULL TIME
            if raw_time == "FT":
                home_empty = TeamMomentumStats(
                    time_in_match="Full Time", stats=last_home
                )
                away_empty = TeamMomentumStats(
                    time_in_match="Full Time", stats=last_away
                )
                yield ("Full Time", False, home_empty, away_empty)
                break

            # HALF TIME
            if raw_time == "HT":
                if not is_halftime:
                    is_halftime = True
                    home_empty = TeamMomentumStats(
                        time_in_match="Half Time", stats=last_home
                    )
                    away_empty = TeamMomentumStats(
                        time_in_match="Half Time", stats=last_away
                    )
                    yield ("Half Time", True, home_empty, away_empty)

                await asyncio.sleep(1)
                continue

            # VỪA HẾT HT → vào HIỆP 2
            if is_halftime and raw_time not in {"HT", "FT"}:
                sec = to_seconds(raw_time)
                if sec > 45 * 60:
                    in_second_half = True
                    is_halftime = False
                    print("[Crawler] 🟢 Second half started at", raw_time)

            print(
                f"is_halftime={is_halftime}, in_second_half={in_second_half}, raw_time={raw_time}"
            )
            # Chuẩn hóa thời gian
            norm_time = normalize_time(raw_time, in_second_half)
            print(f"[CLOCK] raw={raw_time} → normalized={norm_time}")

            # GET STATS
            stats_all = {tab: extract_tab(driver, tab) for tab in tabs}
            # asyncio.create_task(save_stats_to_mongo(norm_time, stats_all))
            # await save_stats_to_mongo(norm_time, stats_all)

            def build(idx: int) -> MomentumUsedStats:
                attack = stats_all["Attack"]
                defence = stats_all["Defence"]
                discipline = stats_all["Discipline"]
                distribution = stats_all["Distribution"]
                general = stats_all["General"]
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
            last_home = build(0)
            last_away = build(1)
            home = TeamMomentumStats(time_in_match=norm_time, stats=build(0))
            away = TeamMomentumStats(time_in_match=norm_time, stats=build(1))

            yield (norm_time, False, home, away)

            await asyncio.sleep(0.7)

    finally:
        driver.quit()
        print("[Crawler] Chrome closed.")
