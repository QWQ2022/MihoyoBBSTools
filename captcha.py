import time
from request import http
from loghelper import log

appkey = "前往 ttocr.com 获取 api 填入"

def captcha(gt: str, challenge: str):
    try:
        rep = http.post(
            url= "http://api.ttocr.com/api/recognize",
            data={
                "appkey": appkey,
                "gt": gt,
                "challenge" : challenge,
                "referer" : "https://api-takumi.mihoyo.com/event/luna/sign",
                "itemid" :   388
            }
        ).json()
    
        max_wait_time = 120  # 最大等待时间
        interval = 10  # 轮询间隔时间
    
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                rep2 = http.post(
                    url="http://api.ttocr.com/api/results",
                    data={
                        "appkey": appkey,
                        "resultid": str(rep["resultid"]),
                    },
                    timeout=(60, 60)  # 设置连接超时和读取超时均为60秒
                ).json()
    
                if rep2.get("status") == 2:
                    log.info("等待识别结果...")
                    time.sleep(interval)  # 等待一段时间后再次发送请求
                else:
                    log.info("识别成功！")
                    log.debug(f"API Response1: {rep}")
                    log.debug(f"API Response2: {rep2}")
                    # 返回包含 validate 和 challenge 的字典
                    return {
                        "validate": rep2["data"]["validate"],
                        "challenge": challenge  # 使用传入的 challenge
                    }
    
            except Exception as e:
                log.error(f"请求发生错误: {e}")
                return None
    
        log.warning("超过最大等待时间，未获取到结果")
        return None
    except Exception as e:
        log.error(f"异常错误: {e}")
        return None


def game_captcha(gt: str, challenge: str) -> dict:
    return captcha(gt, challenge)


def bbs_captcha(gt: str, challenge: str) -> dict:
    return captcha(gt, challenge)


def get_points():
    try:
        response = http.get(f"http://api.ttocr.com/api/points?appkey={appkey}")
        result = response.json()
        
        if result.get('status') == 1:
            points = result.get('points', '0')
            return 0,int(points)
        else:
            msg = result.get('msg', '未知错误')
            log.error(f"查询失败: {msg}")
            return 1,msg
            
    except Exception as e:
        log.error(f"请求异常: {str(e)}")
        return 2,e


if __name__ == "__main__":
    points = get_points()[0]
    if isinstance(points, int):
        log.info(f"当前剩余点数：{points}")
