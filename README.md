# OnlineEducationPlatform

## 项目描述
一个前后端分离的在线学习平台, 实现在线浏览视频详情, 观看视频, 在线购买课程, 支持支付宝付款, 使用Redis存储购物车及订单数据提高访问效率, 支持不同价格策略购买课程。

## 项目功能

在线平台部分主要为vue提供接口功能，接口基于django rest framewok框架的基础搭建，利用其内置组件和⾃定义扩展实现JWT⽤户认证，根据依赖django-redis组件实现对缓存的操作。

在线业务主要将课程分为“免费课”和“专题课”，基于django contenttype组件实现课程多价格策略，为了减轻数据库压力将临时购买信息放⼊redis以便操作，购物流程包含 ⻉里、优惠券、⽀付宝联合支付。在线通知使用阿⾥短信接⼝对购买、提交作业、咨询等信息的提醒。最后使用保利威视在线视频播放的功能。

## 已实现功能

1. 基于Django Rest Framework框架搭建后端API
2. 基于支付宝, 第三方接口开发购物车, 结算中心, 支付后端逻辑代码
3. 基于JWT+极验验证实现Authentication模块, 增加本网站的反爬机制, 提高数据安全
4. 使用redis缓存用户账单信息，减轻数据库压力
5. 使用Vue element-ui搭建前端单页面应用

## 待完善功能

1. 保利威视在线视频播放的功能
2. 微信支付功能
3. 阿里云短信通知功能
4. celery异步任务发送邮件通知订单状态功能


## 部署
1. 下载代码
2. 新建虚拟环境
3. 解决python模块依赖问题，`pip3 install -r requirements.txt`
4. 修改项目配置
    1. 支付宝支付配置
        1. `mkdir keys`
        2. 上传支付宝公钥文件到keys目录下，`alipay_public_2048.txt`
        3. 上传APP私钥到keys目录下，`app_private_2048.txt`
        4. 将项目settings.py中关于支付宝的配置
            1. 168行修改app_id
            2. 175,176行将 return_url,notify_url修改为自己服务器地址加路由，http://ip:8000/trade/alipay/
    2. 极验滑动验证配置，在setting.py文件中154，155行将gee_test_access_id，gee_test_access_key 修改为自己极验的配置
    3. 在./api/views/trade.py中26行 将 `http://localhost:80` 修改为前端服务器地址    
5. 数据库
    1. 启动redis服务 `systemctl start redis` 或者 `redis-server redis.conf `
    2. 为测试方便，采用sqlite文件数据库，如需求自行更换
6. 运行项目 `python3  manage.py  runserver 0.0.0.0:8000`    
 
 
 
## Nginx + uwsgi  部署

1. 部署1-5步骤
2. 准备uwsgi配置文件
   ```
    # vim uwsgi.ini,创建配置文件
    [uwsgi]
    # Django-related settings
    # the base directory (full path)
    # 指定django的项目目录，第一层
    chdir           = /opt/OnlineEducationPlatform/OnlineEducationPlatform
    # Django's wsgi file
    # 找到django的wsgi文件
    # 这里需要写项目的第二层目录 OnlineEducationPlatform
    module          = OnlineEducationPlatform.wsgi
    # the virtualenv (full path)
    #填写虚拟环境的绝对路径
    home            =/root/Envs/OnlineEducationPlatform
    # process-related settings
    # master
    master          = true
    # maximum number of worker processes
    processes       = 5
    # the socket (use the full path to be safe
    #指定socket协议，运行django，只能与nginx结合时使用
    #指定socket协议，运行django，只能与nginx结合时使用
    #指定socket协议，运行django，只能与nginx结合时使用
    socket          = 0.0.0.0:9000
    
    #如果你没用nginx，只想自己启动一个http界面，用这个
    #http =  0.0.0.0:8000
    
    # ... with appropriate permissions - may be needed
    # chmod-socket    = 664
    # clear environment on exit
    vacuum          = true
   
   ```
3. 配置nginx，增加 nginx 第二个虚拟主机
   ```
    server {
     listen 8000;
     server_name _;
     location / {
         # 把接收到的请求转发给 wwsgi 运行的端口
          uwsgi_pass 127.0.0.1:9000;
         # 把另一文件的参数包含进来
          include /etc/nginx/uwsgi_params;
      }
    }
   ```
4. 重启 nginx, 启动 uwsgi
    1. `nginx -s reload`
    2. `uwsgi --ini uwsgi.ini`


## 表结构设计

1. 课程表
   1. 课程分类表
   2. 课程表
   3. 课程详情表
   4. 教师表
   5. 价格与课程有效期表
   6. 课程章节表 
      1. 暂时没用到
   7. 课程目录表
      1. 关联课程，不同类型的课程
   8. 常见问题表
2. 优惠券表
3. 订单表
4. 用户表


## 技术栈 & 一些问题

### contenttypes 

Django ContentTypes是由Django框架提供的一个核心功能，它对当前项目中所有基于Django驱动的model提供了更高层次的抽象接口。 

