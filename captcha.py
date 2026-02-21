import time
from request import http
from loghelper import log
import os
import configparser
from pathlib import Path

def get_ttocr_key():
    env_enable = os.getenv("ttocr_enable")
    env_key = os.getenv("ttocr_key")
    if env_enable and env_enable.lower() == "true" and env_key:
        return env_key
    elif env_enable and env_enable.lower() == "true":
        log.error("环境变量未配置key")
        return None
    elif env_enable and env_enable.lower() == "false":
        return None
    config_path = Path(__file__).parent / 'config' / 'captcha.ini'
    if not config_path.exists():
        return None
    
    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding='utf-8')
    if cfg.has_section('ttocr') and cfg.get('ttocr', 'enable', fallback='false').lower() == 'true':
        key = cfg.get('ttocr', 'captcha_key', fallback='')
        if key and not key == '':
            return key
        else:
            log.warning("未配置key")
    return None
    
    
def captcha(gt: str, challenge: str):
    appkey = get_ttocr_key()
    if not appkey:
        return None

    
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
                elif rep2.get("status") == 1:
                    log.info("识别成功！")
                    log.debug(f"API Response1: {rep}")
                    log.debug(f"API Response2: {rep2}")
                    # 返回包含 validate 和 challenge 的字典
                    return {
                        "validate": rep2["data"]["validate"],
                        "challenge": challenge  # 使用传入的 challenge
                    }
                elif rep2.get("status") == 4039:
                    log.warnning(f"请求失败{rep2.get(msg)},正在尝试重新查询")
                else:
                    log.error(rep2)
                    return None
    
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
    appkey = get_ttocr_key()
    if not appkey:
        return 3, ""
    try:
        response = http.get(f"http://api.ttocr.com/api/points?appkey={appkey}")
        result = response.json()
        
        if result.get('status') == 1:
            points = result.get('points', '0')
            return 0, int(points)
        else:
            msg = result.get('msg', '未知错误')
            log.error(f"查询失败: {msg}")
            return 1, msg
            
    except Exception as e:
        log.error(f"请求异常: {str(e)}")
        return 2, e


if __name__ == "__main__":
    status,points = get_points()
    if status == 0:
        log.info(f"当前剩余点数：{points}")
