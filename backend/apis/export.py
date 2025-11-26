import csv
import io
import os
import uuid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Body,
    UploadFile,
    File,
    Request,
)
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from core.supabase.auth import get_current_user
from core.repositories import feed_repo, tag_repo
from core.wx import search_Biz
from schemas import success_response, error_response
from datetime import datetime
from core.config import cfg
from core.res import save_avatar_locally


router = APIRouter(prefix=f"/export", tags=["导入/导出"])


@router.get("/mps/export", summary="导出公众号列表")
async def export_mps(
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    _current_user: dict = Depends(get_current_user),
):
    try:
        # 获取公众号列表
        feeds = await feed_repo.get_feeds(limit=limit, offset=offset)

        # 如果有搜索关键词，进行过滤
        if kw:
            feeds = [
                feed for feed in feeds if kw.lower() in feed.get("mp_name", "").lower()
            ]

        # 准备CSV数据
        headers = ["id", "公众号名称", "封面图", "简介", "状态", "创建时间", "faker_id"]
        data = [
            [
                mp.get("id"),
                mp.get("mp_name"),
                mp.get("mp_cover"),
                mp.get("mp_intro"),
                mp.get("status"),
                mp.get("created_at"),
                mp.get("faker_id"),
            ]
            for mp in feeds
        ]

        # 创建临时CSV文件
        temp_file = "temp_mp_export.csv"
        with open(temp_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)

        # 返回文件下载
        return FileResponse(
            temp_file,
            media_type="text/csv",
            filename="公众号列表.csv",
            background=BackgroundTask(lambda: os.remove(temp_file)),
        )

    except Exception as e:
        print(f"导出公众号列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(code=50001, message="导出公众号列表失败"),
        )


@router.post("/mps/import", summary="导入公众号列表")
async def import_mps(
    file: UploadFile = File(...),
    _current_user: dict = Depends(get_current_user),
):
    try:
        # 读取上传的CSV文件
        contents = (await file.read()).decode("utf-8-sig")
        csv_reader = csv.DictReader(io.StringIO(contents))

        # 验证必要字段
        required_columns = ["公众号名称", "封面图", "简介"]
        if not all(col in csv_reader.fieldnames for col in required_columns):
            missing_cols = [
                col for col in required_columns if col not in csv_reader.fieldnames
            ]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code=40001, message=f"CSV文件缺少必要列: {', '.join(missing_cols)}"
                ),
            )

        # 导入数据
        imported = 0
        updated = 0
        skipped = 0

        for row in csv_reader:
            mp_id = row.get("id")
            mp_name = row["公众号名称"]
            mp_cover = row["封面图"]
            mp_intro = row.get("简介", "")
            status_val = int(row.get("状态", 1)) if row.get("状态") else 1
            faker_id = row.get("faker_id", "")

            # 检查是否已存在
            existing = await feed_repo.get_feed_by_faker_id(faker_id)

            if existing:
                # 更新现有记录
                update_data = {
                    "mp_cover": mp_cover,
                    "mp_intro": mp_intro,
                    "status": status_val,
                    "faker_id": faker_id,
                }
                await feed_repo.update_feed(existing["id"], update_data)
                updated += 1
            else:
                # 创建新记录
                feed_data = {
                    "id": mp_id,
                    "mp_name": mp_name,
                    "mp_cover": mp_cover,
                    "mp_intro": mp_intro,
                    "status": status_val,
                    "faker_id": faker_id,
                }

                if not feed_data["id"]:
                    import base64

                    _mp_id = base64.b64decode(faker_id).decode("utf-8")
                    feed_data["id"] = f"MP_WXS_{_mp_id}"

                await feed_repo.create_feed(feed_data)
                imported += 1

        return success_response(
            {
                "message": "导入公众号列表成功",
                "stats": {
                    "total": imported + updated + skipped,
                    "imported": imported,
                    "updated": updated,
                    "skipped": skipped,
                },
            }
        )

    except Exception as e:
        print(f"导入公众号列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(code=50001, message="导入公众号列表失败"),
        )


@router.get("/mps/opml", summary="导出公众号列表为OPML格式")
async def export_mps_opml(
    request: Request,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    _current_user: dict = Depends(get_current_user),
):
    try:
        # 获取公众号列表
        feeds = await feed_repo.get_feeds(limit=limit, offset=offset)

        # 如果有搜索关键词，进行过滤
        if kw:
            feeds = [
                feed for feed in feeds if kw.lower() in feed.get("mp_name", "").lower()
            ]

        rss_domain = cfg.get("rss.base_url", str(request.base_url))
        if rss_domain == "":
            rss_domain = str(request.base_url)

        # 生成OPML内容
        opml_content = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <head>
    <title>公众号订阅列表</title>
    <dateCreated>{date}</dateCreated>
  </head>
  <body>
{outlines}
  </body>