django_content_type记录了当前的Django项目中所有model所属的app（即app_label属性）以及model的名字（即model属性）

model层的多态，一张表可以绑定任意一张表。  

应用，一张表内可能需要与多张表关联，但关联的N张表，不需要同时用到，只需要一张表中的几种，如果同时增加N个外键，消耗资源， 第一次优化，可以将表之间的关系抽出，新建一张表，只存Id,与其内存，(提高范式)，第二次优化，第一次优化仅仅是提高了范式，仍然会有资源浪费，这时可以使用contenttypes，存储指定表的信息。

参考

https://www.cnblogs.com/liwenzhou/p/10277883.html

https://www.cnblogs.com/whj233/articles/11295606.html





### AbstractUser

用户表继承于这个 表  ，使用Django自带的操作对密码加密存储，    使用一些集成的方法

需要在 settings 中告诉django



详情 https://www.django.cn/article/show-18.html



Django 默认密码存储格式

`<algorithm>$<iterations>$<salt>$<hash>`

这些是用来存储用户密码的插件，以美元符号分隔，包括：哈希算法，算法迭代次数（工作因子），随机 Salt 和最终的密码哈希值。该算法是 Django 可以使用的单向哈希或密码存储算法中的一种；见下文。迭代描述了算法在哈希上运行的次数。Salt 是所使用的随机种子，哈希是单向函数的结果。

