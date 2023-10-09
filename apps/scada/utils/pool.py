# 每个线程保留一个模块的连接
import threading
from apps.scada.models import Module
from apps.scada.utils.grm.client import GrmClient


grm_pool_local = threading.local()


def get_grm_client(module: Module) -> GrmClient:
    """缓存使用过的grm客户端"""

    key = (
        module.module_number,
        module.module_secret,
        module.module_url,
    )

    if not hasattr(grm_pool_local, "grm_pool"):
        pool: dict[tuple[str, str, str], GrmClient] = {}
        grm_pool_local.grm_pool = pool
    else:
        pool = grm_pool_local.grm_pool

    if key in pool:
        return pool[key]
    else:
        client = GrmClient(
            module.module_number, module.module_secret, module.module_url
        )
        client.connect()

        pool[key] = client
        return client
