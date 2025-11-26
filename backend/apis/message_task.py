import uuid
from datetime import datetime
from typing import List, Optional
from core.print import print_error, print_info
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from core.supabase.auth import get_current_user
from core.repositories import message_repo
from schemas import success_response, error_response, MessageTaskCreate


router = APIRouter(prefix="/message_tasks", tags=["消息任务"])


@router.get("", summary="获取消息任务列表")
async def list_message_tasks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[int] = None,
    _current_user: dict = Depends(get_current_user),
):
    """获取消息任务列表"""
    try:
        filters = {}
        if status is not None:
            filters["status"] = status
        total = await message_repo.count_message_tasks(filters=filters)
        message_tasks = await message_repo.get_message_tasks(
            filters=filters, limit=limit, offset=offset
        )
        return success_response(
            {
                "list": message_tasks,
                "page": {"limit": limit, "offset": offset},
                "total": total,
            }
        )
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.get("/{task_id}", summary="获取单个消息任务详情")
async def get_message_task(
    task_id: str,
    _current_user: dict = Depends(get_current_user),
):
    """获取单个消息任务详情"""
    try:
        message_task = await message_repo.get_message_task_by_id(task_id)
        if not message_task:
            raise HTTPException(status_code=404, detail="Message task not found")
        return success_response(data=message_task)
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.get("/message/test/{task_id}", summary="测试消息")
async def test_message_task(
    task_id: str,
    _current_user: dict = Depends(get_current_user),
):
    """测试消息消息任务详情"""
    try:
        message_task = await message_repo.get_message_task_by_id(task_id)
        if not message_task:
            raise HTTPException(status_code=404, detail="Message task not found")
        return success_response(data=message_task)
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.get("/{task_id}/run", summary="执行单个消息任务详情")
async def run_message_task(
    task_id: str,
    isTest: bool = Query(False),
    _current_user: dict = Depends(get_current_user),
):
    """执行单个消息任务详情"""
    try:
        from jobs.mps import run

        mps = {"count": 0, "list": []}
        tasks = run(task_id, isTest=isTest)
        count = 0
        if not tasks:
            raise HTTPException(status_code=404, detail="Message task not found")
        else:
            import json

            for task in tasks:
                try:
                    ids = json.loads(task.mps_id)
                    count += len(ids)
                    mps["count"] = count
                    mps["list"].append(ids)
                except Exception as e:
                    print_error(e)
                    pass
        if isTest:
            count = 1
        mps["message"] = f"执行成功，共执行更新{count}个订阅号"
        return success_response(
            data=mps, message=f"执行成功，共执行更新{count}个订阅号"
        )

    except Exception as e:
        print_error(e)
        return error_response(code=402, message=str(e))


@router.post("", summary="创建消息任务", status_code=status.HTTP_201_CREATED)
async def create_message_task(
    task_data: MessageTaskCreate = Body(...),
    _current_user: dict = Depends(get_current_user),
):
    """创建新消息任务"""
    try:
        task_data_dict = {
            "id": str(uuid.uuid4()),
            "message_template": task_data.message_template,
            "web_hook_url": task_data.web_hook_url,
            "cron_exp": task_data.cron_exp,
            "mps_id": task_data.mps_id,
            "message_type": task_data.message_type,
            "name": task_data.name,
            "status": task_data.status if task_data.status is not None else 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        new_task = await message_repo.create_message_task(task_data_dict)
        return success_response(data=new_task)
    except Exception as e:
        print_error(e)
        return error_response(code=500, message=str(e))


@router.put("/{task_id}", summary="更新消息任务")
async def update_message_task(
    task_id: str,
    task_data: MessageTaskCreate = Body(...),
    _current_user: dict = Depends(get_current_user),
):
    """更新消息任务"""
    try:
        existing_task = await message_repo.get_message_task_by_id(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="Message task not found")

        update_data = {}
        if task_data.message_template is not None:
            update_data["message_template"] = task_data.message_template
        if task_data.web_hook_url is not None:
            update_data["web_hook_url"] = task_data.web_hook_url
        if task_data.mps_id is not None:
            update_data["mps_id"] = task_data.mps_id
        if task_data.status is not None:
            update_data["status"] = task_data.status
        if task_data.cron_exp is not None:
            update_data["cron_exp"] = task_data.cron_exp
        if task_data.message_type is not None:
            update_data["message_type"] = task_data.message_type
        if task_data.name is not None:
            update_data["name"] = task_data.name

        updated_tasks = await message_repo.update_message_task(task_id, update_data)
        if updated_tasks:
            return success_response(data=updated_tasks[0])
        else:
            return error_response(code=500, message="更新消息任务失败")
    except Exception as e:
        return error_response(code=500, message=str(e))


@router.put("/job/fresh", summary="重载任务")
async def fresh_message_task(current_user: dict = Depends(get_current_user)):
    """重载任务"""
    from jobs.mps import reload_job

    reload_job()
    return success_response(message="任务已经重载成功")


@router.delete("/{task_id}", summary="删除消息任务")
async def delete_message_task(
    task_id: str,
    _current_user: dict = Depends(get_current_user),
):
    """删除消息任务"""
    try:
        existing_task = await message_repo.get_message_task_by_id(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="Message task not found")

        await message_repo.delete_message_task(task_id)
        return success_response(message="Message task deleted successfully")
    except Exception as e:
        return error_response(code=500, message=str(e))
