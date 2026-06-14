# ============================================================
# 【设备层】device_manager.py
# 职责：通过 ADB 协议管理手机连接与断开
# 依赖库：adbutils（封装了 ADB 命令，支持 USB / WiFi 连接）
# ============================================================

import adbutils
from utils.logger import logger


class DeviceManager:
    """ADB 设备连接管理器"""

    def __init__(self):
        # 连接本机 ADB 服务（默认端口 5037），adbutils 会自动启动 adb server
        self.adb = adbutils.AdbClient(host="127.0.0.1", port=5037)
        self.current_device = None  # 当前选中的设备对象

    def list_devices(self):
        """扫描并返回当前所有已连接的 ADB 设备列表"""
        try:
            devices = self.adb.device_list()
            logger.debug(f"Found {len(devices)} device(s)")
            return devices
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []

    def connect(self, serial=None):
        """
        连接指定设备。
        - serial 为 None 时自动选第一台设备（适合只插一台手机的场景）
        - serial 为具体序列号时精确连接（适合多设备并发场景）
        """
        devices = self.list_devices()
        if not devices:
            raise RuntimeError(
                "No devices found. Please connect your phone via USB or enable ADB over WiFi."
            )

        if serial:
            self.current_device = self.adb.device(serial)
        else:
            self.current_device = devices[0]  # 默认取第一台

        logger.info(f"Connected to device: {self.current_device.serial}")
        return self.current_device

    def connect_wifi(self, ip: str, port: int = 5555):
        """
        通过 WiFi ADB 连接手机（无需 USB 线）。
        前提：手机已开启 ADB over WiFi（开发者选项 → 无线调试）
        """
        address = f"{ip}:{port}"
        result = self.adb.connect(address)  # 发送 adb connect 指令
        logger.info(f"WiFi connect result: {result}")
        return self.connect(address)

    def disconnect(self):
        """断开当前设备连接，释放资源"""
        if self.current_device:
            try:
                self.adb.disconnect(self.current_device.serial)
                logger.info(f"Disconnected from {self.current_device.serial}")
            except Exception as e:
                logger.warning(f"Disconnect error: {e}")
            finally:
                self.current_device = None

    def get_device_info(self) -> dict:
        """
        读取手机基本信息（型号、品牌、Android 版本、序列号）。
        通过读取 Android 系统属性（ro.product.*）实现。
        """
        if not self.current_device:
            raise RuntimeError("No device connected.")
        props = {
            "model":   self.current_device.prop.get("ro.product.model", "Unknown"),
            "brand":   self.current_device.prop.get("ro.product.brand", "Unknown"),
            "android": self.current_device.prop.get("ro.build.version.release", "Unknown"),
            "serial":  self.current_device.serial,
        }
        return props
