#!/usr/bin/env bash
export XSSP_REST_SETTINGS='../dev_settings.py'
gunicorn --log-level debug --log-file "-" -k gevent -b 127.0.0.1:5000 xssp_rest.application:app