</opml>""".format(
            date=datetime.now().isoformat(),
            outlines="".join(
                [
                    f'<outline text="{mp.get("mp_name")}" title="{mp.get("mp_name")}" type="rss"  xmlUrl="{rss_domain}feed/{mp.get("id")}.atom"/>\n'
                    for mp in feeds
                ]
            ),
        )

        # 创建临时OPML文件
        temp_file = "temp_mp_export.opml"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(opml_content)

        # 返回文件下载
        return FileResponse(
            temp_file,
            media_type="application/xml",
            filename="公众号订阅列表.opml",
            background=BackgroundTask(lambda: os.remove(temp_file)),
        )

    except Exception as e:
        print(f"导出OPML列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50002, message="导出OPML列表失败"),
        )


@router.get("/tags", summary="导出标签列表")
async def export_tags(
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    _current_user: dict = Depends(get_current_user),
):
    try:
        # 获取标签列表
        tags = await tag_repo.get_tags(limit=limit, offset=offset)

        # 如果有搜索关键词，进行过滤
        if kw:
            tags = [tag for tag in tags if kw.lower() in tag.get("name", "").lower()]

        headers = ["id", "标签名称", "封面图", "描述", "状态", "创建时间", "mps_id"]
        data = []
        for tag in tags:
            data.append(
                [
                    tag.get("id"),
                    tag.get("name"),
                    tag.get("cover"),
                    tag.get("intro"),
                    tag.get("status"),
                    tag.get("created_at", ""),
                    tag.get("mps_id"),
                ]
            )

        # 创建临时CSV文件
        temp_file = "temp_tags_export.csv"
        with open(temp_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)

        return FileResponse(
            temp_file,
            media_type="text/csv",
            filename="标签列表.csv",
            background=BackgroundTask(lambda: os.remove(temp_file)),
        )

    except Exception as e:
        print(f"导出标签列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50003, message="导出标签列表失败"),
        )


@router.post("/tags/import", summary="导入标签列表")
async def import_tags(
    file: UploadFile = File(...),
    _current_user: dict = Depends(get_current_user),
):
    try:
        contents = (await file.read()).decode("utf-8-sig")
        csv_reader = csv.DictReader(io.StringIO(contents))

        required_columns = ["标签名称", "状态", "mps_id"]
        if not all(col in csv_reader.fieldnames for col in required_columns):
            missing_cols = [
                col for col in required_columns if col not in csv_reader.fieldnames
            ]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code=40002, message=f"CSV文件缺少必要列: {', '.join(missing_cols)}"
                ),
            )

        imported = 0
        updated = 0
        skipped = 0

        for row in csv_reader:
            tag_id = row.get("id")
            tag_name = row.get("标签名称")

            if not tag_name or not tag_name.strip():
                skipped += 1
                continue  # 如果标签名称为空，则跳过此行

            existing_tag = None
            if tag_id and tag_id.strip():
                existing_tag = await tag_repo.get_tag_by_id(tag_id.strip())
            else:
                # 如果没有提供ID，尝试按名称查找
                existing_tag = await tag_repo.get_tag_by_name(tag_name.strip())

            cover = row.get("封面图", "")
            intro = row.get("描述", "")
            try:
                status_val = int(row.get("状态", 1))
            except (ValueError, TypeError):
                status_val = 1
            mps_id_str = row.get("mps_id") or "[]"

            if existing_tag:
                # 更新现有记录
                update_data = {
                    "name": tag_name.strip(),
                    "cover": cover,
                    "intro": intro,
                    "status": status_val,
                    "mps_id": mps_id_str,
                    "updated_at": datetime.now().isoformat(),
                }
                await tag_repo.update_tag(existing_tag["id"], update_data)
                updated += 1
            else:
                # 创建新记录
                tag_data = {
                    "id": tag_id or str(uuid.uuid4()),
                    "name": tag_name.strip(),
                    "cover": cover,
                    "intro": intro,
                    "status": status_val,
                    "mps_id": mps_id_str,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
                await tag_repo.create_tag(tag_data)
                imported += 1

        return success_response(
            {
                "message": "导入标签列表成功",
                "stats": {
                    "total_rows": imported + updated + skipped,
                    "imported": imported,
                    "updated": updated,
                    "skipped": skipped,
                },
            }
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"导入标签列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50004, message=f"导入标签列表失败: {str(e)}"),
        )
