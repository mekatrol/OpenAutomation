class Interval:
    def __init__(self, interval):
        self.interval = interval

        # Init count down to interval
        self._count_down = self.interval

    def interval_expired(self):
        # If there is not interval then it has expired
        if self.interval == None:
            return True

        # Decrement count down
        self._count_down -= 1

        # Count down not reached zero (interval incomplete)?
        if self._count_down > 0:
            return False

        # Reset countdown from interval
        self._count_down = self.interval

        return True
