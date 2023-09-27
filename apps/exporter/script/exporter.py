
import logging
import random
import signal
import sys

import click
from prometheus_client import CollectorRegistry, start_wsgi_server
from prometheus_client.core import GaugeMetricFamily

from utils.grm.client import GrmClient

# 配置标准输出到日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class GrmCollector(object):
    def __init__(self, module_id, module_secret, module_url):
        self._client = GrmClient(module_id, module_secret, module_url)
        self._module_url = module_url
        self._client.connect()

    def collect(self):
        # 获取变量
        vars = self._client.enumerate()
        # 获取值
        self._client.read(vars)

        # 构建指标
        g = GaugeMetricFamily(f'grm_{self._client.token.id}_gauge',
                              'Grm设备数据',
                              labels=['name', 'type', 'local'])
        for v in vars:
            if v.name.startswith('$'):
                continue
            if v.read_error == 0:
                # 全部统一用浮点值，客户端使用type解决转换问题
                g.add_metric(labels=[v.name, v.type, 'false'], value=v.value)
        yield g


@click.command()
@click.option('--random_port', envvar='RANDOM_PORT', type=int, required=True, help='Random port start number')
@click.option('--host', envvar='HOST', default='127.0.0.1', type=str, help='Host address')
@click.option('--advertise', envvar='ADVERTISE', default='127.0.0.1', type=str, help='Advertise address')
@click.option('--module-id', envvar='MODULE_ID', required=True, type=str, help='Module ID')
@click.option('--module-secret', envvar='MODULE_SECRET', required=True, type=str, help='Module secret')
@click.option('--module-url', envvar='MODULE_URL', required=True, type=str, help='Module URL')
def cli(random_port, host, advertise, module_id, module_secret, module_url):
    """命令入口"""
    collector = GrmCollector(module_id=module_id, 
                             module_secret=module_secret, 
                             module_url=module_url)
    registry = CollectorRegistry()
    registry.register(collector)

    start_port = random_port
    end_port = random_port + 1000
    for _ in range(0, 3):
        try:
            port = random.randint(start_port, end_port)
            start_wsgi_server(port, host, registry)

            # 写日志，设定一个标记给管理引用获取exporter的访问地址
            logger.info(f'# ADVERTISE {advertise}:{port}')

            def signal_handler(signal, frame):
                logger.info('Received SIGTERM. Cleaning up...')
                sys.exit(0)

            # 注册信号处理程序
            signal.signal(signal.SIGTERM, signal_handler)

            # 阻塞主线程
            signal.pause()
            
        except OSError as e:
            logger.info(f'Failed to start server on {host}:{port}: {e}')
    sys.exit(-1)

if __name__ == '__main__':
    cli()
