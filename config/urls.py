"""
URL configuration for config project.
プロジェクト全体のURL設定ファイル。

`urlpatterns` リストが、URLと対応するビューをルーティングする役割を担う。
"""
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView

# tasksアプリケーションから必要なビューをインポート
from tasks.views import (
    UserRegisterView, 
    TaskListView, 
    TaskCreateView, 
    TaskUpdateView, 
    TaskDeleteView, 
    TrashView, 
    TaskRestoreView, 
    TaskBulkDeleteView, 
    CategoryCreateView, 
    CategoryListView, 
    CategoryDeleteView 
)
from tasks import views # 他のビュー（TaskDetailView, CategoryUpdateView, UserUpdateViewなど）はviewsから直接参照

# ==============================================================================
# URL Patterns
# ==============================================================================

urlpatterns = [
    # Django管理画面
    path('admin/', admin.site.urls),
    
    # --------------------------------------------------
    # タスク機能 (Task Management URLs)
    # --------------------------------------------------
    
    # ホームページ (タスク一覧表示)
    path('', TaskListView.as_view(), name='home'), 
    
    # タスクのステータス更新
    path('task/update_status/<int:pk>/', views.TaskUpdateStatusView.as_view(), name='task_update_status'),

    # タスク作成ページ
    path('tasks/create/', TaskCreateView.as_view(), name='task_create'),

    # タスク詳細ビュー
    path('tasks/<int:pk>/details/', views.TaskDetailView.as_view(), name='task_detail'), 

    # タスク編集ページ
    path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='task_update'), 
    
    # タスク削除処理
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='task_delete'), 
    
    # ゴミ箱一覧
    path('tasks/trash/', TrashView.as_view(), name='trash'), 
    
    # タスク復元処理
    path('tasks/<int:pk>/restore/', TaskRestoreView.as_view(), name='task_restore'), 

    # タスクの一括物理削除処理
    path('tasks/bulk-delete/', TaskBulkDeleteView.as_view(), name='task_bulk_delete'),

    # --------------------------------------------------
    # カテゴリ機能 (Category Management URLs)
    # --------------------------------------------------
    
    # カテゴリ一覧ページ
    path('categories/', CategoryListView.as_view(), name='category_list'),
    
    # カテゴリ作成ページ
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    
    # カテゴリ編集ページ
    path('category/update/<int:pk>/', views.CategoryUpdateView.as_view(), name='category_update'),
    
    # カテゴリ削除処理
    path('categories/delete/<int:pk>/', CategoryDeleteView.as_view(), name='category_delete'),

    # --------------------------------------------------
    # 認証・ユーザーアカウント機能 (Authentication & Account URLs)
    # --------------------------------------------------
    
    # 💡 修正箇所：自作のログアウトビューを一番上に配置（GETリクエスト対応）
    # path内の 'accounts/logout/' を指定することで標準のincludeよりも先にマッチさせます
    path('accounts/logout/', views.logout_view, name='logout'),

    # Django標準の認証URLをインクルード (login, password_reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # ユーザー登録ページ
    path('accounts/register/', UserRegisterView.as_view(), name='register'),
    
    # 登録完了画面
    path('accounts/register/success/', 
            TemplateView.as_view(template_name='registration/registration_success.html'), 
            name='registration_success'),

    # ユーザープロフィール（アカウント情報）編集ページ
    path('accounts/profile/edit/', views.UserUpdateView.as_view(), name='profile_edit'),
    
    # パスワード変更フォーム
    path('accounts/password_change/', 
              auth_views.PasswordChangeView.as_view(
                  template_name='registration/password_change_form.html',
                  success_url=reverse_lazy('password_change_done') 
              ), 
              name='password_change'),
    
    # パスワード変更完了画面
    path('accounts/password_change/done/', 
              auth_views.PasswordChangeDoneView.as_view(
                  template_name='registration/password_change_done.html'
              ), 
              name='password_change_done'),

    # タスク完了切り替え処理
    path('tasks/<int:pk>/complete/', views.task_complete, name='task_complete'),

]