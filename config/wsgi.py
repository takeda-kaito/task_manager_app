"""
WSGI config for config project.

このファイルは、プロジェクトのWSGI (Web Server Gateway Interface) アプリケーションを
設定します。同期サーバー（例: Gunicorn, uWSGI）がアプリケーションを呼び出すためのエントリーポイントです。
"""

import os

from django.core.wsgi import get_wsgi_application

# 環境変数 'DJANGO_SETTINGS_MODULE' を設定します。
# これにより、Djangoはどの設定ファイル（settings.py）を使用すべきかを認識します。
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# DjangoのWSGIアプリケーションを取得し、'application' というモジュールレベル変数として公開します。
# 外部のWSGIサーバーは、この 'application' オブジェクトをエントリーポイントとして使用します。
application = get_wsgi_application()