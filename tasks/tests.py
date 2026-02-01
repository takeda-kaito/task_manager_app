"""
tasksアプリケーションのモデル、ビュー、認証に関するテストスイート。
BaseTestクラスで共通のテストデータをセットアップし、各テストクラスで機能を検証する。
"""
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
    テストクラス間で共有される共通のセットアップを定義する基底クラス。
    認証ユーザー、カテゴリ、様々な状態のタスクなどの初期データを準備する (Arrange)。
    """
    def setUp(self):
        """テスト実行前の初期設定"""
        self.client = Client()
        
        # 認証ユーザーの作成とログイン処理
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        # カテゴリの作成
        self.category_work = Category.objects.create(name='仕事', user=self.user)
        self.category_private = Category.objects.create(name='プライベート', user=self.user)
        
        # テスト用タスクの作成 (未着手, 未削除)
        self.task_active = Task.objects.create(
            user=self.user,
            title='アクティブなタスク',
            category=self.category_work,
            priority='high',
            due_date=timezone.now() + datetime.timedelta(days=5),
            status=0,         # status=0 は未着手
        )
        # テスト用タスクの作成 (完了済み, 未削除)
        self.task_completed = Task.objects.create(
            user=self.user,
            title='完了したタスク',
            category=self.category_work,
            priority='medium',
            status=2,         # status=2 は完了
        )
        # テスト用タスクの作成 (削除済み/ゴミ箱)
        self.task_deleted = Task.objects.create(
            user=self.user,
            title='削除されたタスク',
            category=self.category_private,
            priority='low',
            status=0,
            is_deleted=True,  # 論理削除フラグを設定
            deleted_at=timezone.now() # 削除日時を設定
        )


class TaskModelTest(BaseTest):
    """Taskモデルの属性とメソッドに関するテスト"""

    def test_task_creation(self):
        """タスクが正しく作成され、属性が設定されるかテスト (Assert)"""
        # データベースにタスクが作成されたことを確認
        self.assertTrue(Task.objects.filter(title='アクティブなタスク').exists())
        # 属性が正しく設定されていることを確認 (priorityは文字列で保存されることを想定)
        self.assertEqual(self.task_active.priority, 'high')
        self.assertEqual(self.task_active.category.name, '仕事')


class CategoryModelTest(BaseTest):
    """Categoryモデルの属性と関連に関するテスト"""
    
    def test_category_creation(self):
        """カテゴリが正しく作成され、タスクと紐づいているかテスト (Assert)"""
        # カテゴリが存在することを確認
        self.assertTrue(Category.objects.filter(name='仕事').exists())
        # '仕事'カテゴリに紐づくタスク数を確認 (task_active と task_completed の2つ)
        self.assertEqual(self.category_work.task_set.count(), 2)

    def test_category_str_representation(self):
        """__str__ メソッドがカテゴリ名を返すことを確認 (Assert)"""
        self.assertEqual(str(self.category_private), 'プライベート')


class TaskViewTest(BaseTest):
    """タスク関連ビュー（home, create, complete, delete）の動作テスト"""

    def test_home_view_status_code_and_content(self):
        """タスク一覧 (home) へのアクセスが成功し、未削除のタスクのみが表示されるか"""
        # Act: homeビューにアクセス
        response = self.client.get(reverse('home'))
        # Assert: ステータスコードと使用テンプレートを確認
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/home.html')
        
        # Assert: アクティブなタスクと完了したタスクが表示されることを確認
        self.assertContains(response, 'アクティブなタスク')
        self.assertContains(response, '完了したタスク')
        # Assert: 削除されたタスクは表示されないことを確認
        self.assertNotContains(response, '削除されたタスク')

    def test_task_create_and_redirect(self):
        """タスクの新規作成とリダイレクトのテスト"""
        # Arrange: 必須フィールドを含むPOSTデータを準備
        post_data = {
            'title': '新規タスクのテスト', 
            'category': self.category_work.pk, # 有効なCategoryのPKを渡す
            'priority': 'medium', 
            'status': 0, # 未着手
            # 'due_date' など、他の必須フィールドがあればここに追加
        }

        # Act: タスク作成ビューにPOSTリクエストを送信
        response = self.client.post(reverse('task_create'), data=post_data)

        # Assert: リダイレクト先がhomeビューであることを確認 (ステータスコード302)
        self.assertRedirects(response, reverse('home'))
        # Assert: データベースにタスクが作成されたことを確認
        self.assertTrue(Task.objects.filter(title='新規タスクのテスト').exists())

    def test_task_complete(self):
        """タスク完了処理のテスト (論理完了)"""
        # Arrange: 完了前の状態が未着手(0)であることを確認
        self.assertEqual(self.task_active.status, 0) 
        
        # Act: 完了処理ビューにPOSTリクエストを送信
        response = self.client.post(reverse('task_complete', args=[self.task_active.pk]))
        # Assert: homeビューにリダイレクトされたことを確認
        self.assertRedirects(response, reverse('home'))
        
        # Assert: データベースのステータスが 2 (完了) になっているか確認
        self.task_active.refresh_from_db()
        self.assertEqual(self.task_active.status, 2)

    def test_task_delete_soft(self):
        """タスク削除処理のテスト (論理削除)"""
        # Arrange: 削除前はis_deletedがFalseであることを確認
        self.assertFalse(self.task_active.is_deleted)
        
        # Act: 削除処理ビューにPOSTリクエストを送信
        response = self.client.post(reverse('task_delete', args=[self.task_active.pk]))
        # Assert: homeビューにリダイレクトされたことを確認
        self.assertRedirects(response, reverse('home'))
        
        # Assert: データベースで is_deleted が True および deleted_at が設定されているか確認
        self.task_active.refresh_from_db()
        self.assertTrue(self.task_active.is_deleted)
        self.assertIsNotNone(self.task_active.deleted_at)


class CategoryViewTest(BaseTest):
    """カテゴリ関連ビュー（一覧, 作成, 編集, 削除）の動作テスト"""
    
    def test_category_list_view(self):
        """カテゴリ一覧ページへのアクセスと内容の確認"""
        # Act: カテゴリ一覧ビューにアクセス
        response = self.client.get(reverse('category_list'))
        # Assert: ステータスコードと使用テンプレートを確認
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/category_list.html')
        
        # Assert: task_set.count が正しく表示されているか確認 (仕事: 2, プライベート: 1)
        # HTMLの厳密なタグ構造に依存せず、タスク数が含まれていることをチェック
        self.assertContains(response, '2')
        self.assertContains(response, '1')
        
    def test_category_create(self):
        """カテゴリ新規作成のテスト"""
        # Act: カテゴリ作成ビューにPOSTリクエストを送信
        response = self.client.post(reverse('category_create'), {'name': '新規カテゴリ'})
        # Assert: リダイレクトとデータベースへの保存を確認
        self.assertRedirects(response, reverse('category_list'))
        self.assertTrue(Category.objects.filter(name='新規カテゴリ').exists())
        
    def test_category_update(self):
        """カテゴリ編集のテスト"""
        # Act: カテゴリ編集ビューにPOSTリクエストを送信
        response = self.client.post(reverse('category_update', args=[self.category_work.pk]), {
            'name': 'Updated Work'
        })
        # Assert: リダイレクトとデータベースの更新を確認
        self.assertRedirects(response, reverse('category_list'))
        self.category_work.refresh_from_db()
        self.assertEqual(self.category_work.name, 'Updated Work')
        
    def test_category_delete(self):
        """カテゴリ削除のテスト（カテゴリ削除時のタスクへの影響も確認）"""
        # Arrange: 削除前の関連タスク数を確認
        self.assertEqual(self.category_work.task_set.count(), 2)
        
        # Act: カテゴリ削除ビューにPOSTリクエストを送信
        response = self.client.post(reverse('category_delete', args=[self.category_work.pk]))
        # Assert: リダイレクトを確認
        self.assertRedirects(response, reverse('category_list'))
        
        # Assert: Categoryモデルがデータベースから物理削除されているか確認
        self.assertFalse(Category.objects.filter(pk=self.category_work.pk).exists())
        
        # Assert: 外部キー制約 (on_delete=SET_NULLを想定) の動作確認
        self.task_active.refresh_from_db()
        self.assertIsNone(self.task_active.category)


class TrashViewTest(BaseTest):
    """ゴミ箱関連ビュー（一覧, 復元, 完全削除）の動作テスト"""
    
    def test_trash_view_content(self):
        """ゴミ箱ページに削除済みタスクのみが表示されるか"""
        # Act: ゴミ箱ビューにアクセス
        response = self.client.get(reverse('trash'))
        # Assert: ステータスコードを確認
        self.assertEqual(response.status_code, 200)
        
        # Assert: 削除済みタスクが表示されることを確認
        self.assertContains(response, '削除されたタスク')
        # Assert: アクティブなタスクは表示されないことを確認
        self.assertNotContains(response, 'アクティブなタスク')

    def test_task_restore(self):
        """タスク復元処理のテスト"""
        # Arrange: 削除済み状態であることを確認
        self.assertTrue(self.task_deleted.is_deleted)
        
        # Act: 復元処理ビューにPOSTリクエストを送信
        response = self.client.post(reverse('task_restore', args=[self.task_deleted.pk]))
        # Assert: ゴミ箱 (trash) にリダイレクトされたことを確認
        self.assertRedirects(response, reverse('trash')) 
        
        # Assert: データベースで is_deleted が False になっているか確認
        self.task_deleted.refresh_from_db()
        self.assertFalse(self.task_deleted.is_deleted)
        self.assertIsNone(self.task_deleted.deleted_at)

    def test_task_bulk_delete(self):
        """タスク完全削除 (パージ) 処理のテスト"""
        
        # Act: 削除済みタスクのPKを渡して一括削除 (物理削除) を実行
        response = self.client.post(reverse('task_bulk_delete'), {'task_ids': [self.task_deleted.pk]})
        # Assert: ゴミ箱 (trash) にリダイレクトされたことを確認
        self.assertRedirects(response, reverse('trash'))
        
        # Assert: タスクがデータベースから完全に削除されたことを確認
        self.assertFalse(Task.objects.filter(pk=self.task_deleted.pk).exists())


class AuthenticationTest(TestCase):
    """認証と権限のテスト（ログイン不要の基底クラスとは分離）"""
    
    def setUp(self):
        """テスト実行前の初期設定（ログインしないユーザーを作成）"""
        # ログイン処理を行わないため、Clientの作成は個別のテストメソッドで行う
        self.user = User.objects.create_user(username='testuser', password='password')
        
    def test_login_required(self):
        """ログインしていないユーザーは認証が必要なビューにリダイレクトされるかテスト"""
        client = Client()
        # 認証が必要なビューのURLリスト
        protected_urls = [
            reverse('home'),
            reverse('task_create'),
            reverse('trash'),
            reverse('category_list'),
        ]
        
        # Act & Assert: 各URLへのアクセスをテスト
        for url in protected_urls:
            response = client.get(url)
            self.assertEqual(response.status_code, 302) # リダイレクトステータスコード
            # リダイレクト先がログインページであることを確認 (nextパラメータを含む)
            self.assertRedirects(response, f'{reverse("login")}?next={url}')