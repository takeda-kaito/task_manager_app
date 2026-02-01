#!/usr/bin/env bash
# エラーが発生したら即座に終了する設定
set -o errexit

# 1. ライブラリのインストール
pip install -r requirements.txt

# 2. 静的ファイル（CSS/JSなど）の集約
python manage.py collectstatic --no-input

# 3. データベースのマイグレーション（テーブル作成・更新）
python manage.py migrate

# 前回の行を消して、これを貼り付けてください
python manage.py createsuperuser --no-input --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || python manage.py changepassword "$DJANGO_SUPERUSER_USERNAME" <<EOF
$DJANGO_SUPERUSER_PASSWORD
$DJANGO_SUPERUSER_PASSWORD
EOF