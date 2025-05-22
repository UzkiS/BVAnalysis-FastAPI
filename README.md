# BVAnalysis-FastAPI

使用豆包用 FastAPI 重构的[BVAnalysis](https://github.com/RWONG722/BVAnalysis) 添加了直播功能 全部代码都由豆包转换

添加 IP 限制,单 IP 一分钟限制访问 10 次

启动命令

```
pip install -r requirements.txt && python ./app.py
```

使用方式

```
http://127.0.0.1:5000/BVxxxxxxxxxx
http://127.0.0.1:5000/BVxxxxxxxxxx?p=1
http://127.0.0.1:5000/live/xxxxxxx
```
