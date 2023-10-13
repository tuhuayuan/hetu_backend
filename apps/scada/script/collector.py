import logging
import random
import signal
import sys
import threading
from wsgiref.simple_server import WSGIRequestHandler, make_server

import click
from prometheus_client import CollectorRegistry, make_wsgi_app, start_wsgi_server
from prometheus_client.core import GaugeMetricFamily

from apps.scada.utils.grm.client import GrmClient, GrmError


# 配置标准输出到日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

server_handler = logging.StreamHandler(stream=sys.stderr)
server_handler.setLevel(logging.ERROR)
logger.addHandler(server_handler)

class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO  # 仅允许 INFO 级别的记录通过
    
info_handler = logging.StreamHandler(stream=sys.stdout)
info_handler.setLevel(logging.INFO)
info_handler.addFilter(InfoFilter())
logger.addHandler(info_handler)


class GrmCollector(object):
    def __init__(self, module_number, module_secret, module_url):
        self._client = GrmClient(module_number, module_secret, module_url)
        self._module_url = module_url
        try:
            self._client.connect()
        except GrmError as e:
            logger.error(f"登陆GRM模块错误 {e.message}")

    def collect(self):
        try:
            # 获取变量
            vars = self._client.enumerate()
            # 获取值
            self._client.read(vars)
        except GrmError as e:
            logger.error(f"读取GRM模块数据错误 {e.message}")
            raise StopIteration()

        # 构建指标
        g = GaugeMetricFamily(
            f"grm_{self._client.token.id}_gauge",
            "Grm设备数据",
            labels=["name", "type", "local"],
        )
        for v in vars:
            if v.read_error == 0:
                # 全部统一用浮点值，客户端使用type解决转换问题
                g.add_metric(labels=[v.name, v.type, "false"], value=v.value)
            else:
                logger.error(f"ERROR: {v.read_error}, Variable: {v.name}")
        yield g


class CollectorHandler(WSGIRequestHandler):
    """WSGI handler"""

    def log_error(self, format, *args):
        """Log an error.

        This is called when a request cannot be fulfilled.  By
        default it passes the message on to log_message().

        Arguments are the same as for log_message().

        XXX This should go to the separate error log.

        """
        logger.error(format, *args)

    def log_message(self, format, *args):
        """不使用该方法"""
        pass


@click.command()
@click.option(
    "--random_port",
    envvar="RANDOM_PORT",
    type=int,
    required=True,
    help="Random port start number",
)
@click.option(
    "--host",
    envvar="HOST",
    default="127.0.0.1",
    type=str,
    help="Host address",
)
@click.option(
    "--advertise",
    envvar="ADVERTISE",
    default="127.0.0.1",
    type=str,
    help="Advertise address",
)
@click.option(
    "--module-number",
    envvar="MODULE_NUMBER",
    required=True,
    type=str,
    help="Module Number",
)
@click.option(
    "--module-secret",
    envvar="MODULE_SECRET",
    required=True,
    type=str,
    help="Module secret",
)
@click.option(
    "--module-url",
    envvar="MODULE_URL",
    required=True,
    type=str,
    help="Module URL",
)
def cli(random_port, host, advertise, module_number, module_secret, module_url):
    """命令入口"""
    collector = GrmCollector(
        module_number=module_number, module_secret=module_secret, module_url=module_url
    )
    registry = CollectorRegistry()
    registry.register(collector)

    start_port = random_port
    end_port = random_port + 1000
    for _ in range(0, 3):
        try:
            # 随机端口
            port = random.randint(start_port, end_port)
            # 构建wsgi服务器
            app = make_wsgi_app(registry)
            httpd = make_server(host, port, app, handler_class=CollectorHandler)
            t = threading.Thread(target=httpd.serve_forever)
            t.daemon = True
            t.start()
            # 写日志，设定一个标记给管理引用获取exporter的访问地址
            logger.info(f"# ADVERTISE {advertise}:{port}")

            # 处理停止信号
            def signal_handler(signal, frame):
                logger.info("Received SIGTERM. Cleaning up...")
                sys.exit(0)

            # 注册信号处理程序
            signal.signal(signal.SIGTERM, signal_handler)
            # 阻塞主线程
            signal.pause()
        except OSError as e:
            logger.error(f"Failed to start server on {host}:{port}: {e}")
    sys.exit(-1)


if __name__ == "__main__":
    cli()
