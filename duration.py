class Duration:
    
    def __init__(self, milliseconds, seconds=0, minutes=0):
        self.milliseconds = milliseconds + seconds * 1000 + minutes * 60 * 1000

    def minutes_seconds_milliseconds(self):
        minutes = (self.milliseconds / 1000) // 60
        seconds = (self.milliseconds - (minutes * 60 * 1000)) // 1000
        milliseconds = self.milliseconds - seconds * 1000 - minutes * 60 * 1000
        return int(minutes), int(seconds), int(milliseconds)
    
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
