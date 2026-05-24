import gradio as gr
import webview
import time
import threading
from openai import OpenAI
import json
from ai_tools import search_web, identify_images, write_file, read_file

# 配置Ollama
ollama_base_url='http://localhost:11434/v1'

client = OpenAI(
    base_url=ollama_base_url,  # Ollama的OpenAI兼容端点
    api_key="ollama",     # Ollama不需要真正的API密钥
)

# 系统消息
SYSTEM_MESSAGE = {"role": "system", "content": "你是一个助手，回答要简洁，可使用工具"}

web_search_tool = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "当需要查询实时新闻、最新事件、天气、股价或未知事实时使用",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "搜索关键词"
                },
                "max_results": {
                    "type": "integer", 
                    "description": "返回结果数",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "当需要查询电脑文件时使用",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "搜索文件路径内容"
                }
            },
            "required": ["file_path"]
        }
    }
},

{
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "当需要写入（创建）电脑文件内容时使用",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要写入的文件路径"
                },
                "write_content": {
                    "type": "string",
                    "description": "要写入的内容"
                },
                "write_mode": {
                    "type": "string",
                    "description": "要写入的模式：w或者a"
                }
            },
            "required": ["file_path", "write_content", "write_mode"]
        }
    }
},

{
    "type": "function",
    "function": {
        "name": "identify_images",
        "description": "当需要识别图片文字时使用",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要识别的图片文件路径"
                },
            },
            "required": ["file_path"]
        }
    }
},

]

def respond(message, history):
    """
    Gradio响应函数
    """
    # 构建完整的消息列表
    all_messages = [SYSTEM_MESSAGE]  # 1. 先添加系统消息
	
    # 2. 添加历史记录
    for human_msg, ai_msg in history:
        all_messages.append({"role": "user", "content": human_msg})
        all_messages.append({"role": "assistant", "content": ai_msg})
    # 3. 添加当前用户消息
    all_messages.append({"role": "user", "content": message})

    try:
        # 调用API
        response = client.chat.completions.create(
            model="qwen2.5:3b",
            messages=all_messages,
            tools=web_search_tool,
            tool_choice="auto",
            stream=False,
            temperature=0.7
        )

        reply = response.choices[0].message

        if reply.content and reply.content.strip():
            yield str(reply.content)
            return

        if hasattr(reply, 'tool_calls') and reply.tool_calls:
            tool_call = reply.tool_calls[0]

            if tool_call.function.name == "web_search":
                # 解析参数
                args = json.loads(tool_call.function.arguments)
                query = args.get("query", message)
                
                # 执行搜索
                search_result = search_web(query, args.get("max_results", 5))
                 
                # 更新消息并获取最终回复
                all_messages.extend([
                    reply,
                    {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": search_result
                }
                ])
			
                second_response = client.chat.completions.create(
                    model="qwen2.5:3b",
                    messages=all_messages,
                    stream=False,
                    temperature=0.7
                )
			
                yield str(second_response.choices[0].message.content)
            
            elif tool_call.function.name == "read_file":
                args = json.loads(tool_call.function.arguments)
                file_path = args.get("file_path", message)
                
                file_content = read_file(file_path)

                all_messages.extend([
                    reply,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": file_content
                    }
                ])

                second_response = client.chat.completions.create(
                    model="qwen2.5:3b",
                    messages=all_messages,
                    stream=False,
                    temperature=0.3
                )

                yield str(second_response.choices[0].message.content)
            
            elif tool_call.function.name == "write_file":
                args = json.loads(tool_call.function.arguments)
                file_path = args.get("file_path", "")
                write_content = args.get("write_content", "")
                write_mode = args.get("write_mode", "")

                write_ = write_file(file_path, write_content, write_mode)

                all_messages.extend([
                    reply,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": write_
                    }
                ])

                second_response = client.chat.completions.create(
                    model="qwen2.5:3b",
                    messages=all_messages,
                    stream=False,
                    temperature=0.7
                )

                yield str(second_response.choices[0].message.content)

            elif tool_call.function.name == "identify_images":
                args = json.loads(tool_call.function.arguments)
                file_path = args.get("file_path", "")
                
                result = identify_images(file_path)

                all_messages.extend([
                    reply,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    }
                ])

                second_response = client.chat.completions.create(
                    model="qwen2.5:3b",
                    messages=all_messages,
                    stream=False,
                    temperature=0.7
                )

                yield str(second_response.choices[0].message.content)

            else:
                yield "错误：工具调用失败"

        else:
            yield "模型没有返回任何内容"
		
    except Exception as e:
        error_msg = f"错误: {str(e)}\n请检查Ollama是否已启动"
        yield error_msg


# 创建界面
demo = gr.ChatInterface(
    respond,
    title="千问模型",
    description="与 qwen2.5:3b 模型对话"
)

def start_web():
    demo.launch(
        server_name="127.0.0.1",  # 本地地址
        server_port=7860,  # 端口
        show_error=True  # 显示错误
    )


# 启动界面
if __name__ == "__main__":
    t = threading.Thread(target=start_web)
    t.daemon = True
    t.start()
    time.sleep(2) 
    webview.create_window("AI 助手", "http://127.0.0.1:7860", width=800, height=600)
    webview.start()
