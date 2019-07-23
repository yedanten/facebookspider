# -*- coding: utf-8 -*-
import base64
import requests
from requests.adapters import HTTPAdapter
import html
import json
from pyquery import PyQuery as pq
import time
import argparse
from urllib import parse
import re
import threading
from selenium import webdriver
from jinja2 import Environment, PackageLoader
import os

facebook_mobile_index_url = 'https://m.facebook.com'

# 建立facebook用户模型
class fb_user(object):
	def __init__(self, args, uri = ''):
		if uri:
			self.__url = uri
		else:
			self.__url = args.url
		self.__detailed = args.detailed
		self.__basic = args.basic
		self.__friends = args.friends
		self.__posts = args.posts
		self.__avatar = args.avatar
		self.__proxies = {
			'http': 'http://127.0.0.1:1080',
			'https': 'http://127.0.0.1:1080'
		}
		self.__headers = {
			'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
			'cookie': args.cookies
		}
		self.css = [],

		self.avatar_string = ''
		self.base_info = {}
		self.friends = []
		self.photos = [],
		self.posts = '',
		self.videos = [],
		self.saved_collections = []
		self.check_ins = []
		self.music = []
		self.tv_shows = []
		self.likes = []
		self.notes = []
		self.sports = []
		self.books = []
		self.events = []
		if 'id' in self.__url:
			self.userid = parse.parse_qs(parse.urlparse(self.__url).query)['id'][0]
		else:
			self.userid = parse.urlparse(self.__url).path.replace('/', '')

		if uri:
			self.__action(True)
		else:
			self.__action()

	# 执行获取信息操作
	def __action(self, follow = False):
		# 建立子线程
		thread_list = []
		if self.__detailed:
			thread_list.append(threading.Thread(target = self.get_base_info, name = "getbase"))
			thread_list.append(threading.Thread(target = self.get_friends, name = "getfriends"))
			thread_list.append(threading.Thread(target = self.get_posts, args = (follow, ), name = "getposts"))
			thread_list.append(threading.Thread(target = self.get_avatar, name = "getavatar"))
		else:
			if self.__basic:
				thread_list.append(threading.Thread(target = self.get_base_info, name = "getbase"))
			if self.__friends:
				thread_list.append(threading.Thread(target = self.get_friends, name = "getfriends"))
			if self.__posts:
				thread_list.append(threading.Thread(target = self.get_posts, name = "getposts"))
			if self.__avatar:
				thread_list.append(threading.Thread(target = self.get_avatar, name = "getavatar"))

		# 开启爬取任务
		for thread in thread_list:
			thread.start()

		# 等待所有子线程都完成爬取任务
		for thread in thread_list:
			thread.join()

	# 分割cookies字符串，提供给selenuim使用
	def __extract_cookies(self, cookie):
		cookies = cookie.split("; ")
		return cookies

	# 获取头像
	def get_avatar(self):
		print('getting avatar……')
		s = requests.Session()
		s.mount('http://', HTTPAdapter(max_retries=3))
		s.mount('https://', HTTPAdapter(max_retries=3))

		# 调用graphAPI获取
		pic_url = 'https://graph.facebook.com/' + self.userid + '/picture?type=large'
		r = s.get(pic_url, headers = self.__headers, proxies = self.__proxies)

		# 将头像图片base64编码后存放
		self.avatar_string = str(base64.b64encode(r.content), encoding = 'utf-8')
		print('got avatar')

	# 获取基础信息
	def get_base_info(self):
		print('getting basic info……')
		s = requests.Session()
		s.mount('http://', HTTPAdapter(max_retries=3))
		s.mount('https://', HTTPAdapter(max_retries=3))

		# 根据提供的是user_id还是username进行拼接不同的url
		if self.userid.isdigit():
			url = 'https://m.facebook.com/profile.php?id=' + self.userid + '&v=info'
		else:
			url = 'https://m.facebook.com/' + self.userid + '/?v=info'
		r = s.get(url, headers = self.__headers, proxies = self.__proxies)

		# 选中class为aboutme的节点
		html_doc = pq(r.text)
		aboutme_node = html_doc('.aboutme')
		
		# 基础信息解析
		for node in aboutme_node.find('div[id][data-sigil=profile-card]').items():
			value = []
			key = node.attr('id')
			list_tree = node.find('header:first').next()
			for list_node in list_tree.children().items():
				value.append(list_node.text().replace('\n', ' '))
			self.base_info.update({key:value})
		print('got basic info')

	# 获取朋友列表
	def get_friends(self):
		print('getting friends……')
		s = requests.Session()
		s.mount('http://', HTTPAdapter(max_retries=3))
		s.mount('https://', HTTPAdapter(max_retries=3))

		# 根据提供的是user_id还是username进行拼接不同的url
		if self.userid.isdigit():
			url = 'https://m.facebook.com/profile.php?id=' + self.userid + '&v=friends'
		else:
			url = 'https://m.facebook.com/' + self.userid + '/friends'

		friends_list = []

		# 因移动端滚动页面至底部才能获取更多好友信息，每一页的url参数都由服务端生成，下一页的url在本次的响应内容中
		# 因此需要不停的请求直到返回的更多好友信息为空
		pattern = re.compile(r'id:"m_more_friends",href:"(.*?)",')
		while True:
			r = s.get(url, headers = self.__headers, proxies = self.__proxies)
			url = pattern.findall(r.text)
			html_doc = pq(r.text)
			friends_node = html_doc('.darkTouch')
			if friends_node:
				for node in friends_node.items():
					friends_list.append({'name': html.unescape(node.find('i').attr('aria-label')), 'uri': node.attr('href')})
				if len(url):
					url = facebook_mobile_index_url + url[0]
				else:
					break
			else:
				break
		self.friends = friends_list
		print('got friends')

	# 获取动态信息
	# 这html太难解析了，图片类，文字类，活动类，投票类，原创发布和分享转发都不一样
	# 获取每页的article标签内容可以拿到该条动态的整段html，但是页面渲染使用的css每页都不一样，会被js进行动态调整
	# 为了渲染报告方便，使用selenuim进行访问，拿到最终的所有html源码，直接保存
	def get_posts(self, flag):
		print('getting posts……')
		options = webdriver.ChromeOptions()
		options.add_argument('--disable-gpu')
		options.add_argument('disable-infobars')
		options.add_argument('--hide-scrollbars')
		options.add_argument('--headless')
		options.add_argument('blink-settings=imagesEnabled=false')
		options.add_argument('user-agent=' + self.__headers['user-agent'])
		options.add_argument('--proxy-server=http://127.0.0.1:1080')
		driver = webdriver.Chrome(chrome_options=options)

		# 先访问一次facebook页面
		driver.get('https://m.facebook.com')
		
		# 通过寻找指定元素确定页面是否存在还是有bug，超时会抛异常
		# 这里使用sleep进行强制等待
		# 欢迎提issue或pull requests一起改进
		time.sleep(10)

		# 添加cookies
		for x in self.__extract_cookies(self.__headers['cookie']):
			driver.add_cookie({'name': x.split('=')[0], 'value': x.split('=')[1]})

		# 根据提供的是user_id还是username进行拼接不同的url
		if self.userid.isdigit():
			url = 'https://m.facebook.com/profile.php?id=' + self.userid
		else:
			url = 'https://m.facebook.com/' + self.userid

		# 访问目标主页
		driver.get(url)
		time.sleep(10)

		# 向下滑动页面至底部10次
		for x in range(1,10):
			driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			time.sleep(5)

		# 保存源码
		html = driver.page_source

		# 退出chrome handless
		driver.close()
		driver.quit()

		self.posts = html
		print('got posts')

	def get_photos(self):
		pass

	def get_videos(self):
		pass

	def get_saved_collections(self):
		pass

	def get_check_ins(self):
		pass

	def get_music(self):
		pass

	def get_tv_shows(self):
		pass

	def get_likes(self):
		pass

	def get_sports(self):
		pass

	def get_books(self):
		pass

	def get_events(self):
		pass

	def get_notes(self):
		pass