默认情况下，Django 使用带有 SHA256 哈希的 [PBKDF2](https://en.wikipedia.org/wiki/PBKDF2) 算法



### 跨域

前后分离项目必然出现跨域问题，究其原因是因为同源策略，协议-ip-port ，三者相同才同源，否则将受到限制，即使服务器正常响应，浏览器也不接受。前后端分离后，或者说动静分离后，两个项目将部署到不同的服务上所以导致二者不同源。



1. 解决方法

nginx反向代理，将前端部署在Nginx下，Nginx作为调用后端服务的代理，这样前端的所有请求都直接指向Nginx地址，而由Nginx去具体请求后端服务。这样对于前端来说，它所有的请求都是在本域下发起的，就没有跨域的问题了。

[三分钟解决前后端分离项目中的跨域问题](https://segmentfault.com/a/1190000012668773#articleHeader2)

[Nginx反向代理](https://www.cnblogs.com/whj233/articles/10952502.html#1982920074)

[为什么会有同源策略](https://www.cnblogs.com/whj233/articles/11286126.html#2337460745)



2. CORS   

此项目采用的跨域方式是CORS.

[CORS](https://www.cnblogs.com/whj233/articles/11286126.html#2337460745)

自定义了  CorsMiddleWare  ，由于API发送的都是非简单请求，就简单的自定义了一下，没有使用 `django-core-headers` 模块



### 认证 

#### JWT

采用JWT方式认证



pyjwt模块常用操作

```python
import jwt

key = "&^JYRKYVJfytd%()&HKVJFI&$)*TYT%*&%&OIVFGUY^$" # 签名秘钥，很重要
encoded_jwt = jwt.encode(payload={'data': '111'}, key=key, algorithm='HS256') # 生成JWT
pyload = jwt.decode(jwt=encoded_jwt, key=key)	# 解码JWT
pyload_not_verify = jwt.decode(jwt=encoded_jwt, verify=False) # 不进行验签
```



##### 原理

[Json Web Token](https://www.cnblogs.com/whj233/articles/11364778.html)



##### 参考

1. [PyJWT介绍](https://juejin.im/post/5c46f6d1f265da61407f3456#heading-0)
2. [Vue.js解析jwt](https://my.oschina.net/hutaishi/blog/1574733)



#### ExpiringJWTAuthentication

认证组件继承于 `rest_framework.authentication.BaseAuthentication`   重写 `authenticate` 方法，实现对

token 的认证。

认证策略

1. 如果 请求请求方法是 `OPTIONS` , 表明这是预检请求（跨域方式采用CORS），返回 Node
2. 拿到用户请求携带的 jwt_token `request.META.get("HTTP_AUTHORIZATION")`
3. 解析 jwt_token ,生成 payload
4. 如果 payload 为空，抛出异常  `raise AuthenticationFailed("认证失败!")`
5. 如果 jwt 已过期，抛出异常 `raise AuthenticationFailed("JWT已过期!")`
6. 如果数据库中查询不到用户，抛出异常 `raise AuthenticationFailed("用户不存在!")`
7. 一切正常，返回 （user,jwt_token）







### 权限

#### LoginUserPermission

继承于`rest_framework.permissions.BasePermission` 重写 `has_permission` 方法，判断 `request.user`实现对用户权限校验。





### 时区 

设置  如下，

```
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = True
```



#### 实验

测试不同设置在Django中的显示

1. TIME_ZONE = 'Asia/Shanghai'
   USE_TZ = False
2. TIME_ZONE = 'Asia/Shanghai'
   USE_TZ = True
3. 默认



实验环境 python3.7, django 2.2

参数

设置是在settings中的不同设置，

时间是生成时间的工具（datetime模块，django.utils.timezone模块），

前端是生成的时间在前端显示的时间，

前端SQL是SQL时间显示到前端的时间

后台是直接生成的时间，

SQL是生成时间插入数据库后的时间，

model auto 是Model 自动生成的时间

local 代表本地时间，utc代表utc时间



| 设置                                       | 生成时间                | 前端  | 前端SQL | 后台  | SQL   | model auto |
| ------------------------------------------ | ----------------------- | ----- | ------- | ----- | ----- | ---------- |
| TIME_ZONE = 'UTC' USE_TZ = True            | datetime.datetime.now() | local | local   | local | local | utc        |
| TIME_ZONE = 'Asia/Shanghai‘ USE_TZ = False | datetime.datetime.now() | local | local   | local | local | local      |
| TIME_ZONE = 'Asia/Shanghai' USE_TZ = True  | datetime.datetime.now() | local | local   | local | utc   | utc        |
| TIME_ZONE = 'UTC' USE_TZ = True            | timezone.now()          | utc   | utc     | utc   | utc   | utc        |
| TIME_ZONE = 'Asia/Shanghai‘ USE_TZ = False | timezone.now()          | local | local   | local | local | local      |
| TIME_ZONE = 'Asia/Shanghai' USE_TZ = True  | timezone.now()          | local | local   | utc   | utc   | utc        |



timezone.now() 源码，可以看出，只要 USE_TZ 为 True 生成的就是 utc时间

```python
def now():
    """
    Return an aware or naive datetime.datetime, depending on settings.USE_TZ.
    """
    if settings.USE_TZ:
        # timeit shows that datetime.now(tz=utc) is 24% slower
        return datetime.utcnow().replace(tzinfo=utc)
    else:
        return datetime.now() # datetime 就是datetime.datetime

```



#### 总结

根据上面实验，可以在服务器生成的时间在被添加到数据库时会变换，当被应用到模板中也会变化。

**数据库时间**

只要设置了USE_TZ=True之后，在服务器生成的时间存到数据库时都会被转化为UTC时间。

**模板显示时间**

在设置了USE_TZ=True之后，如果设置了**TIME_ZONE** = 'Asia/Shanghai'，尽管数据库中存储的是UTC时间，但在模板显示的时候，会转成**TIME_ZONE**所示的本地时间进行显示。

**建议**

为了统一时间，在django开发时，尽量使用UTC时间，即设置USE_TZ=True，**TIME_ZONE** = 'Asia/Shanghai'，并且在获取时间的时候使用django.util.timezone.now()。因为后台程序使用时间时UTC时间就能满足，也能保证证模板时间的正确显示。



#### 参考

[Time zones](https://docs.djangoproject.com/en/2.1/topics/i18n/timezones/)

[为什么Django设置时区为TIME_ZONE = 'Asia/Shanghai' USE_TZ = True后，存入mysql中的时间只能是UTC时间](https://blog.csdn.net/qq_27361945/article/details/80580795)

[Django设置TIME_ZONE为中国，及其规则与善后问题](https://blog.csdn.net/WY00703/article/details/45071277)
[django时区问题时间差8小时](https://www.jianshu.com/p/c1dee7d3cbb9)



### 极验配置

注册账号，配置参数



服务端配置

1. 配置极验参数，
2. 需要安装 `request` 模块，
3. 搭建两个API
   1. 一个用于 客户端初始化验证码参数，客户端向服务器发请求，然后服务器再请极验服务器发请求，获取所需参数。如果极验服务器宕机，验证信息将由服务器本地生成，本地二次校验。
   2. 另一个用于二次验证,校验客户端是否验证，本次请求是否放行。如果信息初始化时采用本地生成， 那么二次验证也将采用本地验证。

[部署文档](https://docs.geetest.com/install/deploy/client/web)



客户端配置

1. 需要在项目在配置 [gt.js 文件,](http://static.geetest.com/static/tools/gt.js)  ,需要页面初始化时向服务器查极验所需参数，再调用 `initGeetest `方法

 [客户端API](https://docs.geetest.com/install/apirefer/api/web/)



tips

1. 如果在用户后台发现验证成功但其他信息不对的情况（比如用户名密码错误），或者验证出现错误的情况。可以使用 `captchaObj.reset();` 重置接口进行再次验证。



数据通讯图

![](https://docs.geetest.com/install/overview/imgs/geetest_netwoking_sequence.jpg)







### cache

缓存使用Redis，应用于 购物车和用户订单信息。

常用操作

```
from django.core.cache import cache
cache.set("key", "value", timeout=None) # key，value键值对,timeout过期时间
cache.get("key")  # 获取key对应的value
cache.ttl("key") # 获取key对应的timetou
cache.persist("key") # 设置key永不超时，0表示已经过期，Node表示永不过期
```



文档

1. [django-redis 中文文档](https://django-redis-chs.readthedocs.io/zh_CN/latest/)
2. [缓存相关](https://www.cnblogs.com/whj233/articles/11295529.html)







### 支付宝支付

#### SDK、库

##### alipay-sdk-python

官方SDK，Python版本像怎么感觉是JAVA程序员写的。。。

实例SDK https://docs.open.alipay.com/54/103419

##### python-alipay-sdk

目前更新的 支付宝Python接口，第一次commit 18 Nov 2016

[python-alipay-sdk文档](https://github.com/fzlee/alipay/blob/master/README.zh-hans.md)



#### 文档

[python-alipay-sdk文档](https://github.com/fzlee/alipay/blob/master/README.zh-hans.md)

 [alipay.trade.page.pay(统一收单下单并支付页面接口)](https://docs.open.alipay.com/api_1)

[电脑网站支付文档 ](https://docs.open.alipay.com/270/105899/)



#### 支付宝App支付的流程

1. 服务端根据 支付宝接口 [alipay.trade.page.pay](https://docs.open.alipay.com/api_1/alipay.trade.page.pay) 生成一个URL返回给客户端，注意此时并没有访问支付宝服务器
2. 客户端拿到URL访问，进行支付
3. 支付成功后，支付宝会发送一个get\post请求
   1. 用户确认支付后，支付宝通过 get 请求 returnUrl（商户入参传入），返回同步返回参数。
   2. 交易成功后，支付宝通过 post 请求 notifyUrl（商户入参传入），返回异步通知参数。
4. 若由于网络等问题异步通知没有到达，商户可自行调用交易查询接口 [alipay.trade.query](https://docs.open.alipay.com/api_1/alipay.trade.page.pay) 进行查询，根据查询接口获取交易以及支付信息（商户也可以直接调用查询接口，不需要依赖异步通知）





#### 源码分析

python-alipay-sdk 模块的 `alipay.api_alipay_trade_page_pay` `alipay.verify` 两个方法

alipay.api_alipay_trade_page_pay

方法作用，根据配置生成支付页面URL

1. 构件请求数据体，内部包含必要参数和其他一些参数
2. 对数据加签，此时数据是一个字典类型
   1. 将value是字典类型数据dumps重新存储
   2. 将字典转换为列表按 (key,value) 排序 
   3. 将列表变为`{}={}&{}={}`字符串格式，然后对字符串进行签名
   4. 将列表数据变为URL格式，加上签名
   5. 返回



alipay.verify

1. 拿到返回的数据
2. 去除不需要验签的数据 sign_type ，sign
3. 将数据按照字典排序，然后进行URLdecode
4. 对数据进行验签
5. 返回结果

[异步返回结果的验签](https://docs.open.alipay.com/270/105902/)

[自行实现验签 ](https://docs.open.alipay.com/200/106120)









### VueX

状态管理器，

三大将， state, mutations ,  Action  ,全局实例化一个store,state 存储状态，改变 state 的唯一方式就是提交 mutations，是同步操作 ,  Action 用于实现异步逻辑。 

[文档](https://vuex.vuejs.org/zh/)

mutations  触发， store.commit('decrement', 10) ， store.commit('increment')

Action ,触发  store.dispatch('increment')

```vue
let store = new Vuex.Store({
	// 三大将
	state:{
		count:1
	},
	// 修改state的唯一方法 是提交mutations, 必须同步操作
	mutations:{
        increment (state) {
          // 变更状态
          state.count++
        }
        decrement (state, payload) {
        	state.count += payload
        }
	},
  // 异步逻辑都应该封装到 action 里面
	actions:{
    increment (context) {
    	context.commit('increment')
    }
	// 参数解构  { commit }
      increment ({ commit }) {
        commit('increment')
      }
	}
});

```



man.js

```vue
const app = new Vue({
  el: '#app',
  // 把 store 对象提供给 “store” 选项，这可以把 store 的实例注入所有的子组件
  store,
  components: { Counter },
  template: `
    <div class="app">
      <counter></counter>
    </div>
  `
})
```



组件中

```
const Counter = {
  template: `<div>{{ count }}</div>`,
  computed: {
    count () {
    	// 获取状态
      return this.$store.state.count
    }
  }
}
```



### localStorage

localStorage 存储到浏览器中的数据，K-V 数据结构，默认永久，如果需要设置过期时间需要对其封装, 默认约定大小5M。



| 特性         | Cookie                                                       | localStorage             | sessionStorage                               |
| ------------ | ------------------------------------------------------------ | ------------------------ | -------------------------------------------- |
| 生命周期     | 一般由服务器生成，可设置失效时间。如果在浏览器端生成Cookie，默认是关闭浏览器后失效 | 除非被清除，否则永久保存 | 仅在当前会话下有效，关闭页面或浏览器后被清除 |
| 存放数据大小 | 4K左右                                                       | 一般为5MB                | 一般为5MB                                    |
| 作用域       | 协议+ip+port                                                 | 协议+ip+port             | 窗口+协议+ip+port                            |



localStorage 常用方法

```
localStorage.setItem("b","isaac");//设置b为"isaac"
var b = localStorage.getItem("b");//获取b的值,为"isaac"
var a = localStorage.key(0); // 获取第0个数据项的键名，此处即为“b”
localStorage.removeItem("b");//清除c的值
localStorage.clear();//清除当前域名下的所有localstorage数据
```



参考


[localstorage 必知必会](https://segmentfault.com/a/1190000004121465)

[详说 Cookie, LocalStorage 与 SessionStorage](https://jerryzou.com/posts/cookie-and-web-storage/)



### binascii 模块

binascii模块 Byte与ASCII 互转    

struct模块 , 任意数据类型与Byte

[文档 ](https://docs.python.org/zh-cn/3/library/binascii.html)



`binascii.``b2a_hex`(*data*)

`binascii.``hexlify`(*data*)

返回二进制数据 *data* 的十六进制表示形式。 *data* 的每个字节都被转换为相应的2位十六进制表示形式。因此返回的字节对象的长度是 *data* 的两倍。

使用：[`bytes.hex()`](https://docs.python.org/zh-cn/3/library/stdtypes.html#bytes.hex) 方法也可以方便地实现相似的功能（但仅返回文本字符串）。



`binascii.``a2b_hex`(*hexstr*)

`binascii.``unhexlify`(*hexstr*)

返回由十六进制字符串 *hexstr* 表示的二进制数据。此函数功能与 [`b2a_hex()`](https://docs.python.org/zh-cn/3/library/binascii.html#binascii.b2a_hex) 相反。 *hexstr* 必须包含偶数个十六进制数字（可以是大写或小写），否则会引发 [`Error`](https://docs.python.org/zh-cn/3/library/binascii.html#binascii.Error) 异常。

使用：[`bytes.fromhex()`](https://docs.python.org/zh-cn/3/library/stdtypes.html#bytes.fromhex) 类方法也实现相似的功能（仅接受文本字符串参数，不限制其中的空白字符）。



### UUID

uuid 生成一个随机的字符串

#### 介绍

UUID: 通用唯一标识符 ( Universally Unique Identifier ), 对于所有的UUID它可以保证在空间和时间上的唯一性. 它是通过MAC地址, 时间戳, 命名空间, 随机数, 伪随机数来保证生成ID的唯一性, 有着固定的大小( 128 bit ).  它的唯一性和一致性特点使得可以无需注册过程就能够产生一个新的UUID. UUID可以被用作多种用途, 既可以用来短时间内标记一个对象, 也可以可靠的辨别网络中的持久性对象.
　　为什么要使用UUID?

　　很多应用场景需要一个id, 但是又不要求这个id 有具体的意义, 仅仅用来标识一个对象. 常见的例子有数据库表的id 字段. 另一个例子是前端的各种UI库, 因为它们通常需要动态创建各种UI元素, 这些元素需要唯一的id , 这时候就需要使用UUID了.

#### uuid模块

python的uuid模块提供UUID类和函数uuid1(), uuid3(), uuid4(), uuid5() 来生成1, 3, 4, 5各个版本的UUID ( 需要注意的是: python中没有uuid2()这个函数). 对uuid模块中最常用的几个函数总结如下:、

- **uuid.uuid1(node, clock_seq) : 基于MAC地址，时间戳，随机数**　　

  基于MAC地址，时间戳，随机数来生成唯一的uuid，可以保证全球范围内的唯一性。但由于使用该方法生成的UUID中包含有主机的网络地址, 因此可能危及隐私。 该函数有两个参数, 如果 node 参数未指定, 系统将会自动调用 getnode() 函数来获取主机的硬件地址. 如果 clock_seq  参数未指定系统会使用一个随机产生的14位序列号来代替

- uuid.uuid2()　　

  算法与uuid1相同，不同的是把时间戳的前4位置换为POSIX的UID。不过需要注意的是python中没有基于DCE的算法，所以python的uuid模块中没有uuid2这个方法。

- **uuid.uuid3(namespace, name) : 基于名字的MD5散列值**　　

  通过计算一个命名空间和名字的md5散列值来给出一个uuid，所以可以保证命名空间中的不同名字具有不同的uuid，但是相同的名字就是相同的uuid了。namespace并不是一个自己手动指定的字符串或其他量，而是在uuid模块中本身给出的一些值。比如uuid.NAMESPACE_DNS，uuid.NAMESPACE_OID，uuid.NAMESPACE_OID这些值。这些值本身也是UUID对象，根据一定的规则计算得出。

- **uuid.uuid4() : 基于随机数**　　

  通过随机数来生成UUID. 使用的是伪随机数有一定的重复概率

- **uuid.uuid5(namespace, name) : 基于名字的SHA-1散列值**　　

  和uuid3基本相同，只不过采用的散列算法是sha1

#### 简单使用

```
import uuid

name = '233'
namespace = uuid.NAMESPACE_OID
u1 = uuid.uuid1()
u3 = uuid.uuid3(namespace, name)
u4 = uuid.uuid4()
u5 = uuid.uuid5(namespace, name)
print(u1)
print(u3)
print(u4)
print(u5)

```



```
15f8047a-c70d-11e9-90de-c85b760945ba
6b419265-56cc-35c7-8c55-17242c752880
59b0df4a-5758-4598-9548-988045b0db99
82e8d28b-ad16-5f73-b3d7-a1e4b8e86de3
```





#### 参考

1. [python之uuid通用唯一标识符模块](https://www.jianshu.com/p/d128a3e17d0a)



### DRF-view 

[详细文档](https://www.cnblogs.com/whj233/articles/11364751.html)

view ，django CBV的view,拥有 `dispatch()` 方法,通过反射向CBV中分发请求

APIView，继承view ，重写了 `dispatch()` 方法，增加了 内容协商，版本控制，认证，权限，限制功能，并将原来 django 的 HttpRequest对象 更新为 rest_framework 重写的 Request 对象，在重写的 Request 对象中，原来的 request 对象变为 request._request ,还新增了 request.data ,为根据 request.content_type 解析出的数据， request.query_params 为URL中的参数

GenericAPIView,继承于APIView ,增加了 `get_queryset()` `get_serializer()` `paginator()`方法，对应的功能是 queryset ，序列化，分页，只需赋予 queryset对象，序列化类，分页类即可自动完成操作。

ViewSetMixin ,重写 `as_view()`方法，根据路由url中 action参数直接将 一个请求绑定一个方法，然后再用 GenericAPIView 中的 `dispatch()` 方法进行分发

GerericViewSet ,继承于 ViewSetMixin ，GenericAPIView

ListModelMixin，实现 `list()` 方法，返回一个queryset的列表，对应于 get 

CreateModelMixin, 实现`create()`方法 ,创建一个实例，对应于 post

RetrieveModelMixin,实现`retrieve()`方法, 返回一个具体实例，对应于 get 

UpdateModelMixin,实现`update()`方法 ,对某个实例进行更新，对应于 put/patch

DestroyModelMixin,实现`destroy()`方法,删除某个实例，对应于 delete



ModelViewSet , 继承于 GerericViewSet ，ListModelMixin，CreateModelMixin，RetrieveModelMixin，UpdateModelMixin，DestroyModelMixin





### Pycharm terminal 中无法执行 pip 命令

问题描述，在 pycharm terminal中无法中执行与 python 相关的命令，无法执行虚拟环境中的命令( scripts文件中的执行文件)，也无法执行全局环境中的 pyhton 命令( scripts文件中的执行文件)。然后在操作系统中打开一个 终端窗口，可以执行全局 python 命令，进入虚拟环境后，也可以执行虚拟环境的命令。



尝试过的方法：

1. 本地远程开发，利用 pycham 的 Deloyment 远程开发功能，SFTP本地阅读、编辑代码，上传更新，SSH session 远程执行命令，另外也可以用ssh配置远程的解释器 。
2. 迁移Linux开发，虚拟机下装好图形化界面，配好IDE后发现内存根本不够，分配3G只剩 80M，而且很卡，放弃无果。
3. 重新安装 python 解释器，失败无果。
4. 重新安装 pycharm IDE，失败无果。
5. powershell 中虚拟环境操作，奇怪的是在 powershell  中进入虚拟环境后，执行命令结果却是全局环境中的结果。需要注意的是在 powershell  中默认无法执行脚本命令，需要设置权限，[详情](https://www.cnblogs.com/zhaozhan/archive/2012/06/01/2529384.html)。但是设置后，扔然无法直接执行，需要在 相对路径 下执行。





解决方案：

手动重新进入虚拟环境，即可以运行虚拟环境下的 pip,pyhotn...等命令 

1. 切到需虚拟环境 script 目录 
   1. 找到虚拟环境目录， 创建项目-->创建虚拟环境 --> 默认就是虚拟环境目录
   2. `cd C:\Users\***\.virtualenvs\`
   3. `cd 虚拟环境名`  ，虚拟环境名就是当前命令行前面括号中的名字
   4. `cd  Scripts`  
   5. 一条命令  `cd  C:\Users\***\.virtualenvs\虚拟环境名\scripts`
2. 退出虚拟化境
   1. `deactivate`
3. 进入虚拟环境
   1. `activate`
4. 完成



### Crypto模块安装

1. 问题描述，在windows上直接通过 `pip install crypto`  ，无法安装缺少 VC 库。

解决方法，手动下载对应版本whl包安装，编译好的文件，不需要其他依赖。 

2. 安装好之后 run ,提示 `ModuleNotFoundError: No module named 'Crypto'` 报错

解决方法，去对应虚拟环境目录下将 `*\虚拟环境\lib\site-packages\crypto`   crypto 文件夹名修改为 Crypto

3. 使用某一功能，继续报错，`ModuleNotFoundError: No module named 'winrandom'`

解决方法，去对应虚拟环境 `lib\site-packages\Crypto\Random\OSRNG\nt.py`  ，将第28行 `import winrandom` 修改为 `from . import winrandom` 



参考 

[ImportError: No module named Crypto.Cipher](https://stackoverflow.com/questions/19623267/importerror-no-module-named-crypto-cipher)


## 后端接口详情

### /login 

#### -post

调用滑动验证模块，对其校验，如果通过再对用户名、密码进行校验，校验成功后生成或更新token存入数据库，返回给用户响应。



request

```
{
    "username": "",
     "password": " ",
     "geetest_challenge": "",
     "geetest_validate": "",
     "geetest_seccode": ""
 }
```



response



登录失败

```
{
    "code":,
    "msg": "",
    "data":
}

```

登录成功

```
{
    "code":,
    "msg": "",
    "data"：{
    	token："",
		userinfo: {
			username："",
			head_img:"",
		}
    }
}


```



错误代码

1. code：1000，正常
2. code：1001，滑动验证校验失败，重新完成滑动验证
3. code：1002，密码错误
4. code：1003，用户不存在



### /logout

#### delete

用户登出操作，先进行用户认证 ，然后进行权限识别，如果都通过，进行登出操作，返回给用户响应。



认证：ExpiringJWTAuthentication

权限 ：LoginUserPermission





### /course/category

request

```
course/category/ 
```

response

```
{
    "error_no": 0,
    "data": [
        {"id": 1, "name": "Python"},
        ...
    ]
}
```





### /courses

request

```
/courses/?category_id=id 
```

response

```
{
	"code": 0,
	"data": [
        {
            "id": 1,
            "name": "",
            "course_img": "",
            "brief": "",
            "level": "",
            "coursedetail_id": "",
            "is_free": false,
            "price": "",
            "origin_price": ""
        },
        ...
	]
}
```





### /coursedetail/id

request

```
/coursedetail/id/ 
```

response

```
{
	"id": 1,
	"name": "",
	"prices": [{
		"id": 1,
		"valid_period": 7,
		"valid_period_name": "1周",
		"price": 100.0
	}, 
	...
	],
	"brief": "",
	"study_all_time": "",
	"level": "",
	"teachers_info": [{
		"teacher_id": "1",
		"teacher_name": "",
		"title": "",
		"signature": "",
		"teacher_image": "",
		"teacher_brief": ""
	}],
	"is_online": true,
	"recommend_coursesinfo": [{
		"course_id": "",
		"course_name": ""
	}, {
		"course_id": "",
		"course_name": ""
	}],
	"hours": 100,
	"course_slogan": "",
	"video_brief_link": "",
	"why_study": "",
	"what_to_study_brief": "",
	"career_improvement": "",
	"prerequisite": "",
	"course": 22,
	"recommend_courses": [],
	"teachers": []
}
```



### /account

#### get

获取刚才新建账单的信息



request

```
/account/
```

response

```
{
    "code": 1000,
    "msg": "",
    "data": {
        "account_course_list": [{
            "id": 2,
            "name": "",
            "course_img": "",
            "relate_price_policy": {
                "1": {
                    "prcie": 100.0,
                    "valid_period": 7,
                    "valid_period_text": "1周",
                    "default": true
                },
                ...
            },
            "default_price": 100.0,
            "rebate_price": 100.0,
            "default_price_period": 7,
            "default_price_policy_id": 1,
            "coupon_list": [{
                "pk": 3,
                "name": "",
                "coupon_type": "",
                "money_equivalent_value": 0.0,
                "off_percent": 80,
                "minimum_consume": 0
            },
            ...
            ]
        },
        ...
        
        ],
        "total": 1,
        "global_coupons": [{
            "pk": 2,
            "name": "",
            "coupon_type": "满减券",
            "money_equivalent_value": 50.0,
            "off_percent": null,
            "minimum_consume": 100
        },
        ...
        ],
        "total_price": "100.0"
    }
}

```



错误代码

1. 1000,正常
2. 1101，获取购物车失败



#### post

新建一个账单，存储到redis中。数据结构见 get 请求返回的数据

存储的数据结构

```
{
    "account_course_list": [{
        "id": 2,
        "name": "",
        "course_img": "",
        "relate_price_policy": {
            "1": {
                "prcie": 100.0,
                "valid_period": 7,
                "valid_period_text": "1周",
                "default": true
            },
            ...
        },
        "default_price": 100.0,
        "rebate_price": 100.0,
        "default_price_period": 7,
        "default_price_policy_id": 1,
        "coupon_list": [{
            "pk": 3,
            "name": "",
            "coupon_type": "",
            "money_equivalent_value": 0.0,
            "off_percent": 80,
            "minimum_consume": 0
        },
        ...
        ]
    },
    ...

    ],
    "global_coupons": [{
        "pk": 2,
        "name": "",
        "coupon_type": "满减券",
        "money_equivalent_value": 50.0,
        "off_percent": null,
        "minimum_consume": 100
    },
    ...
    ],
    "total_price": "100.0"
}
```





request

```
[
    {
        "course_id":1,
        "price_policy_id":2
    },
]
```



response

```
{
	"code" : 100X,
	"msg" : "",
	"data" : null
}
```



错误代码

1. 1000，正常
2. 1102,价格策略异常
3. 1103，课程不存在



#### put

获取当前账单总价格

request

```
{"is_beli":"true","choose_coupons":{"global_coupon_id":id,course_id:coupon_id}}
{"is_beli":"false","choose_coupons":{"2":1,"global_coupon_id":2}}

global_coupon_id 通用优惠券
id 通用优惠券id
course_id 课程id
coupon_id 优惠券id 
```

response

```
{"code":1000,"msg":"","data":{course_id:rebate_price,"total_price":80.0}}
{"code":1000,"msg":"","data":{"1":123.22,"total_price":80.0}}


course_id 课程id str 类型
rebate_price 优惠后的价格
```



错误代码

1. 1000，正常
2. 1104，优惠券未达到最低消费
3. 5000，未知错误



### /shoppingcar



#### post

添加产品到购物车，先对前端传递参数进行验证，验证通过， 存储到redis中。key shopping_car_userId_courseId , value，JSON

数据结构,

```
course_info = {
    "id": "",
    "name": "",
    "course_img": "",
    "relate_price_policy": [
        "1": {
            "prcie": 100.0,
            "valid_period": 7,
            "valid_period_text": "1周",
            "default": true
        },
    	...
    
    ],
    "default_price": "",
    "default_price_period": "",
    "default_price_policy_id": ""
}

```



request

```
{"course_id":2,"price_policy_id":1}
```



response

```
{"code":1000,"msg":"","data":null}
```



错误代码

1. 1000，正常
2. 1201，价格策略异常
3. 1202，加入购物车失败



#### get

拿到用户id ，去redis里模糊匹配，拿到所有key，然后再查出对应的 value，返回给前端。

request

```
/shoppingcar
```



responde

```
{
	"code": 1000,
	"msg": "",
	"data": {
		"shopping_car_list": [{
			"id": 2,
			"name": "",
			"course_img": "",
			"relate_price_policy": {
				"1": {
					"prcie": 100.0,
					"valid_period": 7,
					"valid_period_text": "1周",
					s"default": true
				},
				...
			},
			"default_price": 100.0,
			"default_price_period": 7,
			"default_price_policy_id": 1
		}],
		"total": 1
	}
}
```





错误代码

1. 1233，获取购物车失败



#### delete

删除购物车中某件物品，先对前端传递的 course_id 参数验证，如果课程存在，删除，返回前端响应。

request

```
{"course_id":2}
```

response

```
{"code":1000,"msg":"","data":"删除成功"}
```



错误代码

1. 1000，正常
2. 1203，删除的课程不存在
3. 1204，删除失败





### /payment

#### post

重新计算总价格，生成订单，返回支付URL



request

```
      {
      is_beli:true,
      course_list=[
                  {  course_id:1
                   default_price_policy_id:1,
                   coupon_record_id:2
                   },
                  { course_id:2
                   default_price_policy_id:4,
                   coupon_record_id:6
                   }
               ],
       global_coupon_id:3,
       pay_money:298
       }

```





response

```
{"code":1000,"msg":"","data":"URL"}
```



错误代码

1. 1000:  成功
1. 1301:  课程不存在
1. 1302:  价格策略不合法
1. 1303:  加入购物车失败
1. 1304:  获取购物车失败
1. 1305:  贝里数有问题
1. 1306:  优惠券异常
1. 1307:  优惠券未达到最低消费
1. 1308:  支付总价格异常
1. 5000：未知错误



### /myorder

#### get

获取用户的订单信息

request

```
/myorder/
```

response

```
{
	"code": 1000,
	"msg": "",
	"data": [{
		"order_number": "",
		"date": "",
		"status": "",
		"actual_amount": 111,
		"orderdetail_list": [{
			"original_price": 1000.0,
			"price": 1000.0,
			"course_name": "",
			"valid_period_display": ""
		},
        ...
		]
	},
	...
	]
}
```



### /get_pay_url

根据前端传递的订单id和支付价格，校验后返回支付URL

#### get

request

```
/get_pay_url/?order_number=${order_number}&final_price=${final_price}
```

response

```
{"code":1000,"msg":"","data":"URL"}
```



错误代码

1. 1000，正常
2. 1402，订单不存在



### /trade/alipay/

这个接口需要项目放到公网上支付宝才可以回调成功。

#### get

支付宝 return_url 回调地址，验签后向用户返回支付页面。



#### post

支付宝  notify_url 回调地址，验签后，改变订单状态，向支付宝发送响应。

