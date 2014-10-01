#!/usr/bin/env bash
nosetests --with-xunit --nologcapture tests/integration/
behave -v --junit --junit-directory . --no-logcapture --logging-level=DEBUG tests/integration/features/
