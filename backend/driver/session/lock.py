import os
import time
import threading
from core.common.print import print_warning


# 进程内登录互斥，防止并发登录/重复扫码
# 该锁仅限于当前进程内，无法跨进程同步
LOGIN_MUTEX = threading.Lock()

# 锁的 TTL（存活时间），过期后认为锁失效
# 目的是防止死锁（如进程崩溃导致锁文件未删除）
LOCK_TTL_SECONDS = 10 * 60  # 10 minutes


class LockManager:
    """
    跨进程锁管理：基于文件的原子创建 + TTL 超时清理 + PID 存活校验 + owner 防误删机制。

    锁通过原子创建文件（O_EXCL）实现互斥，防止多个进程同时持有锁。
    通过 TTL 控制锁的最大存活时间，避免因异常退出导致的死锁。
    通过检查锁文件中记录的 PID 是否存活，进一步判断锁是否有效。
    记录锁的拥有者 PID，防止非拥有者误删锁文件，保证锁的安全释放。
    """

    def __init__(self, lock_file_path: str, ttl_seconds: int = LOCK_TTL_SECONDS):
        self.lock_file_path = lock_file_path
        self.ttl_seconds = ttl_seconds
        self._owner_pid = None
        self._owner_ts = None

    def is_locked(self) -> bool:
        """
        判断当前是否存在有效锁。

        逻辑：
        1. 若锁文件不存在，返回 False。
        2. 读取锁文件内容，解析 PID 和时间戳。
        3. 检查 TTL 是否过期，过期则删除锁文件并返回 False。
        4. 检查 PID 是否存活，若不存在则删除锁文件并返回 False。
        5. 否则返回 True，表示锁有效。
        """
        try:
            if not os.path.exists(self.lock_file_path):
                return False

            with open(self.lock_file_path, "r") as f:
                content = (f.read() or "").strip()

            pid = None
            ts = None
            if content:
                parts = content.split(",")
                if len(parts) >= 2:
                    try:
                        pid = int(parts[0])
                    except Exception:
                        pid = None
                    try:
                        ts = float(parts[1])
                    except Exception:
                        ts = None

            now = time.time()

            # TTL 过期：清理锁文件，认为锁失效
            if ts is None or (now - ts) > self.ttl_seconds:
                try:
                    os.remove(self.lock_file_path)
                except Exception:
                    pass
                return False

            # PID 不存在（进程已退出）：清理锁文件，认为锁失效
            if pid is not None:
                try:
                    os.kill(pid, 0)
                except Exception:
                    try:
                        os.remove(self.lock_file_path)
                    except Exception:
                        pass
                    return False

            # 锁有效
            return True
        except Exception as e:
            print_warning(f"检查锁失败: {str(e)}")
            return False

    def try_acquire(self) -> bool:
        """
        尝试抢占锁（通过原子创建文件实现）。
        成功返回 True，失败返回 False。

        实现细节：
        - 利用 os.O_CREAT | os.O_EXCL 保证文件原子创建，防止竞争条件。
        - 创建失败（文件已存在）表示锁已被占用。
        - 其他异常会打印警告并返回失败。
        """
        try:
            dirpath = os.path.dirname(self.lock_file_path)
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)
            pid = os.getpid()
            ts = time.time()

            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            fd = os.open(self.lock_file_path, flags)
            with os.fdopen(fd, "w") as f:
                f.write(f"{pid},{ts}")

            self._owner_pid = pid
            self._owner_ts = ts
            return True
        except FileExistsError:
            # 文件已存在，锁被占用，抢锁失败
            self._owner_pid = None
            self._owner_ts = None
            return False
        except Exception as e:
            print_warning(f"创建锁失败: {str(e)}")
            return False

    def release(self) -> bool:
        """
        释放锁：仅当确认当前进程是锁的拥有者时才删除锁文件。

        保护措施：
        - 读取锁文件中的 PID，若与当前记录的拥有者 PID 不符，则拒绝删除，防止误删他人锁。
        - 若锁文件无法解析 PID，保守起见不删除。
        - 锁文件不存在时视为已释放，返回成功。
        - 出现异常时打印警告并返回失败。
        """
        try:
            if not os.path.exists(self.lock_file_path):
                return True

            with open(self.lock_file_path, "r") as f:
                content = (f.read() or "").strip()

            parts = content.split(",") if content else []
            owner_pid = None
            if len(parts) >= 1:
                try:
                    owner_pid = int(parts[0])
                except Exception:
                    owner_pid = None

            # 仅当确认是自己创建的锁时才允许删除
            if owner_pid is not None:
                if self._owner_pid is None or owner_pid != self._owner_pid:
                    return False
            else:
                # 无法解析 owner pid 时，保守起见不删除
                return False

            os.remove(self.lock_file_path)
            return True
        except Exception as e:
            print_warning(f"释放锁失败: {str(e)}")
            return False
