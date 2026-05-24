from easyocr import Reader
from ddgs import DDGS

def identify_images(file_path: str) -> str:
    ans = ""

    reader = Reader(['ch_sim', 'en'])
    try:
        result = reader.readtext(file_path)
    except:
        return "识别出错"

    for i, dectection in enumerate(result,1):
        text = dectection[1]

        ans += f"识别结果：{text}"

    if ans == "":
        return "未识别到内容"

    return ans

def write_file(file_path: str, write_content: str, write_mode: str) -> str:
    try:
        with open(file_path, mode=write_mode, encoding="utf-8") as f:
            f.write(write_content)

        return "写入操作成功"

    except:
        return "写入操作失败"

def read_file(file_path: str) -> str:
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            return f.read()
    except:
        return "获取失败"

    return "获取失败"

def search_web(query: str, max_results: int = 5) -> str:
    """
    极简网络搜索（基于 DuckDuckGo，免费无限制）
    """
    try:
        with DDGS() as ddgs:
            # 获取搜索结果
            results = list(ddgs.text(query, max_results=max_results))
            
        if not results:
            return f"未找到关于 '{query}' 的搜索结果"
        
        # 格式化结果
        result_str = f"搜索关键词: {query}\n找到结果: {len(results)} 条\n\n"
        for i, r in enumerate(results, 1):
            result_str += f"{i}. 【{r.get('title', '无标题')}】\n"
            result_str += f"   链接: {r.get('href', 'N/A')}\n"
            result_str += f"   摘要: {r.get('body', '无摘要')[:100]}...\n\n"
        
        return result_str
        
    except Exception as e:
        return f"网络搜索失败: {str(e)}"



