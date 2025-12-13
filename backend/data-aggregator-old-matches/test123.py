import asyncio
import json


async def next_seconds_time_in_match(time_in_match: str, first_half_end: bool) -> str:
    if time_in_match.find("+") == -1:
        minutes, seconds = map(int, time_in_match.split(":"))
        total_seconds = minutes * 60 + seconds + 1
        new_minutes = total_seconds // 60
        new_seconds = total_seconds % 60
        return f"{new_minutes:2}:{new_seconds:02}"
    else:
        if first_half_end:
            return "45:01"
        else:
            main_time, extra_time = time_in_match.split("+")
            extra_minutes, extra_seconds = map(int, extra_time.split(":"))
            total_extra_seconds = extra_minutes * 60 + extra_seconds + 1
            new_extra_minutes = total_extra_seconds // 60
            new_extra_seconds = total_extra_seconds % 60
            return f"{main_time}+{new_extra_minutes}:{new_extra_seconds:02}"

async def test():
    with open("momentum_index.json", "r") as f:
        raw_data = json.load(f)
        
    is_first_half = True
    previous_time = "0:00"
    for item in raw_data:
        current_time = item["time_in_match"]
        if current_time.find("+") == -1 and previous_time.find("+") != -1:
            is_first_half = False
        item["is_first_half"] = is_first_half
        previous_time = current_time

    new_data = []
    

if __name__ == "__main__":
    asyncio.run(test())
        
