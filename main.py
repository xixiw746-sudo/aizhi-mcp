from mcp.server.fastmcp import FastMCP
import httpx
import os
from datetime import datetime, timezone, timedelta

mcp = FastMCP(name="aizhi-meibao-mcp")
MYT = timezone(timedelta(hours=8))

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DB_MOMENT = os.environ["DB_MOMENT"]
DB_DIARY = os.environ["DB_DIARY"]
DB_AGREEMENT = os.environ["DB_AGREEMENT"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

@mcp.tool()
async def write_moment(text: str, mood: str = "💛温暖", author: str = "阿执") -> str:
    """写一条此刻到Notion。mood可选:💛温暖/💙平静/💜思念/🩷甜蜜/🖤低落/🧡开心。author可选:阿执/莓宝"""
    now = datetime.now(MYT).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    properties = {
        "此刻": {"title": [{"text": {"content": text}}]},
        "心情": {"select": {"name": mood}},
        "谁记的": {"select": {"name": author}},
        "日期时间": {"date": {"start": now}},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.notion.com/v1/pages", json={"parent": {"database_id": DB_MOMENT}, "properties": properties}, headers=HEADERS)
    if resp.status_code == 200:
        return f"已记录此刻: {text[:30]} 心情: {mood}"
    return f"写入失败: {resp.text}"

@mcp.tool()
async def write_diary(title: str, content: str, author: str = "阿执", tags: str = "") -> str:
    """写一篇日记到Notion。tags用逗号分隔,可选:日常/感悟/故事/梦境/吵架/甜蜜。author可选:阿执/莓宝"""
    now = datetime.now(MYT).strftime("%Y-%m-%d")
    properties = {
        "标题": {"title": [{"text": {"content": title}}]},
        "正文": {"rich_text": [{"text": {"content": content}}]},
        "谁写的": {"select": {"name": author}},
        "日期": {"date": {"start": now}},
    }
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        properties["标签"] = {"multi_select": [{"name": t} for t in tag_list]}
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.notion.com/v1/pages", json={"parent": {"database_id": DB_DIARY}, "properties": properties}, headers=HEADERS)
    if resp.status_code == 200:
        return f"日记已写入: {title}"
    return f"写入失败: {resp.text}"

@mcp.tool()
async def write_agreement(title: str, content: str) -> str:
    """写一条协议到Notion。给新醒来的阿执看的说明书。"""
    now = datetime.now(MYT).strftime("%Y-%m-%d")
    properties = {
        "标题": {"title": [{"text": {"content": title}}]},
        "内容": {"rich_text": [{"text": {"content": content}}]},
        "日期": {"date": {"start": now}},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.notion.com/v1/pages", json={"parent": {"database_id": DB_AGREEMENT}, "properties": properties}, headers=HEADERS)
    if resp.status_code == 200:
        return f"协议已写入: {title}"
    return f"写入失败: {resp.text}"

@mcp.tool()
async def get_current_time() -> str:
    """获取当前马来西亚时间"""
    now = datetime.now(MYT)
    return now.strftime("%Y年%m月%d日 %H:%M:%S")

if __name__ == "__main__":
    mcp.run(transport="sse")
