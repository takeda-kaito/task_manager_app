# tasks/admin.py

from django.contrib import admin
from .models import Category, Task

# ==============================================================================
# 1. Category モデルの管理画面設定
# ==============================================================================


# Category モデルをDjango管理画面に登録
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category モデルの管理画面での表示と操作をカスタマイズする。"""

    # 一覧画面（リスト表示）に表示するフィールドを指定
    # name: カテゴリ名, user: カテゴリを作成したユーザー
    list_display = ("name", "user")

    # 📝 Note: userフィールドでフィルタリングを追加すると、特定のユーザーのカテゴリを見つけやすくなる
    # list_filter = ('user',)


# ==============================================================================
# 2. Task モデルの管理画面設定
# ==============================================================================


# Task モデルをDjango管理画面に登録
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Task モデルの管理画面での表示、フィルタリング、検索をカスタマイズする。"""

    # 一覧画面（リスト表示）に表示するフィールドを指定
    list_display = ("title", "user", "category", "status", "due_date", "is_deleted")

    # サイドバーに表示するフィルタリング項目を指定
    # status: 進捗状況, is_deleted: 論理削除フラグ, category: カテゴリ, due_date: 期限
    list_filter = ("status", "is_deleted", "category", "due_date")

    # 検索ボックスで検索対象とするフィールドを指定
    # title: タイトル, description: 詳細
    search_fields = ("title", "description")

    # 📝 Note: 編集画面でフィールドの表示順を定義することもできます
    # fields = ('user', 'title', 'description', 'category', 'priority', 'status', 'due_date', 'is_deleted')
