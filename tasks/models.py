# tasks/models.py

from django.db import models
from django.contrib.auth import get_user_model

# ユーザーモデルを取得する（カスタムユーザーモデルに将来変更されても対応可能）
User = get_user_model() 


# ==============================================================================
# 1. カテゴリモデル (Category Model)
# ==============================================================================
class Category(models.Model):
    """
    タスクを分類するためのカテゴリを定義するモデル。
    各カテゴリは特定のユーザーに紐づく。
    """
    # カテゴリ名 (例: 仕事、プライベート)。最大長を190文字に設定。
    name = models.CharField(max_length=190)
    
    # ユーザーとカテゴリを関連付け（ForeignKey）。
    # on_delete=models.CASCADE: ユーザーが削除されたら、そのユーザーが作成したカテゴリも同時に削除される。
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        """オブジェクトの文字列表現を返す（Django管理画面などで使用）。"""
        return self.name
    
    class Meta:
        # Django管理画面でのモデル表示名を指定
        verbose_name_plural = 'カテゴリ'
        # userとnameの組み合わせをユニークにする（同じユーザーが同じカテゴリ名を複数作成できないようにする）
        unique_together = ('user', 'name')


# ==============================================================================
# 2. タスクモデル (Task Model)
# ==============================================================================
class Task(models.Model):
    """
    個々のタスク情報を格納するモデル。
    進捗状況、優先度、期限、カテゴリ、論理削除フラグを含む。
    """
    
    # --- 定数定義 ---
    
    # 進捗状況の選択肢を定義 (DBには数値、表示には文字列を使用)
    STATUS_CHOICES = [
        (0, '未着手'),
        (1, '進行中'),
        (2, '完了'),
    ]

    # 優先度の選択肢を定義
    PRIORITY_CHOICES = [
        ('none', 'なし'),
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    ]
    
    # --- リレーション ---
    
    # ユーザーとの関連付け (Taskは必ずユーザーに紐づく)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # カテゴリとの関連付け (タスクはカテゴリを持たなくても良い)
    # on_delete=models.SET_NULL: カテゴリが削除されても、タスクのカテゴリフィールドはNULLになるだけで、タスク自体は残る。
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True,      # DBでNULLを許可
        blank=True,     # フォームで空入力を許可
        verbose_name='カテゴリ'
    ) 

    # --- 基本情報 ---
    
    title = models.CharField(max_length=200, verbose_name='タイトル')
    # 詳細（任意入力、長文）
    description = models.TextField(blank=True, null=True, verbose_name='詳細') 
    
    # --- 状態管理 ---
    
    # 優先度フィールド
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='none', 
        verbose_name='優先度'
    )

    # タスクの進捗状況 (STATUS_CHOICESから選択)
    status = models.IntegerField(
        choices=STATUS_CHOICES, 
        default=0, # デフォルトは「未着手」
        verbose_name='進捗状況' 
    ) 
    
    # 期限 (任意入力)
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='期限') 
    
    # --- 論理削除 (ソフトデリート) 機能 ---
    
    # 論理削除フラグ: True ならゴミ箱行き（ユーザーには非表示）
    is_deleted = models.BooleanField(default=False) 
    # 削除日時: 論理削除が行われた時刻を記録
    deleted_at = models.DateTimeField(null=True, blank=True) 

    # --- 追跡用タイムスタンプ ---
    
    # 作成日時 (オブジェクト作成時に自動で設定)
    created_at = models.DateTimeField(auto_now_add=True)
    # 更新日時 (オブジェクトが保存される度に自動で更新)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # デフォルトのソート順を設定
        # 1. 'due_date' (期限が近い順に並ぶ)
        # 2. '-created_at' (期限が同じ場合は新しいタスクが上に来る)
        ordering = ['due_date', '-created_at'] 
        
    def __str__(self):
        """オブジェクトの文字列表現としてタイトルを返す。"""
        return self.title