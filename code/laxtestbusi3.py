import selenium
import requests
import json
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import timedelta, datetime
import time
import csv
import re

# Discord Webhook URL
#WEBHOOK_URL = "https://discord.com/api/webhooks/1295434884361228450/zwTbBwZK3hryiEqFiCa6HWGXzZtWHRldTizl4BUNyZcw_0IHb94kbmikoKwOeFObbGBk"

# 發送 Discord 通知的函數
#def send_discord_notification(message):
 #   data = {"content": message}
  #  response = requests.post(WEBHOOK_URL, data=json.dumps(data), headers={"Content-Type": "application/json"})
   # if response.status_code == 204:
    #    logging.info("Discord 通知發送成功")
    #else:
     #   logging.error(f"Failed to send Discord notification: {response.status_code}, {response.text}")

# 設置 Selenium 驅動
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--headless")
service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

def retry(function, max_retries=3, delay=2):
    """重試機制的通用函數"""
    retries = 0
    while retries < max_retries:
        try:
            return function()  # 嘗試執行目標函數
        except NoSuchElementException:
            retries += 1
            print(f"重試第 {retries} 次，等待 {delay} 秒後重試...")
            time.sleep(delay)
    print("達到最大重試次數，操作失敗")
    return None

def scrape_flights(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    delta = timedelta(days=1)
    success_count = 0  # 總共抓取的航班數量

    # 迴圈遍歷每個日期
    current_date = start_date
    while current_date <= end_date:
        print(f"正在抓取日期: {current_date.strftime('%Y-%m-%d')}")

        url = "https://www.google.com/travel/flights/search?tfs=CBwQAholEgoyMDI1LTAxLTE5KAFqDAgCEggvbS8wZnRreHIHCAESA0xBWEABSANwAYIBCwj___________8BmAEC&tfu=EgYIBRABGAA&hl=zh-TW&gl=TW"
        driver.get(url)

        # 點擊日期選擇器
        try:
            departure_date_picker = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'TP4Lpb'))
            )
            departure_date_picker.click()
            print("成功點擊出發日期選擇器")
        except Exception as e:
            print("無法找到出發日期選擇器", e)

        time.sleep(1)

        # 選擇具體日期
        try:
            specific_date = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@class='WhDFk Io4vne' and @data-iso='{current_date.strftime('%Y-%m-%d')}']//div[@role='button']"))
            )
            specific_date.click()
            print(f"成功選擇出發日期 {current_date.strftime('%Y 年 %m 月 %d 日')}")
        except Exception as e:
            # 嘗試使用其他 XPath 來選擇日期
            try:
                specific_date = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[@class='WhDFk Io4vne Xu6rJc' and @data-iso='{current_date.strftime('%Y-%m-%d')}']//div[@role='button']"))
                )
                specific_date.click()  # 點擊特定的 12/31 日期
                print(f"成功選擇出發日期 {current_date.strftime('%Y 年 %m 月 %d 日')}")

            except Exception as e:
                try:
                    specific_date = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[@class='WhDFk Io4vne inxqCf' and @data-iso='{current_date.strftime('%Y-%m-%d')}']//div[@role='button']"))
                    )
                    specific_date.click()  # 點擊特定的 01/01 日期
                    print(f"成功選擇出發日期 {current_date.strftime('%Y 年 %m 月 %d 日')}")

                except Exception as e:
                    print(f"無法選擇出發日期 {current_date.strftime('%Y 年 %m 月 %d 日')}", e)
                    current_date += delta  # 如果無法選擇，繼續到下一個日期
                    continue  # 跳過當前迭代，進入下一個日期                

        # 點擊 "Done" 按鈕
        try:
            done_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="WXaAwc"]//div//button'))
            )
            done_button.click()
            print("成功點擊 'Done' 按鈕")
        except Exception as e:
            print("無法找到 'Done' 按鈕", e)
        
        time.sleep(2)

        # 獲取所有航班連結
        flight_links = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.pIav2d"))
        )
        print(f"找到 {len(flight_links)} 個航班")
                       
        today_date = datetime.now().strftime("%m%d")
        
        # 準備寫入 CSV 檔案
        with open(f'C:\\Users\\yuen\\Desktop\\專題\\laxbusi{today_date}.csv', 'a', newline='', encoding='utf-8-sig') as csv_file:
            csv_writer = csv.writer(csv_file)

            # 寫入標題
            csv_writer.writerow([
                "出發日期", "出發時間", "出發機場代號", 
                "抵達時間", "抵達機場代號", "航空公司", 
                "停靠站數量", "停留時間", "飛行時間", 
                "是否過夜", "機型", "航班代碼", "艙等", "價格"
            ])

            # 遍歷並點擊每個航班
            for index, flight_element in enumerate(flight_links):
                try:     
                    # 找到每個航班的元素
                    flight_element = flight_links[index]
                    
                    # 點擊航班更多資訊
                    flight_buttons = flight_element.find_elements(By.XPATH, ".//div[@class='vJccne  trZjtf']//div[@class='VfPpkd-dgl2Hf-ppHlrf-sM5MNb']//button")
                    flight_buttons[0].click()  # 點擊第一個按鈕
                    
                    # 等待頁面加載
                    time.sleep(1)

                    # 抓取資料
                    try:                    
                        # 抓取出發時間
                        departure_time_element = flight_element.find_element(By.XPATH, './/div[@class="wtdjmc YMlIz ogfYpf tPgKwe"]').get_attribute("aria-label")
                        departure_time = departure_time_element.split("：")[-1].strip()
                        departure_time = departure_time.replace("。", "").strip()

                        # 抓取抵達時間
                        arrival_time_element = flight_element.find_element(By.XPATH, ".//div[@class='XWcVob YMlIz ogfYpf tPgKwe']").get_attribute("aria-label")
                        arrival_time = arrival_time_element.split("：")[-1].strip()
                        arrival_time = arrival_time.replace("。", "").strip()

                        # 抓取出發機場代號
                        departure_airport = flight_element.find_element(By.XPATH, ".//div[@class='G2WY5c sSHqwe ogfYpf tPgKwe']//div").get_attribute("innerHTML")

                        # 抓取抵達機場代號
                        arrival_airport = flight_element.find_element(By.XPATH, ".//div[@class='c8rWCd sSHqwe ogfYpf tPgKwe']//div").get_attribute("innerHTML")

                        # 抓取航空公司
                        airlines = flight_element.find_elements(By.XPATH, ".//span[@class='Xsgmwe'][1]")
                        # 將航空公司名稱存入列表
                        airlines = [element.get_attribute("innerHTML").strip() for element in airlines]
                        # 將所有航空公司名稱合併成一個變數，並以空格分隔
                        airline = ' '.join(airlines)
                        
                        # 抓取航班號
                        flight_number_element = flight_element.find_elements(By.XPATH, ".//span[@class='Xsgmwe sI2Nye']")
                        # 將航班號存入列表
                        flight_numbers = [element.get_attribute("innerHTML").replace('&nbsp;', ' ').strip() for element in flight_number_element]
                        # 將所有航班號合併成一個變數，並以空格分隔
                        flight_number = ' '.join(flight_numbers)
                        
                        try:
                            # 抓取停靠站數量
                            layover_element = flight_element.find_element(By.XPATH, "//div[@class='EfT7Ae AdWm1c tPgKwe']//span[@class='ogfYpf']").get_attribute("aria-label")
                            layover = layover_element.split(" flight.")[0]  # 提取 "1 stop" 或 "Non-stop"
                        except NoSuchElementException:
                            layover = "Non-stop"

                        if layover != "直達航班。":
                            try:
                                # 嘗試抓取停留時間的內部 HTML
                                layover_info_element = flight_element.find_element(By.XPATH, './/div[@class = "tvtJdb eoY5cb y52p7d"]').get_attribute("innerHTML")
                                time_pattern = r'(\d+\s*(小時|hr|hours)\s*\d+\s*(分鐘|min|minutes)|\d+\s*(小時|hr|hours)|\d+\s*(分鐘|min|minutes))'
                                match = re.search(time_pattern, layover_info_element)
                                layover_time = match.group(1) if match else "未找到停留時間"
                                if not match:
                                    print("未找到停留時間的 HTML:", layover_info_element)
                            except NoSuchElementException:
                                    layover_time = "未找到停留時間"
                        else:
                            layover_time = "Non-stop"

                        try:
                            # 檢查是否有 "Overnight" 元素
                            overnight_element = flight_element.find_element(By.XPATH, './/div[@class="qj0iCb" and contains(text(), "Overnight")]').get_attribute("innerHTML")
                            overnight = "Yes"
                        except NoSuchElementException:
                            overnight = "No"
                            
                        # 抓取機型
                        aircrafts = flight_element.find_elements(By.XPATH, './/span[@class="Xsgmwe"][3]') 
                        aircrafts = [element.get_attribute("innerHTML").strip() for element in aircrafts]
                        aircraft = ' '.join(aircrafts)
                                                
                        # 抓取艙等
                        cabin_class = flight_element.find_element(By.XPATH, './/span[@class="Xsgmwe"][2]').get_attribute("innerHTML")
                        
                        try:
                            # 嘗試第一個 XPath
                            travel_time_element = flight_element.find_element(By.XPATH, ".//div[@class='hF6lYb sSHqwe ogfYpf tPgKwe']//span[5]").get_attribute("innerHTML")
                            match = re.search(r'(\d+ 小時(?: \d+ 分鐘)?)', travel_time_element)
                            flight_duration = match.group(1) if match else None

                            # 如果第一個 XPath 找不到有效內容，再嘗試第二個 XPath
                            if not flight_duration:
                                travel_time_element = flight_element.find_element(By.XPATH, ".//div[@class='hF6lYb sSHqwe ogfYpf tPgKwe']//span[6]").get_attribute("innerHTML")
                                match = re.search(r'(\d+ 小時(?: \d+ 分鐘)?)', travel_time_element)
                                flight_duration = match.group(1) if match else "未找到飛行時間"

                        except NoSuchElementException:
                            flight_duration = "未找到飛行時間"

                        # 抓取價格
                        price = flight_element.find_element(By.XPATH, './/div[contains(@class, "FpEdX")]//span').get_attribute("innerHTML")
                        
                        # 使用 strftime() 補上星期幾
                        weekday = current_date.strftime("%A")  # 取得完整的星期名稱，例如 "Friday"
                        formatted_date = current_date.strftime("%Y-%m-%d") + " " + weekday

                        # 寫入資料
                        csv_writer.writerow([
                            formatted_date, departure_time, departure_airport,
                            arrival_time, arrival_airport, airline,
                            layover, layover_time, flight_duration,
                            overnight, aircraft, flight_number, cabin_class,
                            price
                        ])

                        success_count += 1

                    except NoSuchElementException as e:
                        print(f"抓取航班資料失敗: {e}")

                except Exception as e:
                    print(f"無法點擊第 {index + 1} 個航班: {e}")
                    continue

        # 更新當前日期
        current_date += delta

    driver.quit()
    return success_count

# 調用函式
start_date_input = "2025-02-13"
end_date_input = "2025-02-23"
success_count = scrape_flights(start_date_input, end_date_input)

# 顯示抓取的總航班數量
print(f"共抓取 {success_count} 個航班")
