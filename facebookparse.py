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
			'cookie': 'm_pixel_ratio=3; datr=MY0mXQyulSKzuIbnNj3bZNsE; sb=MY0mXWRhEHaZikj4g-AVYSwB; locale=zh_CN; c_user=100016433047567; xs=22%3AhwSnD_ZqnE3aew%3A2%3A1562807771%3A17776%3A12756; spin=r.1000932104_b.trunk_t.1562898924_s.1_v.2_; act=1562898948523%2F3; dpr=3; presence=EDvF3EtimeF1562899606EuserFA21B16433047567A2EstateFDutF1562899606958CEchFDp_5f1B16433047567F1CC; wd=375x812; x-referer=eyJyIjoiL2hvbWUucGhwIiwiaCI6Ii9ob21lLnBocCIsInMiOiJtIn0%3D; fr=1XTXXdyuocrq3V00H.AWUU7zmJL5W9j-5dC1Wb483McCk.BdIcW4.ZO.AAA.0.0.BdKB12.AWVlHHhO'
		}

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
		print("getting posts……")
		s = requests.Session()
		s.mount('http://', HTTPAdapter(max_retries=3))
		s.mount('https://', HTTPAdapter(max_retries=3))

		
		if self.userid.isdigit():
			url = 'https://m.facebook.com/profile.php?id=' + self.userid
		else:
			url = 'https://m.facebook.com/' + self.userid
		r = s.get(url, headers = self.__headers, proxies = self.__proxies)
		html_text = r.text.replace('<!--', '').replace('-->', '')
		html_doc = pq(html_text)

		# 获取每一条说说的内容
		# 含有aria-label="Open story"的a标签
		# 拼接url: https://m.facebook.com/
		section_node = html_doc('section')
		posts_node = html_doc('article')
		posts_count = 0
		for node in posts_node.items():
			href = html.unescape(node('a:first[aria-label="Open story"]').attr('href'))
			posts_count += 1


		# 获取下一页说说列表链接，直到匹配不到或posts_url_list超过20条
		# 正则匹配含有replace_id的href链接
		next_url_obj = re.compile(r'href:"(\S*)replace_id=(\S*?)",').findall(html_text)

		if next_url_obj:
			next_url = 'https://m.facebook.com' + next_url_obj[0][0] + 'replace_id=' + next_url_obj[0][1]
			# 能找得到下一页的url或者已存储说说内容超过20条
			while ((posts_count <= 50) and next_url != ''):
				r = s.get(next_url, headers = self.__headers, proxies = self.__proxies)

				# 尝试解析响应内容
				try:
					resp = json.loads(r.text.replace('for (;;);', ''))
				except Exception as e:
					print('getting posts: decode next_url content error')
					break

				# 提取post内容和js内容
				post_content = resp['payload']['actions'][0]['html']
				js_code = resp['payload']['actions'][2]['code']

				# 解析post
				dom = pq(post_content)
				next_article_node = dom('article')
				for node in next_article_node.items():
					section_node.append(node.html())
					posts_count += 1

				# 尝试获取下一页url
				try:
					cursor, start_time, profile_id, replace_id = re.compile(r'cursor=(.*?)&start_time=(.*?)&profile_id=(.*?)&replace_id=(.*?)"').findall(js_code)[0]
				except Exception as e:
					break

				# 拼接下一页url
				next_url = 'https://m.facebook.com/profile/timeline/stream/?cursor=' + cursor + '&start_time=' + start_time + '&profile_id=' + profile_id + '&replace_id=' + replace_id

		posts_html = section_node.html()

		# 修正脏数据
		dirty = set(re.compile(r'\\\\.{2} ').findall(posts_html))
		for x in dirty:
			posts_html = posts_html.replace(x, '%' + x[2] + x[3])
		self.posts = parse.unquote(posts_html)

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
