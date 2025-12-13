from .hasher import HashFunction

hasher = HashFunction()
import json

with open("utils/level_up_point.json", "r") as f:
    LEVEL_UP_POINTS = json.load(f)