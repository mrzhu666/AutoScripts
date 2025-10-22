# 获取wewe-rss全部更新请求
# 每日先登录账号，然后再运行这个脚本
# 会重复请求多次，因为有些微信号不能一次请求成功

import requests
import json
import time

def make_trpc_request():
    """
    模拟TRPC请求到feed.refreshArticles接口
    """
    
    # 请求URL
    url = "http://desktop-wsl-tailscale:4000/trpc/feed.refreshArticles?batch=1"
    
    # 请求头
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization": "123567",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "pragma": "no-cache",
        "referer": "http://desktop-wsl-tailscale:4000/dash/feeds"
    }
    
    # 请求体
    payload = {"0": {}}
    
    print("开始发送TRPC请求...")
    start_time = time.time()
    
    try:
        # 发送POST请求，设置较长的超时时间以匹配浏览器的70秒等待
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=120  # 设置2分钟超时
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"请求耗时: {elapsed_time:.2f}秒")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        # 无论状态码如何，都尝试解析JSON响应
        try:
            json_response = response.json()
            print(f"JSON响应: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
            
            # 检查是否有错误信息
            if isinstance(json_response, list) and len(json_response) > 0:
                first_item = json_response[0]
                if "error" in first_item:
                    error_info = first_item["error"]
                    print(f"\n=== 错误详情 ===")
                    print(f"错误消息: {error_info.get('message', 'N/A')}")
                    print(f"错误代码: {error_info.get('code', 'N/A')}")
                    if "data" in error_info:
                        data = error_info["data"]
                        print(f"HTTP状态: {data.get('httpStatus', 'N/A')}")
                        print(f"路径: {data.get('path', 'N/A')}")
                        print(f"错误代码: {data.get('code', 'N/A')}")
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print("响应不是有效的JSON格式")
            
        return response
        
    except requests.exceptions.Timeout:
        print("请求超时（超过120秒）")
        return None
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    for i in range(4):
        print(f"第{i+1}次请求")
        result = make_trpc_request()
        
        if result:
            print("\n=== 请求总结 ===")
            print(f"请求完成! 状态码: {result.status_code}")
            if result.status_code >= 400:
                print("注意: 服务器返回了错误状态码")
        else:
            print("\n=== 请求总结 ===")
            print("请求失败!") 
        time.sleep(10)
        print("--------------------------------")