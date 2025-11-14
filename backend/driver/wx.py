import sys
import threading
import asyncio
from .playwright_driver import PlaywrightController
from .success import Success
import time
import os
from driver.success import getStatus
from driver.store import Store
import re
from threading import Timer, Lock
from .cookies import expire
from core.print import print_error, print_warning, print_info, print_success


# 进程内登录互斥，防止并发登录/重复扫码
LOGIN_MUTEX = threading.Lock()


class Wx:
    HasLogin = False
    SESSION = None
    HasCode = False
    isLOCK = False
    WX_LOGIN = "https://mp.weixin.qq.com/"
    WX_HOME = "https://mp.weixin.qq.com/cgi-bin/home"
    wx_login_url = "static/wx_qrcode.png"
    lock_file_path = "data/.lock"
    CallBack = None
    Notice = None
    # 添加线程锁保护共享变量
    _login_lock = Lock()

    def __init__(self):
        self.lock_path = os.path.dirname(self.lock_file_path)
        self.refresh_interval = 3600 * 24
        self.controller = PlaywrightController()
        if not os.path.exists(self.lock_path):
            os.makedirs(self.lock_path)
        self.Clean()
        self.release_lock()
        pass

    def GetHasCode(self):
        if os.path.exists(self.wx_login_url):
            return True
        return False

    def extract_token_from_requests(self):
        """从页面中提取token"""
        try:
            page = self.controller.page
            # 尝试从当前URL获取token
            current_url = page.url
            token_match = re.search(r"token=([^&]+)", current_url)
            if token_match:
                return token_match.group(1)

            # 尝试从localStorage获取
            token = page.evaluate("() => localStorage.getItem('token')")
            if token:
                return token

            # 尝试从sessionStorage获取
            token = page.evaluate("() => sessionStorage.getItem('token')")
            if token:
                return token

            # 尝试从cookie获取
            cookies = page.context.cookies()
            for cookie in cookies:
                if "token" in cookie["name"].lower():
                    return cookie["value"]

            return None
        except Exception as e:
            print(f"提取token时出错: {str(e)}")
            return None

    def GetCode(self, CallBack=None, Notice=None):
        self.Notice = Notice
        if self.check_lock():
            print_warning("微信公众平台登录脚本正在运行，请勿重复运行")
            return {
                "code": f"{self.wx_login_url}?t={(time.time())}",
                "msg": "微信公众平台登录脚本正在运行，请勿重复运行！",
            }

        self.Clean()
        print("子线程执行中")
        from core.thread import ThreadManager

        self.thread = ThreadManager(
            target=self.wxLogin, args=(CallBack, True)
        )  # 传入函数名
        self.thread.start()  # 启动线程
        print("微信公众平台登录 v1.34")
        return WX_API.QRcode()

    wait_time = 1

    def QRcode(self):
        return {
            "code": f"/{self.wx_login_url}?t={(time.time())}",
            "is_exists": self.GetHasCode(),
        }

    def refresh_task(self):
        try:
            page = self.controller.page
            if not page:
                print("页面刷新失败")
                raise Exception("页面刷新失败")
            page.reload()
            self.Call_Success()
            if "home" not in page.url:
                print("检测到登录已过期，请重新登录")
                raise Exception("登录已经失效，请重新登录")
        except Exception:
            raise Exception("浏览器关闭")

    def schedule_refresh(self):
        if self.refresh_interval <= 0:
            return

        with self._login_lock:
            if (
                not self.HasLogin
                or not hasattr(self, "controller")
                or self.controller is None
            ):
                return

        try:
            self.refresh_task()
            # 使用守护线程避免资源泄露
            timer = Timer(self.refresh_interval, self.schedule_refresh)
            timer.daemon = True
            timer.start()
        except Exception as e:
            print_error(f"定时刷新任务失败: {str(e)}")
            # 不再抛出异常，避免无限循环

    def Token(self, CallBack=None):
        try:
            self.CallBack = CallBack
            if not getStatus():
                print_warning("未登录，请先扫码登录")
                # 异步拉起二维码生成，不阻塞当前调用
                self.GetCode(CallBack=CallBack, Notice=None)
                return {
                    "need_login": True,
                    "message": "未登录，请扫码登录后重试。",
                    "code": f"/{self.wx_login_url}?t={(time.time())}",
                    "is_exists": self.GetHasCode(),
                }

            from driver.token import wx_cfg

            token = str(wx_cfg.get("token", ""))
            if not token:
                print_warning("未找到有效的token")
                return None
            driver = self.controller
            driver.start_browser()
            driver.open_url(f"{self.WX_HOME}?t=home/index&lang=zh_CN&token={token}")

            cookie = Store.load()
            if cookie:
                # 为每个cookie添加必要的domain字段
                for c in cookie:
                    if "domain" not in c:
                        c["domain"] = ".weixin.qq.com"
                    if "path" not in c:
                        c["path"] = "/"
                driver.add_cookies(cookie)
            # 为单个token cookie添加必要的字段
            token_cookie = {
                "name": "token",
                "value": token,
                "domain": ".weixin.qq.com",
                "path": "/",
            }
            driver.add_cookie(token_cookie)
            page = driver.page
            qrcode = page.locator("#jumpUrl")
            qrcode.wait_for(state="visible", timeout=self.wait_time * 1000)
            qrcode.click()
            time.sleep(2)
            return self.Call_Success()
        except ImportError as e:
            print_error(f"导入模块失败: {str(e)}")
            return None
        except Exception as e:
            print_error(f"Token操作失败: {str(e)}")
            return None
        finally:
            self.Close()

    def isLock(self):
        """二维码是否已生成且有效（兼容旧名）"""
        try:
            if self.isLOCK and os.path.exists(self.wx_login_url):
                size = os.path.getsize(self.wx_login_url)
                return size > 364
        except Exception as e:
            print(f"二维码图片获取失败: {str(e)}")
        return False

    def wxLogin(self, CallBack=None, NeedExit=False):
        """
        微信公众平台登录流程：
        1. 检查依赖和环境
        2. 打开微信公众平台
        3. 全屏截图保存二维码
        4. 等待用户扫码登录
        5. 获取登录后的cookie和token
        6. 启动定时刷新线程(默认30分钟刷新一次)
        """

        # 使用上下文管理器确保资源清理
        try:
            # 为登录线程设置独立事件循环（Playwright sync 底层依赖 asyncio）
            try:
                _existing_loop = None
                try:
                    _existing_loop = asyncio.get_event_loop()
                except RuntimeError:
                    _existing_loop = None
                if _existing_loop is None or _existing_loop.is_closed():
                    _new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(_new_loop)
                    print_info("为登录线程创建新的事件循环")
            except Exception:
                # 避免因事件循环异常阻断登录流程
                pass
            # 优先检查跨进程锁与会话有效性，避免无谓启动
            if self.check_lock():
                print_warning("微信公众平台登录脚本正在运行，请勿重复运行")
                return None
            if getStatus():
                print_info("检测到会话仍有效，跳过登录流程")
                self.CallBack = CallBack
                return self.Call_Success()

            # 进程内互斥：避免并发登录任务（非阻塞获取，若已有登录则直接返回）
            acquired = LOGIN_MUTEX.acquire(blocking=False)
            if not acquired:
                print_warning("已有登录任务在进行中，跳过本次调用")
                return None

            self.set_lock()

            with self._login_lock:
                self.HasLogin = False

            # 清理现有资源
            self.cleanup_resources()

            # 初始化浏览器控制器
            driver = self.controller
            print_info("正在启动浏览器...")
            # 显式使用 firefox，避免系统 Chrome 依赖
            for i in range(2):
                try:
                    driver.start_browser(anti_crawler=False, browser_name="firefox")
                    break
                except Exception as e:
                    if i == 1:
                        raise
                    print_warning(f"浏览器启动失败，第{i+1}次重试: {e}")
                    try:
                        driver.cleanup()
                    except Exception:
                        pass
                    time.sleep(1.0)
            driver.open_url(self.WX_LOGIN)
            page = driver.page

            print_info("正在加载登录页面...")
            page.wait_for_load_state("domcontentloaded")

            # 定位二维码区域并显式等待
            qr_tag = ".login__type__container__scan__qrcode"
            qrcode = page.wait_for_selector(qr_tag, state="visible", timeout=15000)
            if qrcode is None:
                raise Exception("未找到登录二维码元素")

            # 截图二维码
            qrcode.screenshot(path=self.wx_login_url)

            print("二维码已保存为 wx_qrcode.png，请扫码登录...")
            self.HasCode = True
            if os.path.getsize(self.wx_login_url) <= 364:
                raise Exception("二维码图片获取失败，请重新扫码")
            # 等待登录成功（检测二维码图片加载完成）
            print("等待扫码登录...")
            if self.Notice is not None:
                self.Notice()

            # 等待跳转到首页
            page.wait_for_url(self.WX_HOME + "*", timeout=120000)
            print("登录成功, 正在获取cookie和token...")

            from .success import setStatus

            with self._login_lock:
                self.HasLogin = True
            setStatus(True)
            self.CallBack = CallBack
            self.Call_Success()
        except Exception as e:
            print(f"\n错误发生: {str(e)}")
            self.SESSION = None
            return self.SESSION
        finally:
            # 若本次需要退出且浏览器已清理，尝试关闭我们为该线程创建的事件循环以防资源泄露
            if 'NeedExit' in locals() and NeedExit:
                try:
                    if not getattr(self.controller, 'driver', None):
                        loop = None
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = None
                        if loop and not loop.is_closed():
                            loop.close()
                except Exception:
                    pass
            # 释放进程内互斥锁
            if 'acquired' in locals() and acquired:
                LOGIN_MUTEX.release()
            self.release_lock()
            if "controller" in locals() and NeedExit:
                self.Clean()
            else:
                pass
        return self.SESSION

    def format_token(self, cookies: any, token=""):
        cookies_str = ""
        for cookie in cookies:
            cookies_str += f"{cookie['name']}={cookie['value']}; "
            if "token" in cookie["name"].lower():
                token = cookie["value"]
        # 计算 slave_sid cookie 有效时间
        cookie_expiry = expire(cookies)
        return {
            "cookies": cookies,
            "cookies_str": cookies_str,
            "token": token,
            "wx_login_url": self.wx_login_url,
            "expiry": cookie_expiry,
        }

    def Call_Success(self):
        """处理登录成功后的回调逻辑"""
        if not hasattr(self, "controller") or self.controller is None:
            print_error("浏览器控制器未初始化")
            return None

        # 获取token
        token = self.extract_token_from_requests()

        try:
            # 使用更健壮的选择器定位元素
            self.ext_data = self._extract_wechat_data()
        except Exception as e:
            print_error(f"获取公众号信息失败: {str(e)}")
            self.ext_data = None

        # 获取当前所有cookie
        cookies = self.controller.get_cookies()
        self.SESSION = self.format_token(cookies, token)
        with self._login_lock:
            self.HasLogin = False if self.SESSION["expiry"] is None else True
        self.Clean()
        if self.HasLogin:
            Store.save(cookies)
            print_success("登录成功！")
            # 启动一次定时刷新（守护线程，内部已处理异常）
            try:
                self.schedule_refresh()
            except Exception:
                pass
        else:
            print_warning("未登录！")

        # print(cookie_expiry)
        if self.CallBack is not None:
            self.CallBack(self.SESSION, self.ext_data)

        return self.SESSION

    def _extract_wechat_data(self):
        """提取微信公众号数据"""
        page = getattr(self.controller, "page", None)
        if page is None:
            return {}
        data = {}
        selectors = {
            "wx_app_name": ".account-name",
            "wx_logo": ".account-avatar img",
            "wx_read_yesterday": ".data-item:nth-child(1) .number",
            "wx_share_yesterday": ".data-item:nth-child(2) .number",
            "wx_watch_yesterday": ".data-item:nth-child(3) .number",
            "wx_yuan_count": ".original-count .number",
            "wx_user_count": ".user-count .number",
        }
        for key, selector in selectors.items():
            try:
                loc = page.locator(selector)
                if key == "wx_logo":
                    data[key] = loc.first.get_attribute("src") or ""
                else:
                    data[key] = (loc.first.inner_text(timeout=2_000) or "").strip()
            except Exception as e:
                print_warning(f"获取{key}失败: {str(e)}")
                data[key] = ""
        return data

    def cleanup_resources(self):
        """清理所有相关资源"""
        try:
            # 清理临时文件
            self.Clean()

            # 重置状态
            with self._login_lock:
                self.HasLogin = False
                self.HasCode = False

            print_info("资源清理完成")
            return True
        except Exception as e:
            return False

    def Close(self):
        rel = False
        try:
            if hasattr(self, "controller") and self.controller is not None:
                self.controller.cleanup()
                rel = True
        except Exception as e:
            print("浏览器未启动")
            # print(e)
            pass
        return rel

    def Clean(self):
        try:
            os.remove(self.wx_login_url)
        except:
            pass
        finally:
            pass

    def expire_all_cookies(self):
        """设置所有cookie为过期状态"""
        try:
            if hasattr(self, "controller") and hasattr(self.controller, "context"):
                self.controller.context.clear_cookies()
                return True
            else:
                print("浏览器未启动，无法操作cookie")
                return False
        except Exception as e:
            print(f"设置cookie过期时出错: {str(e)}")
            return False

    def check_lock(self):
        """检查锁定状态"""
        return os.path.exists(self.lock_file_path)

    def set_lock(self):
        """创建锁定文件"""
        with open(self.lock_file_path, "w") as f:
            f.write(str(time.time()))
        self.isLOCK = True

    def release_lock(self):
        """删除锁定文件"""
        try:
            os.remove(self.lock_file_path)
            self.isLOCK = False
            return True
        except:
            return False


def DoSuccess(cookies: any) -> dict:
    data = WX_API.format_token(cookies)
    Success(data)


WX_API = Wx()


def GetCode(CallBack: any = None, NeedExit=True):
    WX_API.GetCode(CallBack)
