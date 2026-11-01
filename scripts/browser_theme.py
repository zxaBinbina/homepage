"""Select a theme preference through the shared three-mode button."""
from playwright.sync_api import expect


def wait_theme_settled(page):
    page.wait_for_function('''() => !document.documentElement.getAnimations()
        .some(animation => animation.id === 'theme-colors')''')


def set_theme_mode(page, mode):
    assert mode in ('dark', 'light', 'auto')
    button = page.locator('.theme-toggle')
    expect(button).to_be_visible()
    for _ in range(3):
        if button.get_attribute('data-mode') == mode:
            break
        button.click()
    expect(button).to_have_attribute('data-mode', mode)
    expect(page.locator('html')).to_have_attribute('data-theme-mode', mode)
    wait_theme_settled(page)
