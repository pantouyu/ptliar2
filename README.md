# ptliar2
ptliar


#labels Featured
=PTLiar 2.0.11 (10/16发布)=

PTLiar是一个安全方便的PT流量作弊软件。

PTLiar的使用方法很简单，它是一个命令行工具，在Windows下，你需要运行command，或在PTLiar的目录创建批处理文件或快捷方式执行它。

==新版本改进==

为NexusPHP量身定做，防止被列入怀疑列表。


==使用方法==

1.将想要伪装上传的种子放到up_torrents目录下（运行过程中也可以加入）

2.将想要伪装下载的种子放到down_torrents目录下（运行过程中也可以加入）

3.运行PTLiar.exe 【选项】

4.挂机

5.退出PTLiar时，建议使用组合键Ctrl+C，等待程序自动退出。

==主要的可选选项==

-h 显示帮助

-l 列出支持的客户端列表

-c 使用某个客户端，默认utorrent2.21

-v 显示更多提示信息

-m 最大上传速度 kB/s， 默认2048kB/s

-M 最大下载速度 kB/s， 默认1048kB/s

-p 端口号

-e 如果你在使用ipv6，可以加上这个选项

-z 开启反作弊侦查模式，如果你有超过十个种子，建议加上这个选项，它会随机将某些种子的速度设为0，模仿真实情况

-f 跳过一些等待时间

-n 禁用'scrape'

-t 指定若干小时后自动结束

==示例==

1. PTLiar.exe

使用默认设置开始ptliar，最大上传速度2MB/s，最大下载速度1MB/s

2. PTLiar.exe -p 34567 -m 3000 -M 1000 -z -v -c uTorrent3.0

最大下载速度设为1000kB/s，最大上传速度设为3000kB/s，端口设为34567，开启zero-rate，模仿uTorrent3.0

==简要说明==

PTLiar 是如何防范作弊侦查的?

策略：

1.没有人正在上传时，PTLiar不会伪装下载。

2.有人正在上传，但是没有人真的正在下载，PTLiar也不会伪装下载。

3.没有人正在下载时，PTLiar不会伪装上传。

4.有人正在下载，但是没有人真的正在上传，PTLiar也不会伪装上传。

5.速度随机，只在每一次提交Tracker信息之后，更新速度，使随机程度最大化。

6.-z选项：随机将一部分种子的上传/下载速度置零。

协议：

1.伪装uTorrent客户端所有行为。

2.模仿uTorrent HTTP报头，header内容，顺序，客户端ID，urlencode特征等。

3.处理重定向。（正确应对葡萄等PT站点的防御措施）

==建议==

1.先下载后上传，只上传已下载过的种子，某些服务器将辅种认为作弊。

2.尽量使用上传/下载人数较多的种子。

3.开启-z。

4.不要将速度设置得太高。

==长期测试站点==

CHDBits(chdbits.org)

HDChina(hdchina.org)

HDStar(hdstar.org)

葡萄(pt.sjtu.edu.cn)