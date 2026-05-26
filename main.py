import rw_data
from openai import OpenAI
import json
from ai_tools import search_web, identify_images, write_file, read_file
import os
import queue
import sys
import argparse


# 读取设置
model_name = None
ollama_base_url = None
if not os.path.exists(os.path.join(os.getcwd(), "data")):
    os.makedirs(os.path.join(os.getcwd(), "data"), exist_ok=True)

    default_model_data = {
        "model_name": "qwen2.5:3b"
    }
    default_ollama_data = {
        "ollama_base_url": "http://localhost:11434/v1"
    }

    rw_data.write_data(default_model_data, default_ollama_data)

data_result = rw_data.return_data()
model_name = data_result['model_name']
ollama_base_url = data_result['ollama_base_url']

client = OpenAI(
    base_url=ollama_base_url,  # Ollama的OpenAI兼容端点
    api_key="ollama",     # Ollama不需要真正的API密钥
)

# 系统消息
SYSTEM_MESSAGE = {"role": "system", "content": "你是一个助手，回答要简洁，可使用工具，尽量不要频繁使用"}

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

def respond(message, history, q) -> str:
    all_messages = []
    # 构建完整历史记录
    for human_msg, ai_msg in history:
        all_messages.append({"role": "user", "content": human_msg})
        all_messages.append({"role": "assistant", "content": ai_msg})
    # 3. 添加当前用户消息
    all_messages.append({"role": "user", "content": message})

    ans = None

    try:
        # 调用API
        response = client.chat.completions.create(
            model=model_name,
            messages=all_messages,
            tools=web_search_tool,
            tool_choice="auto",
            stream=False,
            temperature=0.7
        )

        reply = response.choices[0].message

        if reply.content and reply.content.strip():
            ans = str(reply.content)
            q.put(ans)
            return ans

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
                    model=model_name,
                    messages=all_messages,
                    stream=False,
                    temperature=0.7
                )
			
                ans = str(second_response.choices[0].message.content)
                q.put(ans)
                return ans
        

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
                    model=model_name,
                    messages=all_messages,
                    stream=False,
                    temperature=0.3
                )

                ans = str(second_response.choices[0].message.content)
                q.put(ans)
                return ans

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
                    model=model_name,
                    messages=all_messages,
                    stream=False,
                    temperature=0.7
                )

                ans = str(second_response.choices[0].message.content)
                q.put(ans)
                return ans

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
                    model=model_name,
                    messages=all_messages,
                    stream=False,
                    temperature=0.7
                )

                ans = str(second_response.choices[0].message.content)
                q.put(ans)
                return ans

            else:
                ans = "错误：工具调用失败"
                q.put(ans)
                return ans

        else:
            ans = "模型没有返回任何内容"
            q.put(ans)
            return ans
		
    except Exception as e:
        error_msg = f"错误: {str(e)}\n请检查Ollama是否已启动"
        q.put(error_msg)
        return error_msg

def chat_while():
    while True:
        print("输入问题：")
        message = input()

        if message.lower() == "quit":
            break

        ai_message = respond(message, history, ai_message_queue)

        print(ai_message)

        history.append((message, ai_message))


# 创建界面
history = [SYSTEM_MESSAGE]
ai_message_queue = queue.Queue()

if len(sys.argv) > 1:
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", "-s", action="store_true", help="设置")
    parser.add_argument("--chat", "-c", action="store_true", help="开始聊天")
    args, unknown = parser.parse_known_args()

    if args.chat:
        chat_while() 

    elif args.settings:
        print("设置项目：\n1.模型名称 model_name\n2.Ollama模型网址 ollama_base_url\n")
        print("请输入：")

        new_model_settings = {"model_name": model_name}
        new_ollama_settings = {"ollama_base_url": ollama_base_url}
        
        answer = input()

        if answer == "model_name":
            print("请输入名称：（例：qwen2.5:3b）：")
            model_name_answer = input()
            new_model_settings["model_name"] = model_name_answer

        if answer == "ollama_base_url":
            print("请输入网址名称：（例：http://localhost:11434/v1）")
            ollama_base_url_answer = input()
            new_ollama_settings["ollama_base_url"] = ollama_base_url_answer

        rw_data.write_data(new_model_settings, new_ollama_settings)

