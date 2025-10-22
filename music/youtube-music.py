import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 爬虫抓取youtube音乐的URL
# 输入歌曲名称，网站：https://music.youtube.com/，搜索歌曲，
# 点击网页歌曲标签，然后抓取前10首歌曲的URL

def get_music_urls(song_name):
    # 启动Chrome浏览器
    driver = webdriver.Chrome()
    driver.get('https://music.youtube.com/')
    time.sleep(2)

    # 查找搜索框并输入歌曲名
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'input'))
    )
    search_box.send_keys(song_name)
    search_box.send_keys(Keys.ENTER)
    
    # 等待搜索结果页加载并点击“歌曲/Songs”标签
    try:
        songs_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//ytmusic-chip-cloud-chip-renderer[.//yt-formatted-string[contains(., '歌曲') or contains(., 'Songs')]]"
            ))
        )
        songs_tab.click()
        # 等待歌曲结果区域更新
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'ytmusic-responsive-list-item-renderer'))
        )
        time.sleep(1)
    except Exception:
        # 如果没有找到歌曲标签，继续尝试直接从当前结果中解析
        pass

    # 查找前10个歌曲搜索结果的信息（标题、作者、时长、播放次数、URL）
    # 搜索结果项组件：ytmusic-responsive-list-item-renderer
    try:
        # 等待结果加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'ytmusic-responsive-list-item-renderer'))
        )
        results = driver.find_elements(By.TAG_NAME, 'ytmusic-responsive-list-item-renderer')
        if not results:
            print('未找到搜索结果')
            return []

        base_url = 'https://music.youtube.com/'
        items = []
        for item in results[:10]:
            try:
                # 标题与URL（多种选择器回退）
                title = ''
                url = ''
                href = ''
                title_link = None
                try:
                    title_link = item.find_element(By.CSS_SELECTOR, 'yt-formatted-string.title a')
                except Exception:
                    try:
                        title_link = item.find_element(By.CSS_SELECTOR, 'a.yt-simple-endpoint[href^="watch?"]')
                    except Exception:
                        pass
                if title_link is not None:
                    # 优先使用 title 属性，其次使用可见文本
                    title = (title_link.get_attribute('title') or title_link.text or '').strip()
                    href = title_link.get_attribute('href') or ''
                    url = href if href.startswith('http') else (base_url + href if href else '')
                else:
                    # 兜底：从播放按钮 aria-label 提取标题
                    try:
                        play_btn = item.find_element(By.CSS_SELECTOR, 'ytmusic-play-button-renderer')
                        aria = play_btn.get_attribute('aria-label') or ''
                        # 形如："Play Title - Artist" or "播放“标题 - 艺术家”"
                        m = re.search(r'(?:Play\s+|播放“)(.+?)(?:\s+-\s+|”\s*-\s*)(.+?)"?$', aria)
                        if m:
                            title = (m.group(1) or '').strip()
                    except Exception:
                        pass

                # 作者与时长（第一个 secondary flex column 文本形如：作者 • 歌曲或专辑 • 4:13）
                author = ''
                duration = ''
                try:
                    meta_primary = item.find_element(By.CSS_SELECTOR, 'div.secondary-flex-columns yt-formatted-string.flex-column')
                    # 优先使用 title 属性（更稳定，含分隔符），其次使用 aria-label，最后使用 text
                    meta_text = (
                        meta_primary.get_attribute('title')
                        or meta_primary.get_attribute('aria-label')
                        or meta_primary.text
                        or ''
                    ).strip()
                    parts = [p.strip() for p in meta_text.split('•')]
                    if len(parts) >= 1 and not author:
                        author = parts[0]
                    # 从末尾提取看起来像时长的字段
                    if not duration and parts:
                        last_part = parts[-1]
                        m = re.search(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', last_part)
                        if m:
                            duration = m.group(0)
                except Exception:
                    pass

                # 播放次数（第二个 secondary flex column，文本示例：1亿 次播放）
                play_count = ''
                try:
                    meta_columns = item.find_elements(By.CSS_SELECTOR, 'div.secondary-flex-columns yt-formatted-string.flex-column')
                    # 优先第二列；若只有一列，则尝试包含“播放”关键字的列
                    if len(meta_columns) >= 2 and not play_count:
                        play_count = (
                            meta_columns[1].get_attribute('title')
                            or meta_columns[1].get_attribute('aria-label')
                            or meta_columns[1].text
                            or ''
                        ).strip()
                    if not play_count:
                        for col in meta_columns:
                            txt = (
                                col.get_attribute('title')
                                or col.get_attribute('aria-label')
                                or col.text
                                or ''
                            ).strip()
                            low = txt.lower()
                            # 兼容不间断空格
                            normalized = txt.replace('\xa0', ' ')
                            low_norm = normalized.lower()
                            if ('播放' in normalized) or ('plays' in low_norm) or ('views' in low_norm):
                                play_count = normalized
                                break
                except Exception:
                    pass

                # 如果时长未能从分隔符中解析，尝试用时间格式匹配
                if not duration:
                    try:
                        meta_primary = item.find_element(By.CSS_SELECTOR, 'div.secondary-flex-columns yt-formatted-string.flex-column')
                        txt = (
                            meta_primary.get_attribute('title')
                            or meta_primary.get_attribute('aria-label')
                            or meta_primary.text
                            or ''
                        )
                        m = re.search(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', txt)
                        if m:
                            duration = m.group(0)
                    except Exception:
                        pass

                if url:
                    items.append({
                        'title': title,
                        'author': author,
                        'duration': duration,
                        'play_count': play_count,
                        'url': url
                    })
            except Exception:
                continue
        print('歌曲列表:')
        for idx, it in enumerate(items, 1):
            print(f"{idx}. 标题: {it['title']} | 作者: {it['author']} | 时长: {it['duration']} | 播放: {it['play_count']} | URL: {it['url']}")
        return items
    except Exception as e:
        print('抓取失败:', e)
        return []
    finally:
        driver.quit()

if __name__ == "__main__":
    song_name = input('请输入歌曲名称: ').strip()
    urls = get_music_urls(song_name)
