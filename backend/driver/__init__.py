"""driver 包入口。

说明：
- 该模块通常用于对外“轻量导出” driver 层的公开 API（例如导出 wx_service 的 Facade）。
- __init__.py 中应尽量避免触发任何副作用：如启动浏览器、创建 controller、读写 Store 等。

当前实现：
- 使用 `from driver import *` 进行星号导入。
- 这种写法通常不推荐：
  1) 可能造成循环导入（driver 包导入自身）。
  2) 导出边界不清晰，不利于维护与静态分析。
  3) 若 driver 顶层导入链存在副作用，可能在 import driver 时被意外触发。

这里先保持现状，仅补充注释，后续如需收口导出，可改为显式导出：
- 例如：`from .wx_service import WxService` / `from .wx_service import get_state` 等。
"""

# NOTE: 暂不改动逻辑。该写法可能导致循环导入或导出边界不清晰，建议后续改为显式导出。
from driver import *
