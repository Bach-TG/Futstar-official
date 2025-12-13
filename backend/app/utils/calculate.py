async def convert_to_seconds(time_in_match: str) -> int:
    if time_in_match.find("+") != -1:
        main_time, extra_time = time_in_match.split("+")
        extra_minutes, extra_seconds = extra_time.split(":")
        return int(main_time) * 60 + int(extra_minutes) * 60 + int(extra_seconds)
    else:
        minutes, seconds = time_in_match.split(":")
        return int(minutes) * 60 + int(seconds)


async def calculate_difference_time(previous_time: str, current_time: str, first_half_end_time: str | None = None) -> int:        
    previous_seconds = await convert_to_seconds(previous_time)
    current_seconds = await convert_to_seconds(current_time)
    if previous_time.find("+") != -1 and current_time.find("+") == -1:
        if first_half_end_time:
            first_half_end_seconds = await convert_to_seconds(first_half_end_time)
            return (first_half_end_seconds - previous_seconds) + current_seconds - (await convert_to_seconds("45:00"))
        else:
            return 1
    return current_seconds - previous_seconds


async def calculate_pnl(entry: float, current: float, D: float) -> float:
    E = (entry - 0) / 100.0 if current >= entry else (100 - entry) / 100.0
    res = D * E * ((current - entry) / 100.0) * ((1.0) / (1.0 - E))
    
    return res


async def next_second_time_in_match(time_in_match: str) -> str:
    if time_in_match.find("+") == -1:
        minutes, seconds = map(int, time_in_match.split(":"))
        total_seconds = minutes * 60 + seconds + 1
        new_minutes = total_seconds // 60
        new_seconds = total_seconds % 60
        return f"{new_minutes}:{new_seconds:02}".strip()
    # else:
    #     if first_half_end:
    #         return "45:01"
    #     else:
    #         main_time, extra_time = time_in_match.split("+")
    #         extra_minutes, extra_seconds = map(int, extra_time.split(":"))
    #         total_extra_seconds = extra_minutes * 60 + extra_seconds + 1
    #         new_extra_minutes = total_extra_seconds // 60
    #         new_extra_seconds = total_extra_seconds % 60
    #         return f"{main_time}+{new_extra_minutes}:{new_extra_seconds:02}"
