"""
Simple class for displaying the progress of a running process.

---------
Variables
---------

threshold:
    The maximum set value, denoting the denominator.

current:
    The current set value, denoting the numerator.

increment:
    The size of the step on current every time the progress bar is updated.
    Default is 1.0.

progress:
    Returns the current progress as a percentage.

-------
Methods
-------

console_update():
    Calculates the current progress as a percentage and prints it to the console.

reset():
    Resets the progress bar back to 0%.

"""

from sys import stdout

class ProgressBar:
    def __init__(self, threshold: float = 100.00, increment: float = 1.0):
        self._threshold = threshold
        self._current = 0.0
        self._increment = increment

    @property
    def progress(self):
        return (self._current / self._threshold) * 100

    def update(self):
        self._current = min(self._threshold, self._current + 1.0)
        return self.progress

    def console_update(self):
        stdout.write(f'\rPercent complete: {self.update():2.2f}%')
        stdout.flush()

    def reset(self, threshold: float = None, increment: float = None):
        self._current = 0.0
        self._threshold = threshold or self._threshold
        self._increment = increment or self._increment
