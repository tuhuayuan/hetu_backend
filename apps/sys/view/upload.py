import imghdr
import mimetypes
import os
from django.conf import settings
from django.http import HttpResponse

from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile
from apps.sys.schemas import ResourceOut
from utils.schema.base import api_schema
from oss2 import (
    Bucket,
    ProviderAuth,
    ObjectIterator,
)
from oss2.credentials import EnvironmentVariableCredentialsProvider


# Get Aliyun OSS credentials from environment variables
auth = ProviderAuth(EnvironmentVariableCredentialsProvider())

# Fill in the correct OSS bucket endpoint and name
oss_endpoint = "oss-cn-shanghai.aliyuncs.com"
oss_bucket_name = "hetu-scada"

# Create an OSS bucket instance
bucket = Bucket(auth, oss_endpoint, oss_bucket_name)

# 路由器
router = Router()


@router.get("/{resource}/{file_name}")
def get_static_resource(request, resource: str, file_name: str):
    """获取资源文件"""

    # 将资源路径和文件名拼接为绝对路径
    file_path = os.path.join(settings.UPLOAD_ROOT, resource, file_name)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise HttpError(404, "File not found: " + file_path)

    # 获取文件的 MIME 类型
    mime_type, _ = mimetypes.guess_type(file_path)

    # 返回文件响应
    with open(file_path, "rb") as file:
        response = HttpResponse(file, content_type=mime_type)
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response


@router.post("", response=str)
@api_schema
def upload_file(request, resource_prefix: str, file: UploadedFile = File(...)):
    """处理图片上传"""

    if file.size > 10 * 1024 * 1024:
        raise HttpError(400, "File size should not exceed 10MB.")

    # 检查图片合法性
    file_content = file.read()
    file_type = imghdr.what(None, h=file_content)
    if file_type not in ["jpeg", "png", "gif"]:
        raise HttpError(400, "Only JPEG, PNG, and GIF files are allowed.")

    # 对象路径
    oss_object_key = f"{resource_prefix}/{file.name}"
    bucket.put_object(oss_object_key, file_content)

    file_url = f"https://{oss_bucket_name}.{oss_endpoint}/{oss_object_key}"
    return file_url


@router.get("", response=list[ResourceOut])
@api_schema
def get_resource_files(request, resource_prefix: str):
    """获取资源下面的文件列表"""

    object_iterator = ObjectIterator(bucket, prefix=resource_prefix)
    files: list[ResourceOut] = []

    for obj in object_iterator:
        files.append(
            ResourceOut(
                resource_key=obj.key,
                resource_url=f"https://{oss_bucket_name}.{oss_endpoint}/{obj.key}",
            )
        )

    return files
