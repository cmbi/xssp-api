#!/usr/bin/env bash
export XSSP_REST_SETTINGS='../dev_settings.py'
celery -A xssp_rest.application:celery worker -B
