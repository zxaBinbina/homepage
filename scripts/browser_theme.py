"""Select a theme preference through the unified theme panel."""
from playwright.sync_api import expect

MODE_LABELS = {'dark': '深色', 'light': '浅色', 'auto': '自动'}


def wait_theme_settled(page):
    page.wait_for_function('''() => !document.documentElement.getAnimations()
        .some(animation => animation.id === 'theme-colors')''')


def set_theme_mode(page, mode):
    assert mode in ('dark', 'light', 'auto')
    button = page.locator('.theme-toggle')
    expect(button).to_be_visible()
    if button.get_attribute('data-mode') != mode:
        # 单一主题按钮改为打开统一面板；在「明暗模式」组内直接选择目标模式。
        if button.get_attribute('aria-expanded') != 'true':
            button.click()
        panel = page.locator('.theme-panel-popover')
        expect(panel).to_be_visible()
        panel.get_by_role('group', name='明暗模式').get_by_role(
            'button', name=MODE_LABELS[mode], exact=True
        ).click()
        # 收起面板，恢复与其他断言一致的页面状态（无浮层遮挡）。
        if button.get_attribute('aria-expanded') == 'true':
            page.keyboard.press('Escape')
        expect(panel).to_have_count(0)
    expect(button).to_have_attribute('data-mode', mode)
    expect(page.locator('html')).to_have_attribute('data-theme-mode', mode)
    wait_theme_settled(page)
