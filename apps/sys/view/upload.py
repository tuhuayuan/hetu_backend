import imghdr
import mimetypes
import os

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse_lazy
from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.post("", response=str)
@api_schema
def upload_file(request, resource: str, file: UploadedFile = File(...)):
    """处理图片上传"""

    if file.size > 10 * 1024 * 1024:
        raise HttpError(400, "File size should not exceed 10MB.")

    # 检查图片合法性
    file_content = file.read()
    file_type = imghdr.what(None, h=file_content)
    if file_type not in ["jpeg", "png", "gif"]:
        raise HttpError(400, "Only JPEG, PNG, and GIF files are allowed.")

    # 保存图片
    upload_path = os.path.join(settings.UPLOAD_ROOT, resource)
    os.makedirs(upload_path, exist_ok=True)

    # 保存文件
    file_name = os.path.join(upload_path, file.name)
    with open(file_name, "wb") as destination:
        destination.write(file_content)

    return f"/{resource}/{file.name}"


@router.get("/{resource}/{file_name}")
def get_static_resource(request, resource: str, file_name: str):
    """获取资源文件"""

    # 将资源路径和文件名拼接为绝对路径
    file_path = os.path.join(settings.UPLOAD_ROOT, resource, file_name)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise HttpError(404, "File not found.")

    # 获取文件的 MIME 类型
    mime_type, _ = mimetypes.guess_type(file_path)

    # 返回文件响应
    with open(file_path, "rb") as file:
        response = HttpResponse(file, content_type=mime_type)
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response


@router.get("/{resource}", response=list[str])
@api_paginate
def get_resource_files(request, resource: str):
    """获取资源下面的文件列表"""

    resource_path = os.path.join(settings.UPLOAD_ROOT, resource)
    if not os.path.exists(resource_path):
        raise HttpError(404, "Resource not found")

    files = []
    for file_name in os.listdir(resource_path):
        if os.path.isfile(os.path.join(resource_path, file_name)):
            file_url = f"/{resource}/{file_name}"
            files.append(file_url)

    return files


@router.get("", response=str)
@api_schema
def get_resource_url(request, resource_path: str):
    """获取资源链接"""

    try:
        # 解析资源路径和文件名
        parts = resource_path.split("/", 2)
        resource = parts[1]
        file_name = parts[2]
    except:
        raise HttpError(400, "Resource path error.")
    
    url = reverse_lazy(
        "api-v1:get_static_resource",
        kwargs={"resource": resource, "file_name": file_name},
    )

    # 获取请求的主机和端口信息
    host = request.get_host()
    port = request.get_port()

    # 构建完整的包含端口号的 URL
    if request.is_secure():
        absolute_url = f"https://{host}{url}"
    else:
        absolute_url = f"http://{host}{url}"
    request.ab
    return absolute_url
