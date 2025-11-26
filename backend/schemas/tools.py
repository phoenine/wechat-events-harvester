from pydantic import BaseModel, Field
from typing import Optional, Any, List


class ExportArticlesRequest(BaseModel):
    """导出文章请求模型"""

    mp_id: str = Field(..., description="公众号ID")
    doc_id: Optional[List[str]] = Field(None, description="文档ID列表, 为空则导出所有文章")
    page_size: int = Field(10, description="每页数量", ge=1, le=10)
    page_count: int = Field(1, description="页数, 0表示全部", ge=0, le=10000)
    add_title: bool = Field(True, description="是否添加标题")
    remove_images: bool = Field(True, description="是否移除图片")
    remove_links: bool = Field(False, description="是否移除链接")
    export_md: bool = Field(False, description="是否导出Markdown格式")
    export_docx: bool = Field(False, description="是否导出Word文档格式")
    export_json: bool = Field(False, description="是否导出JSON格式")
    export_csv: bool = Field(False, description="是否导出CSV格式")
    export_pdf: bool = Field(True, description="是否导出PDF格式")
    zip_filename: Optional[str] = Field(None, description="压缩包文件名，为空则自动生成")


class ExportArticlesResponse(BaseModel):
    """导出文章响应模型"""

    record_count: int = Field(..., description="导出的文章数量")
    export_path: str = Field(..., description="导出文件路径")
    message: str = Field(..., description="导出结果消息")


class ExportFileInfo(BaseModel):
    """导出文件信息模型"""

    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    created_time: str = Field(..., description="创建时间（ISO格式）")
    modified_time: str = Field(..., description="修改时间（ISO格式）")


class DeleteFileRequest(BaseModel):
    """删除文件请求模型"""

    filename: str = Field(..., description="文件名")
    mp_id: str = Field(..., description="公众号ID")
