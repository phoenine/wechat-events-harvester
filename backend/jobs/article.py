from core.articles import article_repo
from core.common.app_settings import settings
from core.common.log import logger
from core.common.utils.async_tools import run_sync
from core.integrations.supabase.storage import supabase_storage_articles
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import mimetypes
import re
import requests
import uuid


def _sanitize_slug(value: str, default: str = "article") -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "-", text).strip("-")
    return text[:80] or default


def _guess_filename(image_url: str, content_type: str, index: int) -> str:
    parsed = urlparse(image_url)
    name = parsed.path.rsplit("/", 1)[-1]
    if not name or "." not in name:
        ext = mimetypes.guess_extension(content_type or "") or ".jpg"
        name = f"image-{index}{ext}"
    return _sanitize_slug(name, f"image-{index}.jpg")


def _format_storage_path(template: str, values: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(values.get(key, values.get("uuid", str(uuid.uuid4()))))

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replace, template)


def _upload_article_images(article: dict) -> dict:
    content = str(article.get("content") or "")
    if not content or not supabase_storage_articles.valid():
        return article

    soup = BeautifulSoup(content, "html.parser")
    images = soup.find_all("img")
    if not images:
        return article

    article_id = str(article.get("id") or str(uuid.uuid4()))
    article_name = _sanitize_slug(str(article.get("title") or article_id))

    for i, img in enumerate(images, start=1):
        src = (img.get("src") or img.get("data-src") or "").strip()
        if not src or src.startswith("data:"):
            continue
        try:
            resp = requests.get(src, timeout=15)
            resp.raise_for_status()
            ctype = (resp.headers.get("Content-Type") or "image/jpeg").split(";")[0]
            filename = _guess_filename(src, ctype, i)
            path = _format_storage_path(
                supabase_storage_articles.path,
                {
                    "uuid": str(uuid.uuid4()),
                    "article_id": article_id,
                    "article_name": article_name,
                    "filename": filename,
                },
            )
            run_sync(
                supabase_storage_articles.upload_bytes(
                    path=path,
                    data=resp.content,
                    content_type=ctype,
                )
            )
            img["src"] = supabase_storage_articles.public_url(path)
            if "data-src" in img.attrs:
                del img.attrs["data-src"]
        except Exception as e:
            logger.warning(f"文章图片上传失败，保留原链接: {e}")

    article["content"] = str(soup)
    return article


def UpdateArticle(art: dict, check_exist: bool = False):
    """更新文章"""
    mps_count = 0
    if settings.debug:
        pass
    try:
        art = _upload_article_images(dict(art))
        # 使用 Supabase 创建文章
        result = article_repo.sync_create_article(art)
        if result:
            mps_count = mps_count + 1
            return True
    except Exception as e:
        logger.info(f"创建文章失败: {e}")
    return False


def Update_Over(data=None):
    logger.info("更新完成")
    pass
