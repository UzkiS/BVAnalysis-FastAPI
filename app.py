import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import function

import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 添加中间件以处理代理头
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 替换为你的实际域名或IP
)

# 如果使用gzip压缩，确保它在代理头中间件之后
app.add_middleware(GZipMiddleware)

@app.middleware("http")
async def filter_invalid_requests_middleware(request: Request, call_next):
    path = request.url.path
    is_valid = (
        path == "/" 
        or path.startswith("/submit") 
        or path.startswith("/live/") 
        or path.startswith("/ip") 
        or re.search(r'BV[a-zA-Z0-9]{10}', path)
    )
    if not is_valid:
        return JSONResponse(status_code=403, content={"error": "Invalid request"})
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def index(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BV Analysis</title>
    </head>
    <body>
        <h1>BV Analysis</h1>
        <form action="/submit" method="get">
            <label for="bvid">BVID:</label>
            <input type="text" id="bvid" name="bvid" required>
            <label for="p">Page Number:</label>
            <input type="number" id="p" name="p">
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    """

# 添加新的路由处理直播推流链接请求
@app.get("/live/{room_id}")
@limiter.limit("10/minute")
async def get_live_stream(request: Request, room_id: int):
    stream_url = await function.room_play_url(room_id)
    if stream_url:
        return RedirectResponse(url=stream_url)
    else:
        return JSONResponse(status_code=404, content={"error": "未能获取到直播推流链接"})

@app.get("/submit", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def submit(request: Request):
    bvid = request.query_params.get('bvid')
    p = request.query_params.get('p', 1)
    logger.info(f"Received bvid: {bvid}, p: {p}")  # 添加日志输出
    try:
        p = int(p)
    except ValueError:
        p = 1
    return RedirectResponse(url=f"/{bvid}?p={p}")

@app.get("/ip")
@limiter.limit("10/minute")
async def get_client_ip(request: Request):
    return {"client_ip": request.client.host}

@app.get("/{param}")
@limiter.limit("10/minute")
async def BiliAnalysis(param: str, request: Request):
    logger.info(f"Received param: {param}")  # 添加日志输出
    bv_match = re.search(r'BV[a-zA-Z0-9]{10}', param)
    if bv_match:
        BV = bv_match.group(0)  # 提取到的 BV 号
        if len(BV) == 12 and BV.startswith('BV') and BV[2:].isalnum():
            p = request.query_params.get('p', 1)
            try:
                p = int(p)
            except ValueError:
                p = 1
            video_info = await function.BiliAnalysis(BV, p)
            videoUrl = video_info["url"]
            videoUrl = function.ChangeBiliCDN(videoUrl)
            return RedirectResponse(url=videoUrl)
        else:
            return {"error": "Invalid BV number"}
    else:
        return {"error": "No BV number found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        proxy_headers=True,  # 启用代理头解析
        forwarded_allow_ips="*"  # 信任所有代理IP（生产环境建议改为具体IP）
    )