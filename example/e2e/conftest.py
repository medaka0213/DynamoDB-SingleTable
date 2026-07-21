import os
import uuid

import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def base_url() -> str:
    # pytest-playwright (pytest-base-url) の同名 fixture を上書きし、
    # 接続先を環境変数 E2E_BASE_URL で指定できるようにする
    return BASE_URL


@pytest.fixture
def unique_suffix() -> str:
    """テスト間・再実行間でデータが衝突しないよう、一意な接尾辞を発行する。"""
    return uuid.uuid4().hex[:8]


@pytest.fixture
def create_post(page: Page, base_url: str):
    """UI 経由で記事を作成し、(タイトル, 著者名, 記事詳細 URL) を返すヘルパ。"""

    def _create(title: str, author: str, content: str = "E2E テスト本文です。") -> str:
        page.goto(f"{base_url}/posts/new")
        page.fill("#title", title)
        page.fill("#author_name", author)
        page.fill("#content", content)
        page.click("button[type=submit]")
        expect(page.locator("h1")).to_have_text(title)
        return page.url

    return _create
