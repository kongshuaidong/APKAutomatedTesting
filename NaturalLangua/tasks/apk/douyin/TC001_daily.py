# ============================================================
# 【抖音 APK】case_daily.py
# 用例：每日定时任务（打开 → 同城 → 搜索 → 播放 → 退出）
# 抖音每日定时任务用例（通过 run_apk_tests.py --apk douyin 或 scheduler.py 执行）
# ============================================================

from tasks.apk.douyin import config as cfg
from tasks.apk.douyin.helpers import (
    click_first_video,
    click_search_button,
    open_search,
    switch_city_to_shenzhen,
)
from tasks.framework.base_case import ApkTestCase


class CaseDaily(ApkTestCase):
    case_id = "TC001_daily"
    case_name = "TC001_抖音每日任务"
    case_desc = "打开抖音、切换深圳、搜索视频、播放、退出"

    def run_steps(self) -> None:
        pkg = cfg.PACKAGE

        # ── 步骤 1：打开抖音 ───────────────────────────────────────────────
        self.app.launch_app(pkg)
        self.wait(4)
        self.assert_step(self.is_foreground(pkg), f"抖音应在前台，包名 {pkg}")

        # ── 步骤 2：切换频道到深圳 ─────────────────────────────────────────
        switch_city_to_shenzhen(self.d, self.ui, cfg.DAILY_CITY)
        self.wait(2)
        self.assert_step(self.is_foreground(pkg), "城市切换后应仍在抖音内")

        # ── 步骤 3：搜索 ───────────────────────────────────────────────────
        open_search(self.d)
        self.wait(1)
        search_input_visible = (
            self.d(focused=True).exists
            or self.d(resourceId="com.ss.android.ugc.aweme:id/search_edit_text").exists
            or self.d(resourceId="com.ss.android.ugc.aweme:id/et_search_kw").exists
            or self.d(className="android.widget.EditText").exists
        )
        self.assert_step(search_input_visible, "搜索输入框应出现")

        self.ui.input_text(cfg.DAILY_SEARCH_KEYWORD)
        self.wait(1)
        edit = self.d(className="android.widget.EditText")
        input_not_empty = edit.exists and (edit.get_text() or "").strip() != ""
        self.assert_step(input_not_empty, "搜索框内容不应为空")

        # ── 步骤 4：点击搜索 ─────────────────────────────────────────────────
        click_search_button(self.d)
        self.wait(3)
        results_loaded = (
            self.d(resourceId="com.ss.android.ugc.aweme:id/cover").exists
            or self.d(resourceId="com.ss.android.ugc.aweme:id/video_cover_layout").exists
            or self.d(resourceId="com.ss.android.ugc.aweme:id/thumbnail").exists
            or self.d(description="视频封面").exists
            or not self.d(focused=True).exists
        )
        self.assert_step(results_loaded, "应出现搜索结果列表")

        # ── 步骤 5：上滑并点击第一个视频 ───────────────────────────────────
        self.ui.swipe("up")
        self.wait(1)
        click_first_video(self.d)
        self.wait(5)
        player_opened = (
            self.d(textContains="评论").exists
            or self.d(descriptionContains="评论").exists
        )
        self.assert_step(player_opened, "应进入视频播放页（底部有评论框）")

        # ── 步骤 6：退出抖音 ─────────────────────────────────────────────────
        self.app.stop_app(pkg)
        self.wait(1)
        self.assert_step(not self.is_foreground(pkg), "退出后抖音不应在前台")
