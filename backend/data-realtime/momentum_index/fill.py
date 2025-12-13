import json

# ---------------------------------------
# 🔧 FILE INPUT / OUTPUT
# ---------------------------------------
INPUT_FILE = "/Users/Yuki/Futstar/data-aggregator-v1/momentum_index/brugge.json"  # đặt file input vào đây
OUTPUT_FILE = "brugge_filled.json"


# ---------------------------------------
# 🔧 TIME HELPERS
# ---------------------------------------
def time_to_seconds(t: str) -> int:
    """Convert 'mm:ss' hoặc '90+8:55' → giây."""
    if "+" in t:
        main, extra = t.split("+")
        mm, ss = map(int, extra.split(":"))
        return int(main) * 60 + mm * 60 + ss
    mm, ss = map(int, t.split(":"))
    return mm * 60 + ss


def seconds_to_time(sec: int) -> str:
    """Convert giây → 'mm:ss'."""
    m = sec // 60
    s = sec % 60
    return f"{m}:{s:02d}"


def increment_stoppage(base: str, delta: int) -> str:
    """
    Tăng thời gian '45+2:33' theo số giây.
    """
    main, extra = base.split("+")
    mm, ss = map(int, extra.split(":"))
    total = mm * 60 + ss + delta
    return f"{main}+{total // 60}:{total % 60:02d}"


def is_stoppage(t: str) -> bool:
    return "+" in t


# ---------------------------------------
# 🔥 FILL LOGIC
# ---------------------------------------
def fill_timeline(data):
    filled = []
    prev = None
    prev_sec = None

    for item in data:
        t = item["time_in_match"]
        sec = time_to_seconds(t)

        # lần đầu
        if prev is None:
            filled.append(item)
            prev = item
            prev_sec = sec
            continue

        gap = sec - prev_sec

        # Không gap → append luôn
        if gap <= 1:
            filled.append(item)
            prev = item
            prev_sec = sec
            continue

        # Xác định dạng hiệp phụ / thường
        prev_is_plus = is_stoppage(prev["time_in_match"])
        curr_is_plus = is_stoppage(t)

        # -----------------------------------
        # CASE 1: Cùng dạng bù giờ → fill dạng +xxx:yy
        # -----------------------------------
        if prev_is_plus and curr_is_plus:
            for d in range(1, gap):
                new_item = prev.copy()
                new_item["time_in_match"] = increment_stoppage(prev["time_in_match"], d)
                filled.append(new_item)

        # -----------------------------------
        # CASE 2: Chuyển hiệp + → thường hoặc thường → +
        # KHÔNG FILL
        # -----------------------------------
        elif (prev_is_plus and not curr_is_plus) or (not prev_is_plus and curr_is_plus):
            pass

        # -----------------------------------
        # CASE 3: Cả 2 đều dạng thường mm:ss → fill normal
        # -----------------------------------
        else:
            for d in range(1, gap):
                new_item = prev.copy()
                new_item["time_in_match"] = seconds_to_time(prev_sec + d)
                filled.append(new_item)

        # Thêm phần tử hiện tại
        filled.append(item)
        prev = item
        prev_sec = sec

    return filled


# ---------------------------------------
# 🚀 MAIN
# ---------------------------------------
def main():
    print(f"📥 Loading {INPUT_FILE} ...")
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    print("⏳ Filling timeline ...")
    filled = fill_timeline(data)

    print(f"💾 Saving to {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(filled, f, indent=4)

    print("✅ Done!")


if __name__ == "__main__":
    main()
