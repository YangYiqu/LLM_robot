import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pprint import pprint
import requests
import re
import os
from skills_python import robot_info

"""
The function delete_skill is designed to sequentially invoke four separate functions for deleting various files associated with a given skill.

1.delete_python(func_name) calls for the deletion of Python files in the skills_python folder related to the skill.
2.delete_txt(func_name) deletes text files in the skills_desc folder connected to the skill.
3.delete_init(func_name) eliminates the __init__.py file in the skills_python folder pertaining to the skill, which often signifies a Python package directory.
4.delete_embedding(func_name) removes the text in embedding files in the langchain folder that related to the skill.

By invoking this function, it enables a one-step cleanup of all relevant files for a particular skill, thus providing a quick deletion functionality."""


def delete_python(func_name):
    folder_name = "skills_python"
    file_name = "{func_name}.py".format(func_name=func_name)
    file_path = os.path.join(folder_name, file_name)

    # 检查文件是否存在，然后进行删除操作
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"The file {file_name} has been successfully deleted.")
    else:
        print(f"The file {file_name} does not exist.")


def delete_txt(func_name):
    folder_name = "skills_desc"
    file_name = "{func_name}.txt".format(func_name=func_name)
    file_path = os.path.join(folder_name, file_name)

    # 检查文件是否存在，然后进行删除操作
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"The file {file_name} has been successfully deleted.")
    else:
        print(f"The file {file_name} does not exist.")


def delete_init(func_name):
    folder_name = "skills_python"
    file_path = os.path.join(folder_name, "__init__.py")

    # 读取文件内容，并删除包含特定字符串的行
    with open(file_path, "r") as file:
        lines = file.readlines()

    with open(file_path, "w") as file:
        for line in lines:
            if func_name.strip() != line.strip():
                file.write(line)

    print(
        f"The lines containing '{func_name}' have been successfully deleted from __init__.py."
    )


def delete_embedding(func_name):
    keywords_path = robot_info.Langchain_chatchat_embedding_Path
    with open(keywords_path, "r") as file:
        lines = file.readlines()

    found_func_name = False
    new_lines = []
    for line in lines:

        if line.strip() == func_name:
            found_func_name = True
        elif line == "":
            pass
        else:
            new_lines.append(line)

    # 如果找到了 func_name，则写回文件
    if found_func_name:
        with open(keywords_path, "w") as file:
            file.writelines(new_lines)
        print(f"Line with {func_name} found and deleted in embedding txt.")
    else:
        print(f"No line with {func_name} found in the file in embedding txt.")


def list_database_files():
    url = robot_info.Langchain_chatchat_API + "knowledge_base/list_files"
    print("\n获取知识库中文件列表：")
    r = requests.get(url, params={"knowledge_base_name": "skill_library"})
    data = r.json()
    files_list = data.get("data")
    pprint(data)
    return files_list


def delete_database_files(func_name):
    files_list = list_database_files()
    url = robot_info.Langchain_chatchat_API + "knowledge_base/delete_docs"
    print(f"\n删除知识文件")
    file_name = "{func_name}.txt".format(func_name=func_name)
    if file_name in files_list:
        print(f"{file_name} is in the database and now deleting...Success!")
        r = requests.post(
            url,
            json={"knowledge_base_name": "skill_library", "file_names": [file_name]},
        )
        data = r.json()
        pprint(data)
    else:
        print(f"{file_name} is not in the database.")


def delete_skill(func_name):
    delete_python(func_name)
    delete_txt(func_name)
    delete_init(func_name)
    delete_embedding(func_name)
    delete_database_files(func_name)
