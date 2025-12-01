from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

from .models import Task, Category

# 認証済みユーザーが必要なビューをテストするために、Userモデルを取得
User = get_user_model()


class BaseTest(TestCase):
    """
    テストクラス間で共有される共通のセットアップとヘルパーメソッドを定義
    """
    def setUp(self):
        self.client = Client()
        
        # ★★★ 修正1: create_userを使い、毎回ユーザーを確実に作成する (get_or_createを削除) ★★★
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        # ★★★ 修正2: カテゴリもcreateに戻す (get_or_createを削除) ★★★
        self.category_work = Category.objects.create(name='仕事', user=self.user)
        self.category_private = Category.objects.create(name='プライベート', user=self.user)
        
        # テスト用タスクの作成 (未着手, 未削除)
        self.task_active = Task.objects.create(
            user=self.user,
            title='アクティブなタスク',
            category=self.category_work,
            priority='high',
            due_date=timezone.now() + datetime.timedelta(days=5),
            status=0,        # 未着手
            # is_deleted=False や deleted_at=None はデフォルトに任せる
        )
        # テスト用タスクの作成 (完了済み, 未削除)
        self.task_completed = Task.objects.create(
            user=self.user,
            title='完了したタスク',
            category=self.category_work,
            priority='medium',
            status=2,         # 完了
            # is_deleted=False や deleted_at=None はデフォルトに任せる
        )
        # テスト用タスクの作成 (削除済み)
        self.task_deleted = Task.objects.create(
            user=self.user,
            title='削除されたタスク',
            category=self.category_private,
            priority='low',
            status=0,
            is_deleted=True, # 削除済み
            deleted_at=timezone.now()
        )


class TaskModelTest(BaseTest):
    """Taskモデルのテスト"""

    def test_task_creation(self):
        """タスクが正しく作成され、属性が設定されるかテスト"""
        # データベースにタスクが作成されたことを確認
        self.assertTrue(Task.objects.filter(title='アクティブなタスク').exists())
        # 属性が正しく設定されていることを確認
        # ★★★ 修正: 数値の '1' ではなく、文字列の 'high' と比較 ★★★
        self.assertEqual(self.task_active.priority, 'high')
        self.assertEqual(self.task_active.category.name, '仕事')
        # データベースにタスクが作成されたことを確認


class CategoryModelTest(BaseTest):
    """Categoryモデルのテスト"""
    
    def test_category_creation(self):
        """カテゴリが正しく作成され、タスクと紐づいているかテスト"""
        # カテゴリが存在することを確認
        self.assertTrue(Category.objects.filter(name='仕事').exists())
        # タスク数を確認 (task_active と task_completed の2つ)
        self.assertEqual(self.category_work.task_set.count(), 2)

    def test_category_str_representation(self):
        """__str__ メソッドがカテゴリ名を返すことを確認"""
        self.assertEqual(str(self.category_private), 'プライベート')


