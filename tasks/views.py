from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    CreateView, 
    ListView, 
    UpdateView, 
    DeleteView, 
    DetailView, 
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin # ログイン必須を強制するMixin
from django.views import View # カスタムなPOST処理を行うために使用
from django.http import HttpResponseRedirect
from django.utils import timezone # 削除日時を記録するために使用

from .forms import UserRegisterForm, TaskForm, CategoryForm, UserProfileEditForm
from .models import Task, Category
# ORMの複雑なクエリ（Case, When, Qなど）に必要なモジュール
from django.db.models import Case, When, Value, BooleanField, IntegerField, Q 
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as auth_logout


# 認証・ユーザーモデルの取得
User = get_user_model()

# ==============================================================================
# 1. ユーザー認証関連ビュー (Authentication Views)
# ==============================================================================

# ユーザー登録ビュー
class UserRegisterView(CreateView):
    """ユーザー登録フォームを表示し、バリデーションとユーザー作成を行う。"""
    form_class = UserRegisterForm # 使用するフォームを指定
    success_url = reverse_lazy('registration_success') # 登録成功後のリダイレクト先
    template_name = 'registration/register.html' # 使用するテンプレート

# ==============================================================================
# 2. タスク関連ビュー (Task Management Views)
# ==============================================================================

# タスク一覧ビュー (フィルタリング、ソート、検索機能を実装)
class TaskListView(LoginRequiredMixin, ListView):
    """
    ログインユーザーのタスク一覧を表示する。
    URLクエリパラメータに基づいて、フィルタリング、検索、並び替えを行う。
    """
    model = Task
    context_object_name = 'tasks' # テンプレートでアクセスする変数名
    template_name = 'tasks/home.html'
    
    def get_queryset(self):
        """データベースから取得するクエリセットをカスタマイズする。"""
        # 1. 基本クエリ: ログインユーザーが所有し、かつ論理削除されていないタスクのみ
        queryset = Task.objects.filter(
            user=self.request.user, 
            is_deleted=False
        )
        
        # URLクエリパラメータの取得
        category_id = self.request.GET.get('category')
        status_filter = self.request.GET.get('status')
        priority_filter = self.request.GET.get('priority')
        search_query = self.request.GET.get('q')

        # 2. カテゴリフィルタリング
        if category_id:
            if category_id == 'none': # URLに 'category=none' が指定された場合
                queryset = queryset.filter(category__isnull=True) # カテゴリがNULLのタスクをフィルタ
            elif category_id.isdigit():
                queryset = queryset.filter(category__id=category_id) # 特定のカテゴリIDでフィルタ
        
        # 3. 進捗状況フィルタリング
        if status_filter and status_filter.isdigit():
            # URLパラメータは文字列なので、整数に変換してフィルタリング
            queryset = queryset.filter(status=int(status_filter))

        # 4. 優先度フィルタリング
        if priority_filter:
             # 'none', 'low', 'medium', 'high' の文字列でフィルタリング
             queryset = queryset.filter(priority=priority_filter)
        
        # 5. 検索フィルタリング
        if search_query:
            # Qオブジェクトを使用して、タイトル または 詳細 のいずれかにクエリ文字列が含まれるタスクをフィルタ
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            )

        # 6. 並び替えロジックの適用
        sort_key = self.request.GET.get('sort', 'due_date') # デフォルトは期限
        order = self.request.GET.get('order', 'asc') # デフォルトは昇順
        
        # 有効なソートキーのリスト
        valid_sort_keys = {
            'due_date': 'due_date',
            'title': 'title',
            'status': 'status',
            'priority': 'priority',
            'created_at': 'created_at',
        }
        
        # 有効なキーが指定された場合の処理
        if sort_key in valid_sort_keys:
            field_name = valid_sort_keys[sort_key]
            
            # --- 優先度によるカスタムソート処理 (文字列フィールドの順序付け) ---
            if sort_key == 'priority':
                # Case/Whenを使用して、priority文字列を数値 ('high': 3, 'low': 1など) にマッピングするカスタムフィールドを追加
                queryset = queryset.annotate(
                    priority_order=Case(
                        When(priority='high', then=Value(3)),
                        When(priority='medium', then=Value(2)),
                        When(priority='low', then=Value(1)),
                        When(priority='none', then=Value(0)),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                )

                if order == 'asc':
                    # 昇順ソート時: 優先度の低いもの(0)が先頭
                    queryset = queryset.order_by('priority_order', 'due_date', '-created_at')
                else:
                    # 降順ソート時: 優先度の高いもの(3)が先頭
                    queryset = queryset.order_by('-priority_order', 'due_date', '-created_at')
                    
            # --- 期限 (due_date) によるソート処理 (NULL値の扱いを制御) ---
            elif sort_key == 'due_date':
                # NULL値（期限なし）を判別するためのカスタムフラグを付与
                queryset = queryset.annotate(
                    due_date_null=Case(
                        When(due_date__isnull=True, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                )

                if order == 'asc':
                    # 昇順ソート時: 期限なし(True)を最後に持ってくるようにソート
                    queryset = queryset.order_by('due_date_null', 'due_date', '-created_at')
                else:
                    # 降順ソート時: 期限なし(True)を最初に持ってくるようにソート
                    queryset = queryset.order_by('-due_date_null', '-due_date', '-created_at') 
            
            # --- その他のフィールドによるソート処理 ---
            else:
                # 昇順/降順を決定
                if order == 'desc':
                    field_name = '-' + field_name
                
                queryset = queryset.order_by(field_name, '-created_at') 
        else:
            # 無効なソートキーが指定された場合、またはデフォルトソート
            # モデルに定義されたデフォルトのソート順 (due_dateのNULL制御) を適用
            queryset = queryset.annotate(
                due_date_null=Case(
                    When(due_date__isnull=True, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ).order_by('due_date_null', 'due_date', '-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        """テンプレートに渡す追加のコンテキストデータを生成する。"""
        context = super().get_context_data(**kwargs)
        
        # ログインユーザーが作成したカテゴリ一覧を取得し、テンプレートに渡す
        context['categories'] = Category.objects.filter(user=self.request.user).order_by('name')
        
        # 現在適用されているフィルタ/ソート情報を取得し、テンプレートに渡す
        current_category_filter = self.request.GET.get('category')
        context['current_category_filter'] = current_category_filter 

        # 選択されたカテゴリのオブジェクトを取得し、コンテキストに追加
        if current_category_filter and current_category_filter.isdigit():
            try:
                context['selected_category'] = Category.objects.get(
                    pk=current_category_filter, 
                    user=self.request.user 
                )
            except Category.DoesNotExist:
                context['selected_category'] = None
        else:
            context['selected_category'] = None
        
        # タスクの進捗状況の選択肢を渡す
        context['status_choices'] = Task.STATUS_CHOICES 
        context['current_status_filter'] = self.request.GET.get('status')
        
        # 優先度の選択肢と現在のフィルタを渡す
        context['priority_choices'] = Task.PRIORITY_CHOICES
        context['current_priority_filter'] = self.request.GET.get('priority')

        # 現在の検索キーワードを渡す
        context['current_search_query'] = self.request.GET.get('q')

        # テンプレートで使用する並び替え可能なフィールドのキーと表示名を定義
        context['sort_headers'] = {
            'title': 'タスク名', 
            'due_date': '期限', 
            'status': '進捗状況',
            'priority': '優先度',
        }

        # 現在のソート情報をコンテキストに追加
        context['current_sort_key'] = self.request.GET.get('sort', 'due_date')
        context['current_order'] = self.request.GET.get('order', 'asc')
        
        return context

# タスク作成ビュー
class TaskCreateView(LoginRequiredMixin, CreateView): 
    """タスク作成フォームを表示・処理する。"""
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('home') 

    def get_form_kwargs(self):
        """フォーム初期化時にユーザーを渡す（カテゴリ選択肢を絞るため）。"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user 
        return kwargs
    
    def form_valid(self, form):
        """フォームが有効な場合、タスクの所有者（user）をログインユーザーに設定する。"""
        form.instance.user = self.request.user
        return super().form_valid(form)

# タスク編集ビュー
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """タスク編集フォームを表示・処理する。編集対象はログインユーザーのタスクのみに限定される。"""
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    context_object_name = 'task'

    def get_form_kwargs(self):
        """フォーム初期化時にユーザーを渡す。"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user 
        return kwargs
    
    def get_queryset(self):
        """編集対象のタスクを、ログインユーザーが所有し、論理削除されていないタスクに限定する。"""
        return Task.objects.filter(user=self.request.user, is_deleted=False)

    def get_success_url(self):
        """編集成功後のリダイレクト先。タスク詳細画面へ遷移する。"""
        return reverse_lazy('task_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """
        フォームが有効な場合の処理。
        編集画面では複雑なリダイレクトを避け、一貫性を持たせるために
        標準の成功URL（詳細画面）へ遷移させます。
        """
        # 親クラスの form_valid を呼ぶだけで、自動的に get_success_url の先へ飛びます
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """キャンセルボタンの遷移先を制御するためのコンテキストを追加。"""
        context = super().get_context_data(**kwargs)
        
        # HTTP Referer (参照元URL) を取得
        referer = self.request.META.get('HTTP_REFERER')
        
        # Refererが編集画面自身でない場合（前のページである場合）をキャンセル先とする
        if referer and referer != self.request.build_absolute_uri(self.request.path):
            context['cancel_url'] = referer
        else:
            # Refererがない、または不正な場合は、タスク一覧に戻す
            context['cancel_url'] = reverse_lazy('home')
            
        return context

# タスク詳細ビュー
class TaskDetailView(LoginRequiredMixin, DetailView):
    """個々のタスクの詳細を表示する。"""
    model = Task
    context_object_name = 'task' 
    template_name = 'tasks/task_detail.html'
    
    def get_queryset(self):
        """詳細表示するタスクを、ログインユーザーが所有し、論理削除されていないタスクに限定する。"""
        return Task.objects.filter(user=self.request.user, is_deleted=False)

# タスクの進捗状況を更新するビュー (インライン更新用)
class TaskUpdateStatusView(LoginRequiredMixin, View):
    """
    タスク一覧画面などでステータス（進捗状況）を更新するための専用ビュー。
    POSTリクエストのみを受け付け、処理後にタスク一覧へリダイレクトする。
    """
    def post(self, request, pk):
        # 1. タスクオブジェクトを、IDとユーザーをキーに取得
        task = get_object_or_404(Task, pk=pk, user=request.user)
        
        # 2. POSTデータから新しいステータス値とフィルタパラメータを取得
        new_status = request.POST.get('new_status')
        filter_params = request.POST.get('filter_params', '') # リダイレクト時に元のフィルタを復元するため
        
        if new_status is not None:
            try:
                # 3. 整数に変換してステータスを更新
                new_status = int(new_status)
                
                # STATUS_CHOICES内に含まれる値かチェック
                valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
                if new_status in valid_statuses:
                    task.status = new_status
                    task.save()
            except ValueError:
                # 無効な値が渡された場合は無視（エラー処理は省略）
                pass

        # 4. タスク一覧画面へリダイレクト（元のフィルタを付加）
        if filter_params:
            # ベースURL + ? + フィルタパラメータ
            redirect_url = f"{reverse('home')}?{filter_params}"
        else:
            redirect_url = reverse('home')
            
        return redirect(redirect_url)

# タスク削除ビュー（論理削除）
class TaskDeleteView(LoginRequiredMixin, View):
    """
    タスクをデータベースから物理的に削除せず、論理的に削除（ゴミ箱へ移動）する。
    GETリクエストではなくPOSTリクエストで処理を行う。
    """
    def post(self, request, pk):
        # 削除対象のタスクを、IDとユーザーをキーに取得
        task = get_object_or_404(Task, pk=pk, user=request.user)
        
        # 論理削除フラグを True に設定し、削除日時を記録
        task.is_deleted = True
        task.deleted_at = timezone.now()
        task.save()
        
        return HttpResponseRedirect(reverse_lazy('home'))

# ゴミ箱ビュー
class TrashView(LoginRequiredMixin, ListView):
    """論理削除された（is_deleted=True）タスクの一覧を表示する。"""
    model = Task
    context_object_name = 'tasks'
    template_name = 'tasks/trash.html'

    def get_queryset(self):
        """ログインユーザーが所有し、論理削除されているタスクのみを取得する。"""
        return Task.objects.filter(user=self.request.user, is_deleted=True).order_by('-deleted_at') # 削除日時が新しい順

# タスク復元ビュー
class TaskRestoreView(LoginRequiredMixin, View):
    """ゴミ箱にあるタスクを復元（is_deleted=Falseに戻す）する。"""
    def post(self, request, pk):
        # 復元対象のタスクを、IDとユーザーをキーに取得
        task = get_object_or_404(Task, pk=pk, user=request.user)
        
        # 論理削除フラグを False に戻し、削除日時をクリア
        task.is_deleted = False
        task.deleted_at = None 
        task.save()
        
        return HttpResponseRedirect(reverse_lazy('trash'))

# タスク一括物理削除ビュー
class TaskBulkDeleteView(LoginRequiredMixin, View):
    """ゴミ箱内のタスクを永続的に（物理的に）削除する。"""
    def post(self, request):
        # POSTデータから、チェックされたタスクIDのリストを取得
        task_ids = request.POST.getlist('task_ids') 
        
        # ログインユーザーが所有し、論理削除されているタスクのみを対象とするベースクエリ
        queryset = Task.objects.filter(
            user=request.user, 
            is_deleted=True
        )
        
        if task_ids:
            # 特定のIDリストに含まれるタスクのみを物理削除
            queryset.filter(pk__in=task_ids).delete()
        else:
            # task_idsがない場合、ゴミ箱内の全タスクを物理削除
            queryset.delete()
        
        return HttpResponseRedirect(reverse_lazy('trash'))

# ==============================================================================
# 3. カテゴリ関連ビュー (Category Management Views)
# ==============================================================================

# カテゴリ一覧ビュー
class CategoryListView(LoginRequiredMixin, ListView):
    """ログインユーザーが作成したカテゴリの一覧を表示する（カテゴリ管理画面）。"""
    model = Category
    context_object_name = 'categories'
    template_name = 'tasks/category_list.html' 

    def get_queryset(self):
        """ログインユーザーが所有するカテゴリのみを取得する。"""
        return Category.objects.filter(user=self.request.user)
    
# カテゴリ作成ビュー
class CategoryCreateView(LoginRequiredMixin, CreateView):
    """カテゴリ作成フォームを表示・処理する。"""
    model = Category
    form_class = CategoryForm
    template_name = 'tasks/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def get_form_kwargs(self):
        """フォームにユーザーを渡す（フォーム側で重複チェックなどに利用）。"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """カテゴリ保存前に、所有者設定と重複チェックを行う。"""
        form.instance.user = self.request.user
        
        # 重複チェック
        if Category.objects.filter(
            user=self.request.user, 
            name=form.cleaned_data['name']
        ).exists():
            form.add_error('name', 'この名前のカテゴリは既に存在します。')
            return self.form_invalid(form)
            
        # 保存処理を実行
        response = super().form_valid(form)
        
        # 保存成功後、nextパラメータがあればそちらへ優先的にリダイレクト
        next_url = self.request.POST.get('next')
        if next_url:
            return HttpResponseRedirect(next_url)
            
        return response

    def get_context_data(self, **kwargs):
        """テンプレートに渡す変数を設定。"""
        context = super().get_context_data(**kwargs)
        
        # URLパラメータまたはPOSTデータから next を取得し、テンプレートに渡す
        # (キャンセルボタンや hidden フィールドで使用)
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        
        # nextがない場合はデフォルトのカテゴリ一覧を戻り先にする
        context['next_url'] = next_url if next_url else reverse_lazy('category_list')
        return context

# カテゴリ編集（名前変更）用ビュー
class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """カテゴリの名前編集フォームを表示・処理する。"""
    model = Category
    form_class = CategoryForm
    template_name = 'tasks/category_form.html'
    success_url = reverse_lazy('category_list')

    def get_form_kwargs(self):
        """フォームにユーザーを渡す。"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        """編集対象を、ログインユーザーが所有するカテゴリに限定する。"""
        return self.model.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        """カテゴリ更新時に、他のカテゴリとの名前の重複をチェックする。"""
        category = form.instance
        new_name = form.cleaned_data['name']
        
        # 編集対象のカテゴリ（自分自身）を除外し、同じユーザーが同じ名前のカテゴリを持っているかチェック
        if Category.objects.filter(
            user=self.request.user, 
            name=new_name
        ).exclude(pk=category.pk).exists():
            form.add_error('name', 'この名前のカテゴリは既に存在します。')
            return self.form_invalid(form)
            
        return super().form_valid(form)

# カテゴリ削除ビュー
class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """カテゴリの削除確認画面を表示し、削除処理を行う。"""
    model = Category
    success_url = reverse_lazy('category_list') 
    template_name = 'tasks/category_confirm_delete.html' 

    def get_queryset(self):
        """削除対象を、ログインユーザーが所有するカテゴリに限定する。"""
        return Category.objects.filter(user=self.request.user)

# ==============================================================================
# 4. ユーザーアカウント編集関連ビュー (User Account Views)
# ==============================================================================

# ユーザープロフィール（アカウント情報）編集ビュー
class UserUpdateView(LoginRequiredMixin, UpdateView):
    """ログインユーザー自身のプロフィール情報を編集する。"""
    model = User
    form_class = UserProfileEditForm
    template_name = 'registration/profile_edit.html' 
    success_url = reverse_lazy('profile_edit') # 編集成功後、編集ページに留まる

    def get_object(self, queryset=None):
        """編集対象を、リクエストを行ったログインユーザー自身に設定する。"""
        return self.request.user

    def get_success_url(self):
        """編集成功後は、プロフィール編集ページに戻る。"""
        return reverse_lazy('profile_edit')
    
# ★★★ この関数を追記・修正 ★★★
def task_complete(request, pk):
    """
    指定されたID (pk) のタスクのステータスを「完了」(status=2) に設定し、一覧ページにリダイレクトする。
    """
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    # POSTリクエストであることを前提として処理
    if request.method == 'POST':
        task.status = 2 # 完了ステータス (models.pyで定義した2)
        task.save()
        return redirect('home')
    
    # POST以外でアクセスされた場合も一覧へリダイレクト
    return redirect('home')

def logout_view(request):
    auth_logout(request)
    return redirect('login') # 'login' はログイン画面のURL名