"""example/ ブログアプリの Playwright E2E テスト。

事前条件: サンプルアプリが起動していること (デフォルト http://localhost:8080)。

    cd example && docker compose up -d --build --wait
    uv run pytest example/e2e -v

接続先は環境変数 E2E_BASE_URL で変更できる。
"""

from playwright.sync_api import Page, expect


def test_index_shows_posts(page: Page, base_url: str):
    """トップページが表示され、シード記事が一覧に出る。"""
    page.goto(base_url)
    expect(page).to_have_title("記事一覧 | ddb_single Blog")
    expect(page.locator("article.card").first).to_be_visible()
    expect(page.get_by_text("Single-Table Design 入門")).to_be_visible()


def test_create_post_and_author_relation(page: Page, base_url: str, create_post, unique_suffix: str):
    """記事を作成すると詳細ページに遷移し、著者リレーション・逆参照が機能する。"""
    title = f"E2E 記事 {unique_suffix}"
    author = f"E2E著者{unique_suffix}"
    create_post(title, author)

    # 詳細ページ: 著者リレーション (Post -> User) がリンク表示される
    author_link = page.locator(".meta a", has_text=author)
    expect(author_link).to_be_visible()

    # 著者ページ: 逆参照 (User <- Post) で記事が一覧に出る
    author_link.click()
    expect(page.locator("h1")).to_have_text(author)
    expect(page.get_by_text(f"{author} さんの記事 (1)")).to_be_visible()
    expect(page.get_by_role("link", name=title)).to_be_visible()

    # 著者一覧にも自動作成された著者が出る
    page.goto(f"{base_url}/authors")
    expect(page.get_by_role("link", name=author)).to_be_visible()


def test_search_posts_by_title(page: Page, base_url: str, create_post, unique_suffix: str):
    """タイトルの contains 検索でヒットし、ヒットしない語では 0 件になる。"""
    title = f"検索対象 {unique_suffix}"
    create_post(title, f"検索著者{unique_suffix}")

    page.goto(base_url)
    page.fill("input[name=q]", unique_suffix)
    page.click(".searchbar button")
    expect(page.get_by_text("検索結果: 1 件")).to_be_visible()
    expect(page.get_by_role("link", name=title)).to_be_visible()

    page.fill("input[name=q]", f"存在しない語{unique_suffix}")
    page.click(".searchbar button")
    expect(page.get_by_text("検索結果: 0 件")).to_be_visible()


def test_add_comment(page: Page, base_url: str, create_post, unique_suffix: str):
    """記事にコメントを投稿すると詳細ページに反映される (Comment -> Post リレーション)。"""
    create_post(f"コメント先 {unique_suffix}", f"コメ著者{unique_suffix}")

    expect(page.get_by_text("コメント (0)")).to_be_visible()
    page.fill("#author_name", f"コメンター{unique_suffix}")
    page.fill("#body", "E2E からのコメントです！")
    page.click("form[action$='/comments'] button[type=submit]")

    expect(page.get_by_text("コメント (1)")).to_be_visible()
    expect(page.get_by_text("E2E からのコメントです！")).to_be_visible()
    expect(page.get_by_text(f"コメンター{unique_suffix}")).to_be_visible()


def test_delete_post_with_comments(page: Page, base_url: str, create_post, unique_suffix: str):
    """記事を削除すると一覧から消え、詳細ページは 404 になる。"""
    title = f"削除対象 {unique_suffix}"
    post_url = create_post(title, f"削除著者{unique_suffix}")

    # コメントも付けてから削除 (コメント連鎖削除の動作確認)
    page.fill("#body", "この記事は消えます")
    page.click("form[action$='/comments'] button[type=submit]")
    expect(page.get_by_text("コメント (1)")).to_be_visible()

    page.once("dialog", lambda dialog: dialog.accept())
    page.click("form[action$='/delete'] button")

    # 一覧にリダイレクトされ、記事が消えている
    expect(page).to_have_title("記事一覧 | ddb_single Blog")
    expect(page.get_by_role("link", name=title)).not_to_be_visible()

    # 詳細ページは 404
    response = page.goto(post_url)
    assert response is not None and response.status == 404
