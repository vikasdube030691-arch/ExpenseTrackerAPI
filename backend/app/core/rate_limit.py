from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory, per-process rate limiting. Fine for a single instance; a multi-instance
# deployment needs a shared backend (e.g. `Limiter(storage_uri="redis://...")`) so
# limits are enforced across processes rather than reset per instance.
#
# `default_limits` applies to every route unless overridden by an explicit
# `@limiter.limit(...)` on that route (e.g. login's stricter per-IP limit).
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
