# tasks/forms.py

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django import forms 
from .models import Task, Category 
from django.contrib.auth import get_user_model

# 適切なユーザーモデルを取得
User = get_user_model()

# ==============================================================================
# 1. ユーザー認証フォーム (Authentication Forms)
# ==============================================================================

# ユーザー登録用フォーム
class UserRegisterForm(UserCreationForm):
    """
    Django標準のUserCreationFormを継承し、ユーザー登録に使用するフォーム。
    登録時にユーザー名とメールアドレスの入力を求める。
    """
    class Meta:
        model = User
        # ユーザーに登録させるフィールドを指定
        fields = ('username', 'email')

# ユーザープロフィール編集用フォーム
class UserProfileEditForm(UserChangeForm):
    """
    ログインユーザー自身のプロフィール情報（ユーザー名、メール、氏名など）を編集するためのフォーム。
    セキュリティ上の理由から、パスワード関連フィールドは除外する。
    """
    # UserChangeFormに含まれるパスワードフィールドを意図的に無効化
    password = None 
    
    class Meta:
        model = User
        # ユーザーに編集させたいフィールドを指定（必要に応じて調整）
        fields = ('username', 'email', 'last_name', 'first_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 不要なDjango標準のフィールド（管理用データ）をフォームから削除
        for field_name in ['date_joined', 'last_login', 'is_superuser', 'groups', 'user_permissions', 'is_staff', 'is_active']:
            if field_name in self.fields:
                del self.fields[field_name]

# ==============================================================================
# 2. タスク関連フォーム (Task Forms)
# ==============================================================================

# タスク作成・編集用フォーム
class TaskForm(forms.ModelForm):
    """
    Taskモデルに基づいたフォーム。
    ログインユーザーが所有するカテゴリのみを選択肢として表示するロジックを含む。
    """
    
    def __init__(self, *args, **kwargs):
        # Viewから渡されるリクエストユーザー（'user'）をキーワード引数から取得
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

        # ログインユーザーのカテゴリのみに制限をかける
        if user is not None:
            # Categoryフィールドのクエリセットをフィルタリング
            category_field = self.fields['category']
            # ログインユーザーが作成したカテゴリのみをドロップダウンの選択肢として設定
            category_field.queryset = Category.objects.filter(user=user).order_by('name')
            # カテゴリが未選択の場合のラベルを 'なし' に変更
            category_field.empty_label = 'なし'
            
        # priorityフィールドにCSSクラスを適用（ModelMetaのwidgetsで設定されていない場合に対応）
        if 'priority' in self.fields:
            self.fields['priority'].widget.attrs.update({'class': 'form-select form-select-sm'})

    # 💡 Note: __init__ メソッドがコードに二重定義されていたため、上記で統合しました。
    
    class Meta:
        model = Task
        # フォームに表示するフィールドの順序とリストを定義
        fields = ['title', 'description', 'due_date', 'status', 'category', 'priority']

        labels = {
            'title': 'タイトル',
            'description': '詳細',
            'due_date': '期限',
            'status': '進捗状況',
            'category': 'カテゴリ',
            'priority': '優先度',
        }
        
        # フォームのウィジェットをカスタマイズ（主にBootstrapのCSSクラスを適用）
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            # HTML5の datetime-local ウィジェットを使用し、日付と時刻の入力を容易にする
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}), 
            
            # ドロップダウン/セレクトボックスにBootstrapのクラスを適用
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'category': forms.Select(attrs={'class': 'form-select'}), 
            # priority は __init__ でクラス適用をチェックする
        }

# ==============================================================================
# 3. カテゴリ関連フォーム (Category Forms)
# ==============================================================================

# カテゴリ作成・編集用のフォーム
class CategoryForm(forms.ModelForm):
    """
    Categoryモデルに基づいたフォーム。カテゴリ名のみを入力させる。
    """
    def __init__(self, *args, **kwargs):
        # 'user' キーワード引数を取得する（Viewから渡されるが、このフォーム内では未使用の場合もある）
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # name フィールドに placeholder と CSS クラスを設定
        self.fields['name'].widget.attrs.update({'placeholder': 'カテゴリ名を入力', 'class': 'form-control'})
        
    class Meta:
        model = Category
        # ユーザーが入力するフィールドは 'name' のみ
        fields = ('name',) 
        
        labels = {'name': 'カテゴリ名'}
        
        # ウィジェットのカスタマイズ
        widgets = {
             'name': forms.TextInput(attrs={'placeholder': 'カテゴリ名を入力', 'class': 'form-control'})
        }