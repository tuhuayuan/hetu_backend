from datetime import datetime

import requests

from apps.scada.utils.grm.schemas import GrmModuleInfo, GrmModuleToken, GrmVariable


class GrmError(Exception):
    def __init__(self, code: int, message: str):
        self.message = message
        self.code = code

    def __str__(self):
        return f"grm error code: {self.code}, message: {self.message}"


class GrmClient:
    req_header = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Type": "text/plain;charset=UTF-8",
    }

    def __init__(
        self,
        module_id: str,
        module_secret: str,
        module_url: str,
        timeout=5,
        reconnect=True,
    ) -> None:
        self._module_id = module_id
        self._module_secret = module_secret
        self._module_url = module_url
        self._timeout = timeout
        self._reconnect = reconnect
        self._module_token: GrmModuleToken = None

    def _exdata(self, data: str, op: str) -> list[str]:
        """GRM数据获取接口"""

        token = self._module_token
        url = f"http://{token.data_url}/exdata?SID={token.sid}&OP={op}"

        resp = requests.post(
            url=url,
            headers=self.req_header,
            data=data.encode("utf-8"),
            timeout=self._timeout,
        )
        if resp.status_code != 200:
            raise GrmError(resp.status_code, "HTTP连接错误")
        
        results = resp.text.split("\r\n")

        if results[0] == "OK":
            return results[1:]
        elif results[0] == "ERROR":
            raise GrmError(int(results[1]), results[2])
        else:
            raise GrmError(-1, "未知错误")

    def _exlogon(self) -> GrmModuleToken:
        """GRM模块登录"""

        data = f"GRM={self._module_id}\r\nPASS={self._module_secret}"
        url = f"{self._module_url}/exlog"

        resp = requests.post(
            url=url, headers=self.req_header, data=data, timeout=self._timeout
        )
        if resp.status_code != 200:
            raise GrmError(resp.status_code, "HTTP连接错误")

        results = resp.text.split("\r\n")

        if results[0] == "OK":
            self._module_token = GrmModuleToken(
                id=self._module_id,
                sid=results[2].split("=")[1],
                data_url=results[1].split("=")[1],
            )
            return self._module_token
        elif results[0] == "ERROR":
            raise GrmError(int(results[1]), results[2])
        else:
            raise GrmError(-1, "未知错误")

    @property
    def token(self):
        return self._module_token

    def connect(self, token: GrmModuleToken = None, force=False) -> GrmModuleToken:
        """连接到模块数据
        1、SID对于每个模块有最大数量限制
        2、SID不活跃10分钟会自动过期
        所以应用需要自己管理好SID的获取和使用
        """
        if token and token.id == self._module_id:
            #  使用提供的Token
            self._module_token = token
            return token
        elif self._module_token and not force:
            # 使用现有的Token
            return self._module_token
        else:
            # 获取新的Token
            return self._exlogon()

    def _with_reconnect(fn):
        """自动重连装饰器，用于返回错误8的时候重新连接"""

        def wrapper(self, *args, **kwargs):
            if self._reconnect:
                try:
                    result = fn(self, *args, **kwargs)
                except GrmError as err:
                    if err.code == 8:
                        # 错误8则刷新sid
                        self._exlogon()
                    else:
                        raise err
            result = fn(self, *args, **kwargs)
            return result

        return wrapper

    @_with_reconnect
    def enumerate(self) -> list[GrmVariable]:
        """枚举模块变量"""

        lines = self._exdata("NTRPG", "E")
        n = int(lines[0])
        vars: list[GrmVariable] = []

        for row in lines[1 : n + 1]:
            fields = row.split(",")
            vars.append(
                GrmVariable(
                    module_number=self._module_id,
                    name=fields[0],
                    type=fields[1],
                    rw=(fields[2] == "W"),
                    priority=int(fields[3]),
                    group=fields[4],
                )
            )
        return vars

    @_with_reconnect
    def read(self, vars: list[GrmVariable]) -> None:
        """读取列表中的变量值"""

        data = f"{len(vars)}\r\n"
        data = data + "\r\n".join([v.name for v in vars])

        lines = self._exdata(data, "R")
        n = int(lines[0])

        for var, row in zip(vars, lines[1 : n + 1]):
            if row.startswith("#ERROR#"):
                # 给变量设置错误状态
                var.read_error = int(row[7:])
            else:
                var.read_error = 0
                var.value = float(row)

    @_with_reconnect
    def write(self, vars: list[GrmVariable]) -> None:
        """写入列表中变量的值"""

        data = f"{len(vars)}\r\n"
        for v in vars:
            data = data + v.name + f"\r\n{v.value}\r\n"

        lines = self._exdata(data, "W")
        n = int(lines[0])

        for v, r in zip(vars, lines[1 : n + 1]):
            v.write_error = int(r)

    @_with_reconnect
    def info(self) -> GrmModuleInfo:
        format_str = "%Y%m%d%H%M%S%f"  # 时间格式，包括毫秒部分
        lines = self._exdata("", "I")

        return GrmModuleInfo(
            id=self._module_id,
            name=lines[0],
            desc=lines[1],
            logo=lines[2],
            logon_clients=int(lines[3]),
            status=int(lines[4]),
            logon_at=datetime.strptime(lines[5], format_str),
            last_activate=datetime.strptime(lines[6], format_str),
            logon_ip=lines[7],
        )
