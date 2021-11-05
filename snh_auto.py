import os
import time
import pickle

import requests
from selenium import webdriver
import yaml
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SnhTickets:
    def __init__(self, username, password, nick_name, ticket_type, ticket_num, target_url, index_url, driver_path):
        self.status = 0
        self.time_start = 0
        self.time_end = 0
        self.ticket_type = ticket_type
        self.try_num = 0
        self.ticket_num = ticket_num
        self.target_url = target_url
        self.driver_path = driver_path
        self.username = username
        self.password = password
        self.nick_name = nick_name
        self.driver = None
        self.index_url = index_url
        self.pay_url = None
        self.pay_pic = None

    def set_cookie(self):
        try:
            cookies = pickle.load(open("cookies.pkl", "rb"))
            for cookie in cookies:
                cookie_dict = {
                    'domain':'.shop.48.cn',
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False}
                self.driver.add_cookie(cookie_dict)
            print(u'###载入Cookie###')
        except Exception as e:
            print(e)

    def login(self):
        print("=== 开始登录 ===")
        self.driver.get(self.target_url)
        WebDriverWait(self.driver, 10, 0.1).until(EC.title_contains('公演'))
        self.set_cookie()

    # 进入抢票网站
    def enter_48shop(self):
        print("===打开浏览器，进入snh商城===")
        if not os.path.exists('cookies.pkl'):
            self.driver = webdriver.Chrome(executable_path=self.driver_path)
            self.get_cookie()
            print("===成功获取Cookie，重启浏览器===")
            self.driver.quit()

        options = webdriver.ChromeOptions()
        # 禁止图片、js、css加载

        prefs = {
                 "profile.managed_default_content_settings.images": 2,
                 "profile.managed_default_content_settings.javascript": 1,
                 "permissions.default.stylesheet": 2}
        options.add_experimental_option("prefs", prefs)

        # 更换等待策略为不等待浏览器加载完全就进行下一步操作
        capa = DesiredCapabilities.CHROME
        capa["pageLoadStrategy"] = "none"
        self.driver = webdriver.Chrome(executable_path=self.driver_path, options=options, desired_capabilities=capa)

        self.login()
        self.driver.refresh()
        try:

            locator = (By.CSS_SELECTOR, "div.login.fl>a")
            WebDriverWait(self.driver, 5, 0.3).until(EC.text_to_be_present_in_element(locator, "你好" + self.nick_name))
            self.status = 1
            print("===登录成功===")
            self.time_start = time.time()
        except:
            self.status = 0
            self.driver.quit()
            raise Exception(u"***错误：登录失败,请删除cookie后重试***")

    # 实现购买函数
    def choose_ticket(self):
        print("===进入抢票界面===")

        while self.driver.title.find("门票详情") == -1:  # 如果跳转到了确认界面就算这步成功了，否则继续执行此步
            self.try_num += 1  # 尝试次数加1
            print("="*30, "第", self.try_num, "尝试")
            # 确认页面刷新成功
            try:
                box = WebDriverWait(self.driver, 5, 0.1).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'i_sel')))
            except:
                print(u"***Error: 页面刷新出错***")
                break

            try:
                buybutton = box.find_element_by_id('buy')  # 寻找立即购买标签
                buybutton_text = buybutton.text
                print("buybutton text: " + buybutton_text)
            except:
                raise Exception(u"***Error: buybutton 位置找不到***")

            if buybutton_text == "即将开抢" or buybutton_text == "即将开售":
                self.status = 2
                raise Exception("===尚未开售，刷新等待===")

            try:
                # 门票种类 is_2:写生款式 is_4：门票种类
                selects = box.find_elements_by_css_selector('span.is_4>em')
                print("=== 门票类型： ", [type.text for type in selects] , "===")
                for item in self.ticket_type:
                    want_ticket_type = selects[item-1]
                    # 判断是否还有票
                    if ("seattypebg" in want_ticket_type.get_attribute("class")):
                        want_ticket_type.click()
                        print("选择了： ", want_ticket_type.text)
                        self.status = 3
                        break

                buy_num = box.find_element_by_id('num')

                buy_num.clear()
                time.sleep(1)
                buy_num = box.find_element_by_id('num')
                buy_num.send_keys(self.ticket_num)
                print("选择了", self.ticket_num, "张票")
                self.status = 4

            except:
                raise Exception(u"***Error: 选择门票类型不成功***")

            if buybutton_text == "立即购买":
                buybutton.click()
            time.sleep(0.5)
            if self.driver.title == "门票详情":
                break

    def pay_for_it(self):
        if self.status in [3, 4]:
            if self.driver.title == "门票详情":
                time.sleep(1)
                ticket_info = self.driver.find_element_by_class_name('sp_list_xx.a1.ccc')
                ticket_title = ticket_info.find_element_by_css_selector('span.sp_list_2a.kb>a').text
                ticket_num = ticket_info.find_element_by_css_selector('span.sp_list_4.kb.lh100').text
                ticket_price = ticket_info.find_element_by_css_selector('span.sp_list_4.lh100.kb.pink').text
                ticket_score = ticket_info.find_element_by_css_selector('span.sp_list_5a.lh100.kb.pink').text
                print("门票信息： 名称：", ticket_title, " 数量：", ticket_num, " 价格：", ticket_price, " 积分：",
                      ticket_score )
                print("抢票结束： 用时", time.time()-self.time_start, "秒")
                try:
                    pay_link = WebDriverWait(self.driver, 1, 0.2).until(
                        EC.presence_of_element_located((By.LINK_TEXT, '前往付款')))
                    pay_link.click()
                except:
                    raise Exception(u"***Error: buybutton 位置找不到***")

                while self.driver.title != "SNH48官方周边商品商城":
                    time.sleep(0.5)
                # 勾选支付宝
                self.driver.find_element_by_id('chxBankCode').click()
                pay_btn = self.driver.find_element_by_id('btn_Bank')
                time.sleep(1)
                pay_btn.click()

                while self.driver.title != "扫码支付":
                    time.sleep(0.5)
                    if self.driver.title == "扫码支付":
                        break

                print("已显示付款码")
                self.pay_url = self.driver.current_url
                self.pay_pic = self.driver.find_element_by_id("imgcode").get_attribute("src")
                print("pay_url: ", self.pay_url, " pay_pic: ", self.pay_pic)


    # 获取账号的cookie信息
    def get_cookie(self):
        self.driver.get(self.index_url)
        loginInfoEle = self.driver.find_element(By.CSS_SELECTOR, "div.login.fl>a")
        loginInfo = loginInfoEle.text
        if loginInfoEle:
            if loginInfo == "请登录":
                print("检测到未登录，跳转到登录界面")
                loginInfoEle.click()
                passwordLoginWay = self.driver.find_element(By.LINK_TEXT, "密码登录/注册")
                if passwordLoginWay:
                    passwordLoginWay.click()
                    time.sleep(1)
                    verify = self.driver.find_element(By.LINK_TEXT, "验证码登录")
                    time.sleep(1.2)
                    if verify:
                        self.driver.find_element_by_id("username").send_keys("18701997306")
                        time.sleep(0.5)
                        self.driver.find_element_by_id("password").send_keys("112233")
                        time.sleep(1)
                        self.driver.find_element_by_css_selector("a#loginbtn2").click()
                        print("正在登录……")
                        while self.driver.title == 'SNH48会员中心':
                            time.sleep(1)
                    pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
                    print("=== Cookie 保存成功 ===")
            elif loginInfo.startswith("你好"):
                UserName = loginInfo[2:]
                print(" 已是登录状态， UserName： ", UserName)
                pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
                print("=== Cookie 保存成功 ===")
        else:
            print("网络可能有误， 不修复我真的很难帮你办事=.=")

    def download_img(img_url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
        }
        r = requests.get(img_url, headers=headers, stream=True)
        # print(r.status_code) # 返回状态码
        if r.status_code == 200:
            # 截取图片文件名
            img_name = img_url.split('/').pop()
            print("img_name: ", img_name)
            with open(img_name, 'wb') as f:
                f.write(r.content)
            return True

def initData():
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
            con = SnhTickets(config['username'], config['password'], config['nick_name'],
                             config['ticket_type'], config['ticket_num'],
                             config['target_url'], config['index_url'], config['driver_path'])
            return con
    except Exception as e:
        print(e)
        exit(1)

if __name__ == '__main__':
    con = initData()
    con.enter_48shop()
    con.choose_ticket()
    con.pay_for_it()
