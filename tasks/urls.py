# tasks/urls.py

from django.urls import path
from . import views # tasksアプリのビュー（tasks/views.py）をインポート

# ==============================================================================
# URL Patterns (タスクアプリケーション固有のURL定義)
# 📝 注意: これらのURLは、config/urls.py で include されるパスの続きとなる
# ==============================================================================

urlpatterns = [
    # タスク一覧 (Home)
    # 例: config/urls.py で path('', include('tasks.urls')) とあれば、このパスは '/' になる
    path('', views.TaskListView.as_view(), name='home'), 
    
    # タスク作成
    path('create/', views.TaskCreateView.as_view(), name='task_create'),
    
    # タスク編集 (タスクID <pk> をURLパラメータとして受け取る)
    path('<int:pk>/update/', views.TaskUpdateView.as_view(), name='task_update'),
    
    # タスク削除（ソフトデリートを実行。タスクID <pk> を受け取る）
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    
    # ゴミ箱一覧（論理削除されたタスクを表示）
    path('trash/', views.TrashView.as_view(), name='trash'),
    
    # タスク復元 (ゴミ箱内のタスクを指定ID <pk> で復元)
    path('trash/<int:pk>/restore/', views.TaskRestoreView.as_view(), name='task_restore'),
    
    # タスク一括物理削除 (チェックされたタスク、またはゴミ箱内の全てのタスクを完全に削除)
    path('trash/bulk-delete/', views.TaskBulkDeleteView.as_view(), name='task_bulk_delete'),
]