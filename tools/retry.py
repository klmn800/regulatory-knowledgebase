"""
Retry helper for Anthropic API calls.

Bounds rate-limit / API-error retries with a small decorator. On final failure
the helper re-raises — callers handle error surfacing themselves (synthesis
returns SynthesisResult with the error message in `answer`; comparator and QC
will surface differently when they migrate). Logs each retry to stderr.
"""

import sys
import time
from functools import wraps

import anthropic


def with_rate_limit_retry(max_attempts: int = 2, sleep_seconds: int = 60):
    """Retry on anthropic.RateLimitError or anthropic.APIError.

    Sleeps `sleep_seconds` between attempts; up to `max_attempts` total tries.
    Re-raises after the final attempt fails. Each retry logs a one-line
    notice to stderr in the form:
        [rate limited, waiting 60s, attempt 2/2]
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (anthropic.RateLimitError, anthropic.APIError):
                    if attempt >= max_attempts:
                        raise
                    print(
                        f"[rate limited, waiting {sleep_seconds}s, "
                        f"attempt {attempt + 1}/{max_attempts}]",
                        file=sys.stderr,
                        flush=True,
                    )
                    time.sleep(sleep_seconds)
        return wrapper
    return decorator
