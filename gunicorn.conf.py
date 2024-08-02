# gunicorn.conf.py

# Gunicorn configuration file

# Server socket
bind = '0.0.0.0:8080'

# Worker processes
workers = 1
threads = 8

# Logging
loglevel = 'info'
accesslog = None
errorlog = None
timeout = 600
