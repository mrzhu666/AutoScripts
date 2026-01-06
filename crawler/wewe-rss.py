"""
Selenium 爬虫：打开 wewe-rss 仪表板页面
用于后续读取左边列表并逐个点击更新
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class FeedItem:
    """左侧订阅列表中的单条数据项。"""

    title: str
    href: str
    data_key: str


def create_webdriver(chrome_driver_path: Optional[str] = None) -> WebDriver:
    """
    创建并配置 Chrome WebDriver 实例。

    Args:
        chrome_driver_path: ChromeDriver 可执行文件的路径，如果为 None 则使用系统 PATH。

    Returns:
        WebDriver: 配置好的 Chrome WebDriver 实例。

    Raises:
        WebDriverException: 当 WebDriver 初始化失败时抛出。

    Example:
        >>> driver = create_webdriver()
        >>> driver.get("http://example.com")
    """
    try:
        chrome_options = Options()
        # 可选：无头模式（取消注释以启用）
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        if chrome_driver_path:
            service = Service(executable_path=chrome_driver_path)
            driver: Chrome = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        logger.info("WebDriver 初始化成功")
        return driver
        
    except WebDriverException as e:
        logger.error(f"WebDriver 初始化失败: {e}")
        raise


def navigate_to_page(driver: WebDriver, url: str, timeout: int = 10) -> bool:
    """
    导航到指定 URL 并等待页面加载完成。

    Args:
        driver: WebDriver 实例。
        url: 要打开的 URL。
        timeout: 等待页面加载的超时时间（秒），默认为 10 秒。

    Returns:
        bool: 如果页面成功加载返回 True，否则返回 False。

    Example:
        >>> driver = create_webdriver()
        >>> success = navigate_to_page(driver, "http://example.com")
        >>> if success:
        ...     print("页面加载成功")
    """
    try:
        logger.info(f"正在打开页面: {url}")
        driver.get(url)
        
        # 等待页面加载完成（检查 document.readyState）
        wait = WebDriverWait(driver, timeout)
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        logger.info(f"页面加载成功: {driver.title}")
        return True
        
    except TimeoutException as e:
        logger.error(f"页面加载超时: {e}")
        return False
    except WebDriverException as e:
        logger.error(f"页面导航失败: {e}")
        return False


def load_cookies_from_file(cookie_file_path: str) -> list[dict[str, str]]:
    """
    从文件中读取 cookie 字符串并解析为字典列表。
    
    文件格式应为标准浏览器 cookie 字符串格式：
    key1=value1; key2=value2; key3=value3
    
    Args:
        cookie_file_path: cookie 文件的路径。
        
    Returns:
        list[dict[str, str]]: Cookie 字典列表，每个字典包含 'name' 和 'value' 键。
        
    Raises:
        FileNotFoundError: 当 cookie 文件不存在时抛出。
        ValueError: 当 cookie 格式无效时抛出。
        
    Example:
        >>> cookies = load_cookies_from_file("cookies.txt")
        >>> print(len(cookies))
        5
    """
    cookie_path = Path(cookie_file_path)
    
    if not cookie_path.exists():
        raise FileNotFoundError(f"Cookie 文件不存在: {cookie_file_path}")
    
    try:
        cookie_content = cookie_path.read_text(encoding='utf-8').strip()
        
        if not cookie_content:
            logger.warning("Cookie 文件为空")
            return []
        
        cookies: list[dict[str, str]] = []
        # 按分号分割多个 cookie
        cookie_pairs = cookie_content.split(';')
        
        for pair in cookie_pairs:
            pair = pair.strip()
            if not pair:
                continue
            
            # 按等号分割键值对（只分割第一个等号，因为值中可能包含等号）
            if '=' not in pair:
                logger.warning(f"跳过无效的 cookie 项: {pair}")
                continue
            
            key, value = pair.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            cookies.append({'name': key, 'value': value})
        
        logger.info(f"成功解析 {len(cookies)} 个 cookie")
        return cookies
        
    except Exception as e:
        logger.error(f"读取或解析 cookie 文件失败: {e}")
        raise ValueError(f"Cookie 文件格式无效: {e}") from e


def set_cookies_from_file(driver: WebDriver, cookie_file_path: str, domain: Optional[str] = None) -> bool:
    """
    从文件中读取 cookie 并设置到浏览器中。
    
    注意：在设置 cookie 之前，必须先访问目标域名。
    
    Args:
        driver: WebDriver 实例。
        cookie_file_path: cookie 文件的路径。
        domain: cookie 的域名，如果为 None 则从当前 URL 提取。
        
    Returns:
        bool: 如果所有 cookie 设置成功返回 True，否则返回 False。
        
    Example:
        >>> driver = create_webdriver()
        >>> driver.get("http://example.com")
        >>> success = set_cookies_from_file(driver, "cookies.txt")
        >>> if success:
        ...     print("Cookie 设置成功")
    """
    try:
        cookies = load_cookies_from_file(cookie_file_path)
        
        if not cookies:
            logger.warning("没有可设置的 cookie")
            return False
        
        # 获取当前 URL 和解析域名
        current_url = driver.current_url
        parsed_url = urlparse(current_url)
        
        # 如果没有指定域名，从当前 URL 提取
        if domain is None:
            domain = parsed_url.netloc
        
        # Selenium 的 domain 不能包含端口号，需要移除
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # 构建根路径 URL（协议 + 域名）
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # 先访问根路径以确保在正确的域名下
        logger.info(f"访问根路径以准备设置 cookie: {base_url}")
        driver.get(base_url)
        
        # 等待页面加载
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        success_count = 0
        failed_count = 0
        failed_cookies: list[str] = []
        
        for cookie_dict in cookies:
            try:
                # 创建新的 cookie 字典（避免修改原始数据）
                cookie_to_add = {
                    'name': cookie_dict['name'],
                    'value': cookie_dict['value'],
                    'domain': domain,
                }
                
                # 添加 path（默认为根路径）
                cookie_to_add['path'] = '/'
                
                driver.add_cookie(cookie_to_add)
                success_count += 1
                logger.debug(f"成功设置 cookie: {cookie_dict['name']}")
            except Exception as e:
                failed_cookies.append(f"{cookie_dict.get('name', 'unknown')}: {str(e)}")
                logger.warning(f"设置 cookie '{cookie_dict.get('name', 'unknown')}' 失败: {e}")
                failed_count += 1
        
        if success_count > 0:
            logger.info(f"成功设置 {success_count} 个 cookie，失败 {failed_count} 个")
            if failed_cookies:
                logger.debug(f"失败的 cookie 详情: {failed_cookies[:3]}")  # 只显示前3个
        
        # 返回原页面并刷新以应用 cookie
        logger.info(f"返回原页面: {current_url}")
        driver.get(current_url)
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        logger.info("已返回原页面并应用 cookie")
        
        return failed_count == 0
        
    except FileNotFoundError as e:
        logger.error(f"Cookie 文件未找到: {e}")
        return False
    except ValueError as e:
        logger.error(f"Cookie 格式错误: {e}")
        return False
    except WebDriverException as e:
        logger.error(f"设置 cookie 时发生 WebDriver 错误: {e}")
        return False


def enter_auth_code(driver: WebDriver, auth_code: str, timeout: int = 10) -> bool:
    """
    在页面中找到 AuthCode 文本输入框并输入密钥。

    本函数会等待输入框出现，清空原有内容并输入新的密钥，
    然后读取输入框的实际值进行校验。

    Args:
        driver: 已经打开目标页面的 WebDriver 实例。
        auth_code: 需要输入的认证密钥字符串。
        timeout: 等待输入框出现的超时时间（秒），默认 10 秒。

    Returns:
        bool: 如果成功输入且校验通过返回 True，否则返回 False。

    Raises:
        WebDriverException: 当发生底层 WebDriver 错误时抛出。

    Example:
        >>> driver = create_webdriver()
        >>> navigate_to_page(driver, "http://desktop-wsl-tailscale:4000/dash")
        >>> ok = enter_auth_code(driver, "123567")
        >>> print(ok)
        True
    """
    try:
        logger.info("开始查找 AuthCode 输入框并输入密钥")
        wait = WebDriverWait(driver, timeout)

        # 优先通过 aria-label 精确定位该输入框
        input_locator = (By.CSS_SELECTOR, 'input[aria-label="AuthCode"]')

        input_element = wait.until(EC.presence_of_element_located(input_locator))
        logger.debug("已找到 AuthCode 输入框，开始输入密钥")

        input_element.clear()
        input_element.send_keys(auth_code)

        real_value = input_element.get_attribute("value") or ""
        if real_value == auth_code:
            logger.info("密钥输入成功并通过校验")
            return True

        logger.warning(
            "密钥输入后校验失败，期望值为 '%s'，实际值为 '%s'",
            auth_code,
            real_value,
        )
        return False

    except TimeoutException as exc:
        logger.error("在页面中查找 AuthCode 输入框超时: %s", exc)
        return False
    except WebDriverException as exc:
        logger.error("输入 AuthCode 时发生 WebDriver 错误: %s", exc)
        raise


def click_auth_confirm_button(driver: WebDriver, timeout: int = 10) -> bool:
    """
    点击页面中的“确认”按钮以提交已输入的密钥。

    本函数会等待按钮变为可点击状态，然后执行点击操作。
    可以根据需要在后续扩展为等待特定页面状态变化。

    Args:
        driver: 已经打开目标页面并输入密钥的 WebDriver 实例。
        timeout: 等待按钮可点击的超时时间（秒），默认 10 秒。

    Returns:
        bool: 如果按钮成功点击返回 True，否则返回 False。

    Raises:
        WebDriverException: 当发生底层 WebDriver 错误时抛出。
    """
    try:
        logger.info("开始查找并点击“确认”按钮")
        wait = WebDriverWait(driver, timeout)

        # 通过按钮文字“确认”以及 type=button 进行定位，避免依赖长 class
        button_locator = (
            By.XPATH,
            '//button[@type="button" and normalize-space(text())="确认"]',
        )

        button_element = wait.until(EC.element_to_be_clickable(button_locator))
        button_element.click()
        logger.info("已点击“确认”按钮")

        # 这里暂不强行等待特定状态，可以在后续任务中根据实际页面再细化校验
        return True

    except TimeoutException as exc:
        logger.error("在页面中查找或点击“确认”按钮超时: %s", exc)
        return False
    except WebDriverException as exc:
        logger.error("点击“确认”按钮时发生 WebDriver 错误: %s", exc)
        raise


def read_left_feed_list(driver: WebDriver, timeout: int = 10) -> list[FeedItem]:
    """
    读取左侧订阅列表，并返回其中所有条目的结构化数据。

    本函数会等待列表至少出现一条记录，然后解析每个条目的标题、
    链接 href 以及 data-key。列表长度是动态的，会根据当前页面实际
    渲染的条目数量返回对应长度的列表。

    Args:
        driver: 已经完成认证并进入仪表盘页面的 WebDriver 实例。
        timeout: 等待列表元素出现的超时时间（秒），默认 10 秒。

    Returns:
        list[FeedItem]: 订阅条目数据列表，如果没有找到则返回空列表。
    """
    try:
        logger.info("开始读取左侧订阅列表")
        wait = WebDriverWait(driver, timeout)

        # 根据提供的结构：li[data-slot=\"base\"] 下的 ul[role=\"group\"] 中的 a[role=\"option\"]
        items_locator = (
            By.CSS_SELECTOR,
            'li[data-slot="base"] ul[role="group"] a[role="option"]',
        )

        elements = wait.until(EC.presence_of_all_elements_located(items_locator))

        feed_items: list[FeedItem] = []
        for element in elements:
            # 文本标题位于内部 span[data-label=true]
            title_span = element.find_element(By.CSS_SELECTOR, 'span[data-label="true"]')
            title = (title_span.text or "").strip()
            href = element.get_attribute("href") or ""
            data_key = element.get_attribute("data-key") or ""

            feed_items.append(
                FeedItem(
                    title=title,
                    href=href,
                    data_key=data_key,
                )
            )

        logger.info("成功读取左侧订阅列表，共 %d 项", len(feed_items))

        # 为了快速人工验证，打印前几项
        for idx, item in enumerate(feed_items[:5], start=1):
            logger.info(
                "订阅项 %d: title='%s', data_key='%s', href='%s'",
                idx,
                item.title,
                item.data_key,
                item.href,
            )

        return feed_items

    except TimeoutException as exc:
        logger.warning("未能在页面中找到左侧订阅列表: %s", exc)
        return []
    except WebDriverException as exc:
        logger.error("读取左侧订阅列表时发生 WebDriver 错误: %s", exc)
        raise


def click_update_link_and_wait(driver: WebDriver, timeout: int = 60) -> bool:
    """
    点击“立即更新”按钮，并等待一次完整的更新状态周期。

    本函数会：
    1. 找到并点击文本为“立即更新”的链接；
    2. 等待其文本变为“更新中...”；
    3. 再等待其文本恢复为“立即更新”，表示后端处理完成。

    Args:
        driver: 当前停留在某个订阅详情页面的 WebDriver 实例。
        timeout: 整个更新流程的最大等待时间（秒），默认 60 秒。

    Returns:
        bool: 如果状态按预期从“立即更新”→“更新中...”→“立即更新”则返回 True，
            否则返回 False。
    """
    wait = WebDriverWait(driver, timeout)

    update_locator = (
        By.XPATH,
        '//a[@role="link" and @href="#" and normalize-space(text())="立即更新"]',
    )
    updating_locator = (
        By.XPATH,
        '//a[@role="link" and @href="#" and normalize-space(text())="更新中..."]',
    )

    try:
        # 第一步：点击“立即更新”
        logger.info("开始查找并点击“立即更新”按钮")
        update_element = wait.until(EC.element_to_be_clickable(update_locator))
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'nearest'});",
            update_element,
        )
        update_element.click()

        # 第二步：等待文本变为“更新中...”
        logger.info("等待“立即更新”按钮进入“更新中...”状态")
        wait.until(EC.presence_of_element_located(updating_locator))

        # 第三步：等待文本恢复为“立即更新”
        logger.info("等待更新完成，“更新中...”恢复为“立即更新”")
        wait.until(EC.element_to_be_clickable(update_locator))

        logger.info("本次“立即更新”流程完成")
        return True

    except TimeoutException as exc:
        logger.warning("等待“立即更新”状态变化超时: %s", exc)
        return False
    except WebDriverException as exc:
        logger.warning("点击或等待“立即更新”时发生 WebDriver 错误: %s", exc)
        return False


def click_all_feed_items(
    driver: WebDriver,
    timeout: int = 10,
    delay_seconds: float = 0.5,
) -> int:
    """
    依次点击左侧订阅列表中的每一项。

    为避免元素失效（StaleElementReference），每次点击前都会重新获取
    当前列表，并按索引定位需要点击的元素。

    Args:
        driver: 已经完成认证并进入仪表盘页面的 WebDriver 实例。
        timeout: 等待列表元素出现的超时时间（秒），默认 10 秒。
        delay_seconds: 每次点击之间的间隔时间（秒），默认 0.5 秒。

    Returns:
        int: 实际成功完成“点击列表项 + 更新”的列表项数量。
    """
    items_locator = (
        By.CSS_SELECTOR,
        'li[data-slot="base"] ul[role="group"] a[role="option"]',
    )

    wait = WebDriverWait(driver, timeout)

    try:
        elements = wait.until(EC.presence_of_all_elements_located(items_locator))
    except TimeoutException as exc:
        logger.warning("等待左侧订阅列表用于点击时超时: %s", exc)
        return 0

    total = len(elements)
    if total == 0:
        logger.info("左侧订阅列表为空，无法进行点击操作")
        return 0

    logger.info("准备依次点击左侧订阅列表中的 %d 项", total)

    clicked = 0
    for index in range(total):
        try:
            # 每次重新获取当前所有元素，避免 StaleElementReference
            current_elements = wait.until(
                EC.presence_of_all_elements_located(items_locator)
            )
            if index >= len(current_elements):
                logger.warning("索引 %d 超出当前列表长度 %d，停止点击", index, len(current_elements))
                break

            element = current_elements[index]

            # 获取一些日志信息（标题和 data-key）
            try:
                title_span = element.find_element(
                    By.CSS_SELECTOR, 'span[data-label="true"]'
                )
                title_text = (title_span.text or "").strip()
            except WebDriverException:
                title_text = ""

            data_key = element.get_attribute("data-key") or ""

            # 第一项通常为“全部”，不对应实际订阅内容，跳过
            if index == 0 or title_text == "全部":
                logger.info(
                    "跳过第 %d 项无效订阅项: title='%s', data_key='%s'",
                    index + 1,
                    title_text,
                    data_key,
                )
                continue

            logger.info(
                "处理第 %d 项订阅: title='%s', data_key='%s'",
                index + 1,
                title_text,
                data_key,
            )

            # 确保元素在可视区域并且可点击
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'nearest'});",
                element,
            )
            wait.until(EC.element_to_be_clickable(element))
            element.click()

            # 每点击一个订阅项后，执行一次“立即更新”并等待完成
            update_ok = click_update_link_and_wait(driver, timeout=60)
            if not update_ok:
                logger.warning(
                    "第 %d 项订阅的“立即更新”流程可能未成功，请手动检查页面状态",
                    index + 1,
                )
            else:
                clicked += 1

            time.sleep(delay_seconds)
        except TimeoutException as exc:
            logger.warning("第 %d 项点击超时: %s", index + 1, exc)
        except WebDriverException as exc:
            logger.warning("点击第 %d 项订阅时发生 WebDriver 错误: %s", index + 1, exc)

    logger.info("列表项点击完成，共成功点击 %d/%d 项", clicked, total)
    return clicked


def main() -> None:
    """
    主函数：创建 WebDriver 并打开目标页面。
    """
    driver: Optional[WebDriver] = None
    target_url = "http://desktop-wsl-tailscale:4000/dash"
    auth_code = "123567"
    
    try:
        # 创建 WebDriver
        driver = create_webdriver()
        
        # 打开目标页面
        success = navigate_to_page(driver, target_url, timeout=15)
        
        if success:
            # 设置 cookie
            cookie_file = Path(__file__).parent / "wewe-rrs-cookie.txt"
            cookie_set = set_cookies_from_file(driver, str(cookie_file))

            if cookie_set:
                logger.info("Cookie 设置成功")
            else:
                logger.warning("Cookie 设置失败，但继续执行")

            # 任务 2：在页面中输入认证密钥
            auth_ok = enter_auth_code(driver, auth_code, timeout=10)
            if not auth_ok:
                logger.warning("认证密钥输入可能未生效，请手动检查页面状态")

            # 任务 3：点击“确认”按钮提交密钥
            confirm_ok = click_auth_confirm_button(driver, timeout=10)
            if not confirm_ok:
                logger.warning("“确认”按钮点击可能未成功，请手动检查页面状态")

            # 任务 4：读取左侧订阅列表（列表项数量是动态的）
            feed_items = read_left_feed_list(driver, timeout=10)
            if not feed_items:
                logger.warning("左侧订阅列表为空或读取失败，请手动检查页面状态")

            # 任务 5：依次点击左侧列表中的每一项
            clicked_count = click_all_feed_items(driver, timeout=10, delay_seconds=0.5)
            logger.info("已尝试点击左侧所有列表项，成功点击数量: %d", clicked_count)

            logger.info(
                "页面已成功打开、输入密钥、点击确认、读取并尝试点击左侧列表，可以开始后续操作"
            )
            # 保持浏览器打开，等待用户操作或后续任务
            input("按 Enter 键关闭浏览器...")
        else:
            logger.error("页面打开失败")
            
    except WebDriverException as e:
        logger.error(f"发生错误: {e}")
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {e}")


if __name__ == "__main__":
    main()
