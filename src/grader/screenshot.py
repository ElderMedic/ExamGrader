"""Screenshot utilities for periodic capture of exam grading interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Optional

import time

import mss
from PIL import Image


@dataclass
class CaptureRegion:
    """Represents a rectangular screen area in pixels."""

    left: int = 0
    top: int = 0
    width: Optional[int] = None
    height: Optional[int] = None

    def to_bbox(self, monitor: dict[str, int]) -> dict[str, int]:
        """Convert to an ``mss``-compatible bounding box."""

        monitor_width = monitor.get("width") or 0
        monitor_height = monitor.get("height") or 0

        width = self.width if self.width is not None else monitor_width
        height = self.height if self.height is not None else monitor_height

        if width is None or height is None or monitor_width <= 0 or monitor_height <= 0:
            raise ValueError("Monitor dimensions must be provided when width/height are None")

        return {
            "left": max(self.left, 0),
            "top": max(self.top, 0),
            "width": min(width, monitor_width),
            "height": min(height, monitor_height),
        }


@dataclass
class ScreenshotConfig:
    """Configuration for periodic screenshots."""

    region: CaptureRegion = CaptureRegion()
    interval_seconds: float = 10.0
    output_dir: Optional[Path] = None
    image_format: str = "png"


class ScreenshotTaker:
    """Cross-platform screenshot helper using ``mss``."""

    def __init__(self, config: ScreenshotConfig) -> None:
        self.config = config
        self._mss = mss.mss()

    def capture_once(self) -> Image.Image:
        """Capture a single screenshot according to the configured region."""

        monitor = self._select_primary_monitor()
        bbox = self.config.region.to_bbox(monitor)
        raw = self._mss.grab(bbox)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
        if self.config.output_dir:
            self._save_image(img)
        return img

    def iter_capture(self) -> Iterator[Image.Image]:
        """Generate screenshots indefinitely at the configured interval."""

        interval = max(self.config.interval_seconds, 0.5)
        while True:
            start = time.time()
            yield self.capture_once()
            elapsed = time.time() - start
            sleep_time = max(interval - elapsed, 0)
            time.sleep(sleep_time)

    def capture_with_callback(self, callback: Callable[[Image.Image], None], *, limit: Optional[int] = None) -> None:
        """Capture repeatedly and pass each image to ``callback``.

        Args:
            callback: Function called with each screenshot ``PIL.Image``.
            limit: Optional maximum number of iterations.
        """

        for idx, image in enumerate(self.iter_capture()):
            callback(image)
            if limit is not None and idx + 1 >= limit:
                break

    def _select_primary_monitor(self) -> dict[str, int]:
        monitors = self._mss.monitors
        if not monitors:
            raise RuntimeError("No monitors detected for screenshot capture")
        # monitors[0] is a virtual bounding box; prefer monitors[1] if available
        if len(monitors) > 1:
            return monitors[1]
        return monitors[0]

    def _save_image(self, image: Image.Image) -> Path:
        output_dir = self.config.output_dir
        if output_dir is None:
            raise ValueError("output_dir must be provided when saving screenshots")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        filepath = output_dir / f"capture_{timestamp}.{self.config.image_format}"
        image.save(filepath, format=self.config.image_format.upper())
        return filepath

    def close(self) -> None:
        self._mss.close()

    def __enter__(self) -> "ScreenshotTaker":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
