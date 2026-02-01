#!/usr/bin/env bash
# エラーが発生したら即座に終了する設定
set -o errexit

# 1. ライブラリのインストール
pip install -r requirements.txt

# 2. 静的ファイル（CSS/JSなど）の集約
python manage.py collectstatic --no-input

# 3. データベースのマイグレーション（テーブル作成・更新）
python manage.py migrate