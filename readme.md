# 写在前面  
获取facebook用户公开信息的小爬虫，写着玩的，目前还有很多坑先挖好，不定期填坑  

## 坑点  
目前仅实现了爬取公开的个人信息，好友列表，动态  
其中获取动态信息使用的是selenuim，不是分析api地址和返回的html结构进行获取，因此速度偏慢  
仅下拉页面10次，因此不保证能获取所有的动态  

# 快速开始  
克隆本项目到本地  
```bash
git clone git@github.com:yedanten/facebookspider.git
```  

安装依赖  
```bash
pip install -r requirements.txt
```  

# 使用帮助  
```
usage: facebookspider.py [-h] --cookies COOKIES -u URL [-A] [-b] [-f]
                         [--posts] [--photos] [--avatar] [--follow]

获取facebook用户公开的信息

optional arguments:
  -h, --help         show this help message and exit
  --cookies COOKIES  提供已登录账号的cookies供爬虫使用
  -u URL, --url URL  目标用户的主页地址 例:https://www.facebook.com/profile.php?id=1000
                     或 https://www.facebook.com/Jackma
  -A, --all          获取目标用户所有公开的信息, 包含个人信息，动态，朋友列表
  -b, --basic        获取目标用户所有公开的个人信息
  -f, --friends      获取目标用户所有公开的朋友列表
  --posts            获取目标用户公开的动态信息
  --photos           获取目标用户公开的相册图片
  --avatar           获取目标用户的头像
  --follow           跟随爬取目标用户的朋友列表
```  

示例  
```bash
python facebookspider.py --cookies "xxxxxxxxx" -u "https://www.facebook.com/profile.php?id=1000" -A
```  

友情提示: 参数 `-u/--url` 不限制PC端还是移动端的url，爬取的都是m端页面。该参数本质是解析user_id或username  

# 结果报告  
爬取的报告将在同目录下生成`report.html`和`report_post.html`  
如果指定`--follow`参数，将还会在`follow_res`目录下生成对应用户名的report.html，动态页将在`follow_res/posts`目录下生成  
看report.html就好了，有链接可以跳转到动态页进行查看的  