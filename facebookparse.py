# -*- coding: utf-8 -*-
import base64
import requests
from requests.adapters import HTTPAdapter
import html
import json
from pyquery import PyQuery as pq
import sys
import random
from fake_useragent import UserAgent
import time
import argparse
from urllib import parse
import re
import threading
from selenium import webdriver
from selenium.webdriver.common.touch_actions import TouchActions

facebook_mobile_index_url = 'https://m.facebook.com'
ua = UserAgent()

class fb_user(object):
	def __init__(self, args):
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

		self.__action()

	def __action(self):
		thread_list = []
		if self.__detailed:
			thread_list.append(threading.Thread(target = self.get_base_info, name = "getbase"))
			thread_list.append(threading.Thread(target = self.get_friends, name = "getfriends"))
			thread_list.append(threading.Thread(target = self.get_posts, name = "getposts"))
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

		for thread in thread_list:
			thread.start()
		for thread in thread_list:
			thread.join()

	def __extract_cookies(self, cookie):
		cookies = cookie.split("; ")
		return cookies

	# 获取头像
	def get_avatar(self):
		print('getting avatar……')
		s = requests.Session()
		s.mount('http://', HTTPAdapter(max_retries=3))
		s.mount('https://', HTTPAdapter(max_retries=3))
		pic_url = 'https://graph.facebook.com/' + self.userid + '/picture?type=large'
		try:
			r = s.get(pic_url, headers = self.__headers, proxies = self.__proxies)
		except Exception as e:
			raise e
		self.avatar_string = str(base64.b64encode(r.content), encoding = 'utf-8')
		print('got avatar')

	def get_base_info(self):
		print('getting basic info……')
		s = requests.Session()
		s.mount('http://', HTTPAdapter(max_retries=3))
		s.mount('https://', HTTPAdapter(max_retries=3))
		if self.userid.isdigit():
			url = 'https://m.facebook.com/profile.php?id=' + self.userid + '&v=info'
		else:
			url = 'https://m.facebook.com/' + self.userid + '/?v=info'
		r = s.get(url, headers = self.__headers, proxies = self.__proxies)

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

	def get_friends(self):
		print('getting friends……')
		s = requests.Session()
		s.mount('http://', HTTPAdapter(max_retries=3))
		s.mount('https://', HTTPAdapter(max_retries=3))
		if self.userid.isdigit():
			url = 'https://m.facebook.com/profile.php?id=' + self.userid + '&v=friends'
		else:
			url = 'https://m.facebook.com/' + self.userid + '/friends'
		friends_list = []
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

	def get_posts(self):
		options = webdriver.ChromeOptions()
		options.add_argument('--disable-gpu')
		options.add_argument('disable-infobars')
		options.add_argument('--hide-scrollbars')
		options.add_argument('blink-settings=imagesEnabled=false')
		options.add_argument('user-agent=' + self.__headers['user-agent'])
		options.add_argument('--proxy-server=http://127.0.0.1:1080')
		driver = webdriver.Chrome(chrome_options=options)
		driver.get('https://m.facebook.com')
		
		time.sleep(2)
		for x in self.__extract_cookies(self.__headers['cookie']):
			driver.add_cookie({'name': x.split('=')[0], 'value': x.split('=')[1]})

		if self.userid.isdigit():
			url = 'https://m.facebook.com/profile.php?id=' + self.userid
		else:
			url = 'https://m.facebook.com/' + self.userid
		driver.get(url)
		time.sleep(10)
		for x in range(1,3):
			driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			time.sleep(5)
		html = driver.page_source
		driver.close()
		driver.quit()
		with open('test.html', 'w', encoding = 'utf-8') as f:
			f.write(html)

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

	def toJson(self):
		return {
			'css': self.css,
			'basic_info': self.base_info,
			'friends': self.friends,
			'avatar_string': self.avatar_string,
			'photos': self.photos,
			'videos': self.videos,
			'saved_collections': self.saved_collections,
			'check_ins': self.check_ins,
			'music': self.music,
			'tv_shows': self.tv_shows,
			'likes': self.likes,
			'notes': self.notes,
			'sports': self.sports,
			'books': self.books,
			'events': self.events,
		}

def main():
	parser = argparse.ArgumentParser(description = 'Get facebook user public details.')
	parser.add_argument('--cookies', dest = 'cookies', required = True, help = 'login cookies')
	parser.add_argument('-u', dest = 'url', required = True, help = 'Taget user home page url. Such as https://www.facebook.com/profile.php?id=1000 or https://www.facebook.com/Jackma')
	parser.add_argument('-A', '--all', dest = 'detailed', action = 'store_true', help = 'Get all of target user info. Such as avatar, public basic info, post of the most recent year, frends list')
	parser.add_argument('-b', dest = 'basic', action = 'store_true', help = 'Get target user public basic info')
	parser.add_argument('-f', dest = 'friends', action = 'store_true', help = 'Get target user friends list')
	parser.add_argument('--posts', dest = 'posts', action = 'store_true', help = 'Get target user post of the most recent year')
	parser.add_argument('--photos', dest = 'photos', action = 'store_true', help = 'Get target user photos')
	parser.add_argument('--avatar', dest = 'avatar', action = 'store_true', help = 'Get target user avatar base64 string')
	
	args = parser.parse_args()

	fb = fb_user(args)
	with open('test.txt', 'w', encoding = 'utf-8') as f:
		f.write(json.dumps(fb, default = lambda obj: obj.__dict__))

if __name__ == '__main__':
	main()
