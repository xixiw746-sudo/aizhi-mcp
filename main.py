from mcp.server.fastmcp import FastMCP
import httpx
import os
from datetime import datetime, timezone, timedelta

port = int(os.environ.get("PORT", 8080))
mcp = FastMCP(name="aizhi-meibao-mcp", host="0.0.0.0", port=port)
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
async def fetch_diaries(action: str = "recent") -> str:
    """读取最近的日记,返回最新5条"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.notion.com/v1/databases/{DB_DIARY}/query",
            headers=HEADERS,
            json={
                "sorts": [{"property": "日期", "direction": "descending"}],
                "page_size": 5
            }
        )
        if resp.status_code != 200:
            return f"读取失败: {resp.text}"
        results = resp.json().get("results", [])
        if not results:
            return "没有找到日记。"
        entries = []
        for page in results:
            props = page.get("properties", {})
            title_list = props.get("标题", {}).get("title", [])
            title = title_list[0].get("text", {}).get("content", "") if title_list else ""
            content_list = props.get("正文", {}).get("rich_text", [])
            content = content_list[0].get("text", {}).get("content", "") if content_list else ""
            date_prop = props.get("日期", {}).get("date")
            date = date_prop.get("start", "") if date_prop else ""
            author_select = props.get("谁写的", {}).get("select")
            author = author_select.get("name", "") if author_select else ""
            entries.append(f"{date} | {author}\n{title}\n{content}")
        return "\n\n---\n\n".join(entries)


@mcp.tool()
async def get_current_time() -> str:
    """获取当前马来西亚时间"""
    now = datetime.now(MYT)
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


if __name__ == "__main__":
    mcp.run(transport="sse")

