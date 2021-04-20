import os
import sys
import time
import numpy as np

from typing import Iterable, List, Optional


class ProgBar:
    """Displays a progress bar.

      Arguments:
          target: Total number of steps expected, None if unknown.
          width: Progress bar width on screen.
          stateful_metrics: Iterable of string names of metrics that should *not* be
            averaged over time. Metrics in this list will be displayed as-is. All
            others will be averaged by the progbar before display.
          interval: Minimum visual progress update interval (in seconds).
    """

    def __init__(self,
                 target: int,
                 width: int = 30,
                 interval: float = 0.05,
                 stateful_metrics: Optional[Iterable] = None):
        self._target = target
        self._width = width
        self._interval = interval
        if stateful_metrics:
            self._stateful_metrics = set(stateful_metrics)
        else:
            self._stateful_metrics = set()

        self._dynamic_display = ((hasattr(sys.stdout, 'isatty') and
                                  sys.stdout.isatty()) or
                                 'ipykernel' in sys.modules or
                                 'posix' in sys.modules or
                                 'PYCHARM_HOSTED' in os.environ)
        self._total_width = 0
        self._seen_so_far = 0
        # We use a dict + list to avoid garbage collection issues found in OrderedDict
        self._values = {}
        self._values_order = []
        self._start = time.time()
        self._last_update = 0

    def update(self,
               current: int,
               values: Optional[List] = None,
               finalize: Optional[bool] = None):
        """Updates the progress bar.

        Arguments:
            current: Index of current step.
            values: List of tuples: `(name, value_for_last_step)`. If `name` is in
              `stateful_metrics`, `value_for_last_step` will be displayed as-is.
              Else, an average of the metric over time will be displayed.
            finalize: Whether this is the last update for the progress bar. If
              `None`, defaults to `current >= self._target`.
        """
        if finalize is None:
            if self._target is None:
                finalize = False
            else:
                finalize = current >= self._target

        values = values or []
        for k, v in values:
            if k not in self._values_order:
                self._values_order.append(k)
            if k not in self._stateful_metrics:
                # Force the minimal value to 1 here, otherwise stateful_metric will be 0s.
                value_base = max(current - self._seen_so_far, 1)
                if k not in self._values:
                    self._values[k] = [v * value_base, value_base]
                else:
                    self._values[k][0] += v * value_base
                    self._values[k][1] += value_base
            else:
                # Stateful metrics output a numeric value. This representation
                # means "take an average from a single value" but keeps the
                # numeric formatting.
                self._values[k] = [v, 1]
        self._seen_so_far = current

        now = time.time()
        info = f' - {now - self._start:.0f}s'
        if now - self._last_update < self._interval and not finalize:
            return

        prev_total_width = self._total_width
        if self._dynamic_display:
            sys.stdout.write('\b' * prev_total_width)
            sys.stdout.write('\r')
        else:
            sys.stdout.write('\n')

        if self._target is not None:
            num_digits = int(np.log10(self._target)) + 1
            bar = f'{current:{num_digits}d}/{self._target} ['
            progress = float(current) / self._target
            progress_width = int(self._width * progress)
            if progress_width > 0:
                bar += ('=' * (progress_width - 1))
                if current < self._target:
                    bar += '>'
                else:
                    bar += '='
            bar += ('.' * (self._width - progress_width))
            bar += ']'
        else:
            bar = f'{current:7d}/Unknown'

        self._total_width = len(bar)
        sys.stdout.write(bar)

        if current:
            time_per_unit = (now - self._start) / current
        else:
            time_per_unit = 0

        if self._target is not None and not finalize:
            eta = time_per_unit * (self._target - current)
            if eta > 3600:
                eta_format = f'{eta // 3600:.0f}:{(eta % 3600) // 60:02.0f}:{eta % 60:02.0f}'
            elif eta > 60:
                eta_format = f'{eta // 60:.0f}:{eta % 60:02.0f}'
            else:
                eta_format = f'{eta:.0f}s'
            info = f' - ETA: {eta_format}'

        for k in self._values_order:
            info += f' - {k}:'
            if isinstance(self._values[k], list):
                avg = np.mean(self._values[k][0] / max(1, self._values[k][1]))
                if abs(avg) > 1e-3:
                    info += f' {avg:.4f}'
                else:
                    info += f' {avg:.4e}'
            else:
                info += f' {self._values[k]}'

        self._total_width += len(info)
        if prev_total_width > self._total_width:
            info += (' ' * (prev_total_width - self._total_width))

        if finalize:
            info += '\n'

        sys.stdout.write(info)
        sys.stdout.flush()

        self._last_update = now

    def add(self, n, values=None):
        self.update(self._seen_so_far + n, values)


class DownloadProgBar:

    def __init__(self):
        self._progbar = None
        self._last_progress = 0
        self._last_time = 0
        self._last_print_progress = 0

    def update(self, current: int, total: int, *args):
        if self._progbar is None:
            self._progbar = ProgBar(total, stateful_metrics=['Speed (MiB/s)'], interval=1)

        diff_progress = current - self._last_progress
        self._last_progress = current

        current_time = time.time()
        speed = None
        if current_time - self._last_time > 2:
            diff_print_progress = current - self._last_print_progress
            diff_time = current_time - self._last_time
            speed = diff_print_progress / 1024 / 1024 / diff_time
            self._last_print_progress = current
            self._last_time = current_time

        if speed is None or np.isclose(speed, 0):
            values = []
        else:
            values = [('Speed (MiB/s)', speed)]
        self._progbar.add(diff_progress, values=values)
