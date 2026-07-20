#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
flask --app run.py db upgrade
python seed.py