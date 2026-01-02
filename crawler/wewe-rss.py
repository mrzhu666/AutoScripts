"""
Selenium 爬虫：打开 wewe-rss 仪表板页面
用于后续读取左边列表并逐个点击更新
"""

import logging
from typing import Optional
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