class TaskViewTest(BaseTest):
    """タスク関連ビューの動作テスト"""

    def test_home_view_status_code_and_content(self):
        """タスク一覧 (home) へのアクセスが成功し、未削除のタスクのみが表示されるか"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/home.html')
        
        # アクティブなタスクと完了したタスク（is_deleted=False）が表示されることを確認
        self.assertContains(response, 'アクティブなタスク')
        self.assertContains(response, '完了したタスク')
        # 削除されたタスクは表示されないことを確認
        self.assertNotContains(response, '削除されたタスク')

    def test_task_create_and_redirect(self):
        """タスクの新規作成とリダイレクトのテスト"""
        post_data = {
            'title': '新規タスクのテスト', 
            'category': self.category_work.pk, 
            'priority': 'medium', 
            # 🌟 修正箇所: status (状態) フィールドを追加
            'status': 0, 
            # 'due_date' が必須の場合は、'due_date': timezone.now().strftime('%Y-%m-%d'), なども追加
        }

        response = self.client.post(reverse('task_create'), data=post_data)

        # assertRedirects はそのまま
        self.assertRedirects(response, reverse('home'))
        # データベースにタスクが作成されたことを確認 (これで成功するはず)
        self.assertTrue(Task.objects.filter(title='新規タスクのテスト').exists())

    def test_task_complete(self):
        """タスク完了処理のテスト (論理完了)"""
        # ★★★ 修正: is_completed -> status。未完了(0)であることを確認 ★★★
        self.assertEqual(self.task_active.status, 0) 
        
        # ... (POST処理はそのまま) ...
        response = self.client.post(reverse('task_complete', args=[self.task_active.pk]))
        self.assertRedirects(response, reverse('home'))
        
        # データベースで status が 2 (完了) になっているか確認
        self.task_active.refresh_from_db()
        # ★★★ 修正: self.assertTrue(self.task_active.is_completed) -> status=2 であることを確認 ★★★
        self.assertEqual(self.task_active.status, 2)

    def test_task_delete_soft(self):
        """タスク削除処理のテスト (論理削除)"""
        self.assertFalse(self.task_active.is_deleted)
        
        response = self.client.post(reverse('task_delete', args=[self.task_active.pk]))
        self.assertRedirects(response, reverse('home'))
        
        # データベースで is_deleted が True になっているか確認
        self.task_active.refresh_from_db()
        self.assertTrue(self.task_active.is_deleted)
        # deleted_at が設定されているか確認
        self.assertIsNotNone(self.task_active.deleted_at)


class CategoryViewTest(BaseTest):
    """カテゴリ関連ビューの動作テスト"""
    
    def test_category_list_view(self):
        """カテゴリ一覧ページへのアクセスと内容の確認"""
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/category_list.html')
        
        # ★★★ 削除しました: setUpで作成済みのデータを使用します ★★★
        
        # task_set.count が正しく表示されているか確認 (仕事: 2, プライベート: 1 (削除済タスク))
        self.assertContains(response, '2')
        self.assertContains(response, '1')
        
    def test_category_create(self):
        """カテゴリ新規作成のテスト"""
        response = self.client.post(reverse('category_create'), {'name': '新規カテゴリ'})
        self.assertRedirects(response, reverse('category_list'))
        self.assertTrue(Category.objects.filter(name='新規カテゴリ').exists())
        
    def test_category_update(self):
        """カテゴリ編集のテスト"""
        response = self.client.post(reverse('category_update', args=[self.category_work.pk]), {
            'name': 'Updated Work'
        })
        self.assertRedirects(response, reverse('category_list'))
        self.category_work.refresh_from_db()
        self.assertEqual(self.category_work.name, 'Updated Work')
        
    def test_category_delete(self):
        """カテゴリ削除 (論理削除/物理削除の設定による) のテスト"""
        # 削除前のタスク数を確認 (仕事カテゴリに紐づくタスクは2つ)
        self.assertEqual(self.category_work.task_set.count(), 2)
        
        response = self.client.post(reverse('category_delete', args=[self.category_work.pk]))
        self.assertRedirects(response, reverse('category_list'))
        
        # Categoryモデルが削除されているか確認
        self.assertFalse(Category.objects.filter(pk=self.category_work.pk).exists())
        
        # 外部キー制約 (on_delete) の動作確認
        # TaskモデルのCategoryフィールドがSET_NULLであれば、タスクは残る
        self.task_active.refresh_from_db()
        self.assertIsNone(self.task_active.category)


class TrashViewTest(BaseTest):
    """ゴミ箱関連ビューの動作テスト"""
    
    def test_trash_view_content(self):
        """ゴミ箱ページに削除済みタスクのみが表示されるか"""
        response = self.client.get(reverse('trash'))
        self.assertEqual(response.status_code, 200)
        
        # 削除済みタスクが表示されることを確認
        self.assertContains(response, '削除されたタスク')
        # アクティブなタスクは表示されないことを確認
        self.assertNotContains(response, 'アクティブなタスク')

    def test_task_restore(self):
        """タスク復元処理のテスト"""
        self.assertTrue(self.task_deleted.is_deleted)
        
        response = self.client.post(reverse('task_restore', args=[self.task_deleted.pk]))
        self.assertRedirects(response, reverse('trash')) # 復元後はゴミ箱 (trash) にリダイレクトが想定される
        
        # データベースで is_deleted が False になっているか確認
        self.task_deleted.refresh_from_db()
        self.assertFalse(self.task_deleted.is_deleted)
        self.assertIsNone(self.task_deleted.deleted_at)

    def test_task_bulk_delete(self):
        """タスク完全削除 (パージ) 処理のテスト"""
        
        # 削除済みタスクのPKを渡して一括削除
        response = self.client.post(reverse('task_bulk_delete'), {'task_ids': [self.task_deleted.pk]})
        self.assertRedirects(response, reverse('trash'))
        
        # タスクがデータベースから完全に削除されたことを確認
        self.assertFalse(Task.objects.filter(pk=self.task_deleted.pk).exists())


class AuthenticationTest(TestCase):
    """認証と権限のテスト"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        
    def test_login_required(self):
        """ログインしていないユーザーは認証が必要なビューにリダイレクトされるかテスト"""
        client = Client()
        # 認証が必要なビューのURL
        protected_urls = [
            reverse('home'),
            reverse('task_create'),
            reverse('trash'),
            reverse('category_list'),
        ]
        
        # 各URLへのアクセスをテスト
        for url in protected_urls:
            response = client.get(url)
            self.assertEqual(response.status_code, 302)
            # リダイレクト先がログインページであることを確認
            self.assertRedirects(response, f'{reverse("login")}?next={url}')