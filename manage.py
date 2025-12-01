#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """管理タスクを実行します (Run administrative tasks)。"""
    
    # 1. 環境変数の設定
    # Djangoに設定ファイル (settings.py) の場所を教える。
    # 'config.settings' はプロジェクトのルートディレクトリにある設定ファイルを指す。
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    try:
        # 2. Django管理コマンド実行関数のインポート
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # 3. ImportErrorの処理
        # Djangoがインストールされていない、または仮想環境が有効になっていない場合の警告メッセージ。
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        
    # 4. コマンドの実行
    # コマンドライン引数 (sys.argv, 例: ['manage.py', 'runserver']) に基づいてDjangoコマンドを実行する。
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # スクリプトが直接実行された場合に main 関数を呼び出す
    main()