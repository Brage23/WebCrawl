
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from time import sleep
from PIL import Image
import os,io,sys
import random
from bs4 import BeautifulSoup 
import difflib

class tianyancha:
    #对象初始化
    def __init__(self,driver_path,debug=False):
        url = 'https://www.tianyancha.com'
        self.url = url
        #firefox_options = Options()
        options = webdriver.ChromeOptions()
        if debug is False:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        #self.browser = webdriver.Firefox(executable_path=driver_path,firefox_options=options)
        self.browser = webdriver.Chrome(executable_path=driver_path, options=options)
        self.browser.maximize_window()
    
    #登录
    def login(self,username,password):
        self.browser.get(self.url)

        #1. 左上角登录/注册
        try:
            WebDriverWait(self.browser,10).until(lambda driver: driver.find_element_by_xpath('//a[@class="link-white"]'))
            self.browser.find_element_by_xpath('//a[@class="link-white"]').click()#登录/注册
        except Exception as e:
            print('1 - login failed',e)
            return False
        
        #2. 密码登录
        try:
            WebDriverWait(self.browser,10).until(lambda driver: driver.find_element_by_xpath('//div[@active-tab="1"]'))
            self.browser.find_element_by_xpath('//div[@active-tab="1"]').click()
        except Exception as e:
            print('2 - login failed',e)
            return False

        #3. 输入用户名与密码
        try:
            WebDriverWait(self.browser,10).until(lambda driver: driver.find_element_by_name("phone"))
            self.browser.find_element_by_name("phone").send_keys(username)
            self.browser.find_element_by_name("password").send_keys(password)
            self.browser.find_element_by_xpath("//div[@class='btn -xl btn-primary -block']").click()
        except Exception as e:
            print('3 - login failed',e)
            return False

        #4. 等待滑块验证码
        try:        
            WebDriverWait(self.browser,10).until(lambda driver: driver.find_element_by_xpath('//div[@class="gt_box"]'))
        except Exception as e:
            print('4 - wait captcha failed',e)
            return False

        k = 1.25 #浏览器缩放比例，请根据实际情况调整

        #5. 截取完整的滑块验证码图片
        try:
            img = self.browser.find_element_by_xpath('//div[@class="gt_box"]')
            locat = img.location
            size = img.size
            self.browser.save_screenshot('tyx_captcha_1.png')
            im = Image.open('./tyx_captcha_1.png')
            
            im1 = im.crop((locat['x'] * k,locat['y'] * k,(locat['x'] + size['width']) * k,(locat['y'] + size['height']) * k))
            #im1.save('./result.png') 
            os.remove('tyx_captcha_1.png')
        except Exception as e:
            print('5 - get captcha pic failed',e)
            return False

        #6. 获取破损的滑块验证码图片
        try:
            slider = self.browser.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]')
            ActionChains(self.browser).click_and_hold(slider).perform()

            self.browser.save_screenshot('tyx_captcha_2.png')
            im = Image.open('./tyx_captcha_2.png')
            im2 = im.crop((locat['x'] * k,locat['y'] * k,(locat['x'] + size['width']) * k,(locat['y'] + size['height']) * k))
            #im2.save('./result2.png')  #debug used
            os.remove('tyx_captcha_2.png')
        except Exception as e:
            print('6 - get captcha pic failed',e)
            return False    

        dis = self.get_slider_distance(im1,im2)#计算需要滑动的距离
        
        self.captcha_move_trace(dis / k)#滑动
        sleep(0.5)
        ActionChains(self.browser).release().perform()

        sleep(3)

        #检查是否成功
        try:
            WebDriverWait(self.browser,3).until(lambda driver: driver.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]'))
            print('login failed')
            return False
        except:
            print('login successd')
            return True

    #计算滑块距离
    def get_slider_distance(self,broken_img,whole_img):
        def is_pixel_equal(broken_img,full_img,x,y):
            broken_pixel = broken_img.load()[x,y]
            whole_pixel = whole_img.load()[x,y]
            threshold = 60
            if abs(broken_pixel[0]-whole_pixel[0])<threshold and abs(broken_pixel[1]-whole_pixel[1])<threshold \
                and abs(broken_pixel[2]-whole_pixel[2])<threshold:
                return True
            else:
                return False
        base_distance = 75
        for i in range(base_distance,whole_img.size[0]):
            for j in range(whole_img.size[1]):
                if not is_pixel_equal(broken_img,whole_img,i,j):
                    return i
        return -1

    #获取移动滑块的路径
    def captcha_move_trace(self,dis):
        def get_slider_trace(distance):
            trace = []
            forward = distance
            faster_dis = forward * (3/5)
            start,v0 = 0,0

            t = random.randint(2, 3) / 10
            while start < forward:
                if start<faster_dis:
                    a=random.uniform(2,2.5)
                else:
                    a=-3
                move = v0 * t + 1 / 2 * a * t * t
                v = v0 + a * t
                v0 = v
                start += move
                trace.append(round(move))
            return trace

        trace = get_slider_trace(dis * 1 / 5)
        for x in trace:
            ActionChains(self.browser).move_by_offset(xoffset=x,yoffset=0).perform()
        sleep(0.2)   
        trace = get_slider_trace(dis * 1 / 5)
        for x in trace:
            ActionChains(self.browser).move_by_offset(xoffset=x,yoffset=0).perform()
        sleep(0.2)
        trace = get_slider_trace(dis * 3 / 5)
        for x in trace:
            ActionChains(self.browser).move_by_offset(xoffset=x,yoffset=0).perform()
        sleep(0.3)

        back_trace = [-2,-4,-4,-5,-4,-4,-2]
        for x in back_trace:
            ActionChains(self.browser).move_by_offset(xoffset=x,yoffset=0).perform()
        sleep(0.3)

        trace = [1,2,3,4,3,2]
        for x in trace:
            ActionChains(self.browser).move_by_offset(xoffset=x,yoffset=0).perform()

    #搜索公司
    def search_company(self,name):
        try:
            #检查是否在首页
            WebDriverWait(self.browser,1).until(lambda driver: driver.find_element_by_xpath('//input[@id="home-main-search"]'))
            self.browser.find_element_by_xpath('//input[@id="home-main-search"]').clear()
            self.browser.find_element_by_xpath('//input[@id="home-main-search"]').send_keys(name)
            self.browser.find_element_by_xpath('//div[@class="input-group-btn btn -xl"]').click()
        except:
            #不在首页
            try:
                self.browser.find_element_by_xpath('//input[@id="header-company-search"]').clear()
                self.browser.find_element_by_xpath('//input[@id="header-company-search"]').send_keys(name)
                self.browser.find_element_by_xpath('//div[@class="input-group-btn btn -sm btn-primary"]').click()   
            except Exception as e:
                print('search company failed!',e)
                return False 
        
        finally:
            return True  

    def get_company_info(self,name):
        if self.search_company(name) is False:
            return None

        src = self.browser.page_source
        bs = BeautifulSoup(src,"html.parser")
        info = {}
        # header-block:企业信息在网页头部
        if bs.find(name='div',attrs={"class":"container company-header-block "}) is not None:
            info['name'] = name
            head_block = bs.find(name='div',attrs={"class":"container company-header-block "})

            header_1 = head_block.find_all(name='div',attrs={"class":"in-block sup-ie-company-header-child-1"})
            for header in header_1:
                label = header.find(name='span',attrs={"class":"label"})
                if label is None:
                    continue
                if label.text == "电话：":
                    spans = header.find_all("span")
                    for span in spans:
                        if 'class' not in span.attrs:
                            info['phone'] = span.text
                            break
                elif label.text == "网址：":
                    info['web'] = header.find(name='a',attrs={"class":"company-link"}).attrs['href']
            header_2 = head_block.find_all(name='div',attrs={"class":"in-block sup-ie-company-header-child-2"})
            for header in header_2:
                label = header.find(name='span',attrs={"class":"label"})
                if label is None:
                    continue
                elif label.text == "邮箱：":
                    spans = header.find_all("span")
                    for span in spans:
                        if 'email' in span.attrs['class']:
                            info['email'] = span.text
                            break
                elif label.text == "地址：":
                    s = header.find(name='script')
                    addr = s.text
                    addr = addr.replace(" ","")
                    info['addr'] = addr
                
            name = bs.find(name='div',attrs={"class":"name"})
            info['owner'] = name.text
            return info
        # list:企业信息以列表形式展示

        if bs.find_all("div",class_="search-item sv-search-company") is not None:
            max_item = None
            max_diff = 0
            items = bs.find_all("div",class_="search-item sv-search-company")
            for item in items:
                diff = difflib.SequenceMatcher(None,name,item.find("div",class_="header").find("a").text).quick_ratio()
                if diff == 1:
                    max_item = item
                    break
                elif diff > max_diff:
                    max_diff = diff
                    max_item = item
            if max_item is not None:
                #company name
                info['name'] = max_item.find("div",class_="header").find("a").text
                #owner
                info['owner'] = max_item.find("div",class_="title -wider text-ellipsis").find("a").text
                #phone
                for col in max_item.find_all("div",class_="col"):
                    label = col.find(name='span',attrs={"class":"label"})
                    if label is None:
                        continue
                    elif label.text == "电话：":
                        for span in col.find_all(name="span"):
                            if 'onclick' in span.attrs:
                                for sub_span in span.find_all(name="span"):
                                    if 'class' not in sub_span.attrs:
                                        info['phone'] = sub_span.text
                    elif label.text == "邮箱：":
                        for span in col.find_all(name="span"):
                            if 'class' not in span.attrs:
                                info['email'] = span.text
                return info
        return None
    def __del__(self):
        self.browser.close()
        self.browser.quit()
        

if __name__ == "__main__": 
    driver_path = "your driver path"
    username = 'your tianyancha username'
    password = 'your tianyancha password'
    tyc = tianyancha(driver_path,debug = True)
    sleep(5)
    while tyc.login(username,password) is False:
        sleep(1)
    sleep(5)
    info = tyc.get_company_info("南昌梅西商贸有限公司")
    print(info)
    sleep(5)
    info = tyc.get_company_info("南通回力橡胶有限公司")
    print(info)
    sleep(5)
    info = tyc.get_company_info("福州安鸿贸易有限公司")
    print(info)

    
    
    


            

