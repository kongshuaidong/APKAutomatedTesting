# ============================================================
# 【设备层】app_controller.py
# 职责：通过包名（package name）控制 App 的启动、停止、重启
# 依赖库：uiautomator2（底层调用 am start / am force-stop 等 ADB 命令）
# ============================================================

import uiautomator2 as u2
from utils.logger import logger


class AppController:
    """Android App 生命周期控制器"""

    def __init__(self, device: u2.Device):
        # uiautomator2 设备对象，所有操作通过它转发给手机
        self.d = device

    def launch_app(self, package_name: str, activity: str = None):
        """
        通过包名启动 App。
        - package_name：如 com.ss.android.ugc.aweme（抖音）
        - activity：可选，指定启动页；不填则打开 App 默认主页
        底层等价于：adb shell am start -n <package>/<activity>
        """
        logger.info(f"Launching app: {package_name}")
        if activity:
            self.d.app_start(package_name, activity)
        else:
            self.d.app_start(package_name)

    def stop_app(self, package_name: str):
        """
        强制停止 App（类似 Android 设置里的"强行停止"）。
        底层等价于：adb shell am force-stop <package>
        """
        logger.info(f"Stopping app: {package_name}")
        self.d.app_stop(package_name)

    def restart_app(self, package_name: str):
        """先强停再启动，实现 App 重启"""
        logger.info(f"Restarting app: {package_name}")
        self.d.app_stop(package_name)
        self.d.app_start(package_name)

    def get_current_app(self) -> dict:
        """
        获取当前前台运行的 App 信息。
        返回字典包含：package（包名）、activity（当前页面）、pid（进程ID）
        """
        info = self.d.app_current()
        logger.debug(f"Current app: {info}")
        return info

    def list_installed_apps(self, third_party_only: bool = True) -> list:
        """
        获取手机上已安装的 App 包名列表。
        - third_party_only=True：只返回用户安装的第三方 App（过滤系统应用）
        """
        apps = self.d.app_list(third_only=third_party_only)
        return apps

    def get_app_info(self, package_name: str) -> dict:
        """获取指定 App 的详细信息（版本号、安装时间等）"""
        info = self.d.app_info(package_name)
        return info

    def clear_app_data(self, package_name: str):
        """
        清除 App 数据和缓存（相当于手机设置里的"清除数据"）。
        底层等价于：adb shell pm clear <package>
        """
        logger.info(f"Clearing data for: {package_name}")
        self.d.app_clear(package_name)
