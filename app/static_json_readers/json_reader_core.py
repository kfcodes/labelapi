from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Generic, Optional, Protocol, Tuple, TypeVar

# ========= Types =========

T = TypeVar("T")  # Final, validated, normalized config type


class Logger(Protocol):
    def __call__(self, message: str, /) -> None: ...


class Extractor(Protocol):
    """Extract a sub-object from loaded JSON or pass-through as-is."""

    def __call__(self, data: Any, /) -> Any: ...


class Validator(Protocol, Generic[T]):
    """Validate + normalize arbitrary data into T (or raise)."""

    def __call__(self, data: Any, /) -> T: ...


# ========= Paths =========

BASE_DIR: Path = Path(__file__).resolve().parents[1]
ENV_DIR: Path = BASE_DIR / "env"

# ========= Helpers =========


def resolve_path(
    path: Optional[str | Path],
    *,
    default_path: Path,
) -> Path:
    """
    Apply resolution rules:
      - None           -> default_path
      - Absolute       -> as-is
      - Starts with 'env/' relative to project BASE_DIR
      - Otherwise      -> relative to ENV_DIR
    """
    if path is None:
        return default_path

    p = Path(path)
    if p.is_absolute():
        return p

    if p.parts and p.parts[0] == "env":
        return BASE_DIR / p

    return ENV_DIR / p


def read_json_file(path: Path, *, context: str) -> Any:
    """
    Read and parse JSON from a file with friendly errors.
    """
    if not path.exists():
        raise FileNotFoundError(f"{context.title()} file not found: {path}")

    try:
        text = path.read_text(encoding="utf-8").strip()
    except Exception as e:  # IO issues, permissions, etc.
        raise OSError(f"Failed reading {context} file {path}: {e}") from e

    if not text:
        raise ValueError(f"{context.title()} file is empty: {path}")

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid {context} JSON in {path}: {e}") from e


# ========= Loader =========


@dataclass
class JsonConfigLoader(Generic[T]):
    """
    Thread-safe, reusable JSON config loader with:
      - Lazy in-memory cache
      - Path resolution (BASE_DIR/env-aware)
      - Pluggable extractor + validator
      - Last-loaded metadata (path + mtime)
    """

    default_path: Path
    context: str
    validator: Validator[T]
    extractor: Optional[Extractor] = None

    # Internal state (use default_factory for mutables/threading primitives)
    _lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False
    )
    _loaded: bool = field(default=False, init=False, repr=False)
    _config: Optional[T] = field(default=None, init=False, repr=False)
    _last_path: Optional[Path] = field(default=None, init=False, repr=False)
    _last_mtime: Optional[float] = field(default=None, init=False, repr=False)

    def load(
        self,
        path: Optional[str | Path] = None,
        *,
        logger: Optional[Logger] = None,
        log_pretty_json: bool = False,
    ) -> T:
        """
        Load (and cache) config from resolved path.
        Returns the validated config of type T.
        """
        with self._lock:
            file_path = resolve_path(path, default_path=self.default_path)

            raw = read_json_file(file_path, context=self.context)
            data = self.extractor(raw) if self.extractor else raw
            cfg: T = self.validator(data)

            if logger:
                if log_pretty_json:
                    try:
                        pretty = json.dumps(data, indent=4, ensure_ascii=False)
                    except Exception:
                        pretty = str(data)
                    logger(f"[{self.context}] Loaded from {file_path}:\n{pretty}")
                else:
                    logger(f"[{self.context}] Loaded from {file_path}")

            self._config = cfg
            self._loaded = True
            self._last_path = file_path
            try:
                self._last_mtime = file_path.stat().st_mtime
            except Exception:
                self._last_mtime = None

            return cfg

    def ensure_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError(
                f"{self.context.title()} config not loaded. Call load() during startup."
            )

    def get(self) -> T:
        """
        Return the cached config (must be loaded first).
        """
        self.ensure_loaded()
        # Returning the cached object; copy in callers if immutability is required.
        return self._config  # type: ignore[return-value]

    def get_last_loaded_meta(self) -> Tuple[Optional[Path], Optional[float]]:
        """
        Returns (path, mtime) of the last successful load.
        """
        return self._last_path, self._last_mtime
