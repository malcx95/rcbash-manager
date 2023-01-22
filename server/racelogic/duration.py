from typing import Tuple, Dict


class Duration:

    def __init__(self, milliseconds=0, seconds=0, minutes=0):
        self.milliseconds = milliseconds + seconds * 1000 + minutes * 60 * 1000

    def minutes_seconds_milliseconds(self) -> Tuple[int, int, int]:
        """Returns a tuple representing this duration as (minutes, seconds, milliseconds)"""
        minutes = (self.milliseconds / 1000) // 60
        seconds = (self.milliseconds - (minutes * 60 * 1000)) // 1000
        milliseconds = self.milliseconds - seconds * 1000 - minutes * 60 * 1000
        return int(minutes), int(seconds), int(milliseconds)

    def minutes_seconds_milliseconds_dict(self) -> Dict[str, int]:
        """
        Returns a dict representing this duration as
        {"minutes": minutes, "seconds": seconds, "milliseconds": milliseconds}
        """
        minutes = (self.milliseconds / 1000) // 60
        seconds = (self.milliseconds - (minutes * 60 * 1000)) // 1000
        milliseconds = self.milliseconds - seconds * 1000 - minutes * 60 * 1000
        return {"minutes": int(minutes), "seconds": int(seconds), "milliseconds": int(milliseconds)}

    def __add__(self, other):
        return Duration(self.milliseconds + other.milliseconds)

    def __mul__(self, num):
        return Duration(int(self.milliseconds * num))

    def __eq__(self, other):
        return self.milliseconds == other.milliseconds

    def __ge__(self, other):
        return self.milliseconds >= other.milliseconds

    def __gt__(self, other):
        return self.milliseconds > other.milliseconds

    def __le__(self, other):
        return self.milliseconds <= other.milliseconds

    def __lt__(self, other):
        return self.milliseconds < other.milliseconds

    def __repr__(self):
        minutes, seconds, milliseconds = self.minutes_seconds_milliseconds()
        return f"Duration(minutes={minutes}, seconds={seconds}, milliseconds={milliseconds})"

    def __str__(self):
        minutes, seconds, milliseconds = self.minutes_seconds_milliseconds()
        return f"{minutes}:{seconds:02d}:{milliseconds:03d}"

    def __hash__(self):
        return self.milliseconds