def main():
	# 解析命令行参数
	parser = argparse.ArgumentParser(description = '获取facebook用户公开的信息')
	parser.add_argument('--cookies', dest = 'cookies', required = True, help = '提供已登录账号的cookies供爬虫使用')
	parser.add_argument('-u', '--url', dest = 'url', required = True, help = '目标用户的主页地址 例:https://www.facebook.com/profile.php?id=1000 或 https://www.facebook.com/Jackma')
	parser.add_argument('-A', '--all', dest = 'detailed', action = 'store_true', help = '获取目标用户所有公开的信息, 包含个人信息，动态，朋友列表')
	parser.add_argument('-b', '--basic', dest = 'basic', action = 'store_true', help = '获取目标用户所有公开的个人信息')
	parser.add_argument('-f', '--friends', dest = 'friends', action = 'store_true', help = '获取目标用户所有公开的朋友列表')
	parser.add_argument('--posts', dest = 'posts', action = 'store_true', help = '获取目标用户公开的动态信息')
	parser.add_argument('--photos', dest = 'photos', action = 'store_true', help = '获取目标用户公开的相册图片')
	parser.add_argument('--avatar', dest = 'avatar', action = 'store_true', help = '获取目标用户的头像')
	parser.add_argument('--follow', dest = 'follow', action = 'store_true', help = '跟随爬取目标用户的朋友列表')
	args = parser.parse_args()

	# 检查目录是否存在
	if not os.path.exists('follow_res/posts'):
		os.makedirs('follow_res/posts')

	# 建立用户模型
	fb = fb_user(args)

	# 将爬取的信息以html形式进行渲染
	env = Environment(loader=PackageLoader('report_tmpl'))
	template = env.get_template('report.j2')
	content = template.render(user = fb, name = 'target')
	with open('report.html', 'w', encoding = 'utf-8') as f:
		f.write(content)

	with open('report_post.html', 'w', encoding = 'utf-8') as f:
		f.write(fb.posts)

	# 如果指定跟随爬取，则进一步获取
	if args.follow:
		for f in fb.friends:
			# 处理可能存在的用户uri为空的情况
			# 例如账号被封禁或主动注销
			if f['uri']:
				print('getting ' + f['name'] + ' info')

				user = fb_user(args, uri = f['uri'])
				content = template1.render(user = user, name = f['name'])
				with open('follow_res/posts/' + f['name'] + '.html', 'w', encoding = 'utf-8') as file:
					file.write(user.posts)

				with open('follow_res/' + f['name'] + '_report.html', 'w', encoding = 'utf-8') as file:
					file.write(content)

				print('got ' + f['name'] + ' info')

if __name__ == '__main__':
	main()