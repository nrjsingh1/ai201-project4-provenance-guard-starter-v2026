"""
Running Provenance Guard under gunicorn instead of Flask's development server.
Unit 9, shape B: local, with logs.

    gunicorn -c gunicorn.conf.py app:app

Address and port come from config.py, which reads HOST and PORT from the
environment — the same two settings `python app.py` uses, so the two ways of
running can't drift apart.
"""

# Not `import config`: gunicorn reads every top-level name here as a setting,
# and `config` is one of its own.
import config as app_config

bind = f"{app_config.HOST}:{app_config.PORT}"

# One worker, on purpose. Each worker loads its own copy of gpt2 (~525 MB), and
# the rate limiter keeps its counts in memory per worker: two workers would
# each allow RATE_LIMIT_PER_MINUTE, quietly doubling the limit unit 8 tested.
workers = 1

# The first /submit loads the model, which takes 10–20 seconds on a laptop and
# longer on an old one. gunicorn's default 30-second timeout would kill the
# worker mid-load and the request would look like a crash.
timeout = 120
