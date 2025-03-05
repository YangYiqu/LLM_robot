import sys,os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role
from _basic_info import QUERY_REWRITE_PROMPT

def query_rewrite(query):
    query_rewrite_prompt=QUERY_REWRITE_PROMPT.format(query=query)
    messages = [
        {
            "role": Role.SYSTEM,
            "content": "You are a helpful assistant that writes python code.",
        },
        {"role": Role.USER, "content": query_rewrite_prompt},
    ]
    response = Generation.call(
            # Generation.Models.qwen_max,
            model="qwen-max-1201",
            messages=messages,
            result_format="message",  # set the result to be "message" format.
            temperature=0,
        )
    return (response.output.choices[0]["message"]["content"])
    