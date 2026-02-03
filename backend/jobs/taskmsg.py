from typing import Union, Optional, Dict, List
from core.message_tasks import message_repo


def get_message_task(job_id: Union[str, list] = None) -> Optional[List[Dict]]:
    """获取消息任务详情"""
    try:
        # 构建过滤器
        filters = {"status": 1}
        if job_id:
            if isinstance(job_id, list):
                filters["id"] = {"in": job_id}
            else:
                filters["id"] = job_id

        # 使用Supabase数据库管理器获取消息任务
        message_tasks = message_repo.sync_get_message_tasks(filters=filters)
        return message_tasks if message_tasks else None
    except Exception as e:
        print(f"获取消息任务失败: {e}")
        return None
