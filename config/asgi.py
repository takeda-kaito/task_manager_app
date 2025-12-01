"""
ASGI config for config project.

このファイルは、プロジェクトのASGI (Asynchronous Server Gateway Interface) アプリケーションを
設定します。非同期サーバー（例: Daphne, Uvicorn）がアプリケーションを呼び出すためのエントリーポイントです。
"""

import os

from django.core.asgi import get_asgi_application

# 環境変数 'DJANGO_SETTINGS_MODULE' を設定します。
# これにより、Djangoはどの設定ファイル（settings.py）を使用すべきかを認識します。
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# DjangoのASGIアプリケーションを取得し、'application' というモジュールレベル変数として公開します。
# 外部のASGIサーバーは、この 'application' オブジェクトをエントリーポイントとして使用します。
application = get_asgi_application()