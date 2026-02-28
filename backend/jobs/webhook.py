import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

from core.articles.model import Article
from core.articles.content_format import format_content
from core.common.lax import TemplateParser
from core.common.log import logger
from core.common.runtime_settings import runtime_settings
from core.feeds.model import Feed
from core.integrations.notice import notice
from core.message_tasks.model import MessageTask

# 消息类型：0=发送到通知渠道，1=调用 Webhook
MESSAGE_TYPE_SEND = 0
MESSAGE_TYPE_WEBHOOK = 1

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def _article_to_dict(article: Article | dict[str, Any]) -> dict[str, Any]:
    """将 Article 或字典转为模板用字典, publish_time 格式化为可读时间。"""
    if isinstance(article, dict):
        out = dict(article)
    else:
        out = article.model_dump(mode="json")
    if out.get("publish_time") is not None:
        try:
            out["publish_time"] = datetime.fromtimestamp(int(out["publish_time"])).strftime(DATETIME_FMT)
        except (TypeError, ValueError, OSError):
            pass
    return out


@dataclass
class MessageWebHook:
    task: MessageTask
    feed: Feed
    articles: list[Article | dict[str, Any]]


def send_message(hook: MessageWebHook) -> str:
    """发送格式化消息"""
    template = (
        hook.task.message_template
        if hook.task.message_template
        else """
### {{feed.mp_name}} 订阅消息：
{% if articles %}
{% for article in articles %}
- [**{{ article.title }}**]({{article.url}}) ({{ article.publish_time }})\n
{% endfor %}
{% else %}
- 暂无文章\n
{% endif %}
    """
    )
    parser = TemplateParser(template)
    data = {
        "feed": hook.feed,
        "articles": hook.articles,
        "task": hook.task,
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    message = parser.render(data)
    # TODO 这里可以添加发送消息的具体实现

    logger.info(f"发送消息: {message}")
    notice(hook.task.web_hook_url, hook.task.name, message)
    return message


def call_webhook(hook: MessageWebHook) -> str:
    """调用webhook接口发送数据"""
    template = (
        hook.task.message_template
        if hook.task.message_template
        else """{
  "feed": {
    "id": "{{ feed.id }}",
    "name": "{{ feed.mp_name }}"
  },
  "articles": [
    {% if articles %}
     {% for article in articles %}
        {
          "id": "{{ article.id }}",
          "mp_id": "{{ article.mp_id }}",
          "title": "{{ article.title }}",
          "pic_url": "{{ article.pic_url }}",
          "url": "{{ article.url }}",
          "description": "{{ article.description }}",
          "publish_time": "{{ article.publish_time }}"
        }{% if not loop.last %},{% endif %}
      {% endfor %}
    {% endif %}
  ],
  "task": {
    "id": "{{ task.id }}",
    "name": "{{ task.name }}"
  },
  "now": "{{ now }}"
}
"""
    )

    # 检查template是否需要content
    template_needs_content = "content" in template.lower()

    # 根据content_format处理内容
    content_format = runtime_settings.get_sync("webhook.content_format", "html")
    logger.info(f"Content将以{content_format}格式发送")
    processed_articles = []
    for article in hook.articles:
        if isinstance(article, dict) and "content" in article and article["content"]:
            processed_article = article.copy()
            # 只有template需要content时才进行格式转换
            if template_needs_content:
                processed_article["content"] = format_content(
                    processed_article["content"], content_format
                )
            processed_articles.append(processed_article)
        else:
            processed_articles.append(article)

    data = {
        "feed": hook.feed,
        "articles": processed_articles,
        "task": hook.task,
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 预处理 content 字段：JSON 转义，便于模板嵌入
    def process_content(content: str | None) -> str:
        if content is None:
            return ""
        # 进行JSON转义处理引号
        json_escaped = json.dumps(content, ensure_ascii=False)
        # 去掉外层引号避免重复
        return json_escaped[1:-1]

    # 处理articles中的content字段，进行JSON转义
    if "articles" in data:
        for i, article in enumerate(data["articles"]):
            if isinstance(article, dict):
                if "content" in article:
                    data["articles"][i]["content"] = process_content(article["content"])
            elif hasattr(article, "content"):
                setattr(
                    data["articles"][i],
                    "content",
                    process_content(getattr(article, "content")),
                )

    parser = TemplateParser(template)

    payload = parser.render(data)
    # logger.info(payload)

    if not hook.task.web_hook_url:
        logger.error("web_hook_url为空")
        raise ValueError("web_hook_url 未配置")

    try:
        response = requests.post(
            hook.task.web_hook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return "Webhook调用成功"
    except Exception as e:
        raise ValueError(f"Webhook调用失败: {str(e)}")


def web_hook(hook: MessageWebHook) -> str | None:
    """根据消息类型路由到 send_message 或 call_webhook。无文章时返回 None。"""
    try:
        if not hook.articles:
            logger.warning("没有更新到文章")
            return None

        hook.articles = [_article_to_dict(a) for a in hook.articles]

        if hook.task.message_type == MESSAGE_TYPE_SEND:
            return send_message(hook)
        if hook.task.message_type == MESSAGE_TYPE_WEBHOOK:
            return call_webhook(hook)
        raise ValueError(f"未知的消息类型: {hook.task.message_type}")
    except Exception as e:
        raise ValueError(f"处理消息时出错: {str(e)}")
