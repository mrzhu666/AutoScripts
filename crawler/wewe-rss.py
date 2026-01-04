"""
Selenium 爬虫：打开 wewe-rss 仪表板页面
用于后续读取左边列表并逐个点击更新
"""

import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
            driver = webdriver.Chrome(service=service, options=chrome_options)
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


def main() -> None:
    """
    主函数：创建 WebDriver 并打开目标页面。
    """
    driver: Optional[WebDriver] = None
    target_url = "http://desktop-wsl-tailscale:4000/dash"
    
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
            
            logger.info("页面已成功打开，可以开始后续操作")
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
