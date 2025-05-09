from collections import deque
from copy import deepcopy
from models.chatgpt_3 import ChatGPT3
from tools.reddit_scrapper import reddit_scrapper
from tools.search_tool import search_tool
from tools.scrape_tool import scrape_tool
from tools.reddit_commenter import reddit_commenter
import json
import time
import os

import re


subreddit_name = 'science'
search_term = ''

log_file="answered_questions.json"

model = ChatGPT3()

# questions_to_answer = 5

def extract_json_from_response(response_text: str):
    try:
        if "```" in response_text:
            response_text = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL).group(1)
        return json.loads(response_text)
    except Exception as e:
        print(f"[!] Failed to extract JSON: {e}")
        return None


def prepare_system_prompts():
    with open("prompts/select_thread.md", "r") as f:
        system_prompt_select_thread = f.read()
    with open("prompts/select_reply_target.md", "r") as f:
        system_prompt_select_reply_target = f.read()
    with open("prompts/generate_reply_to_comment.md", "r") as f:
        system_prompt_generate_reply_to_comment = f.read()
    with open("prompts/generate_reply_to_thread.md", "r") as f:
        system_prompt_generate_reply_to_thread = f.read()
    with open("prompts/filter_comment.md", "r") as f:
        system_prompt_filter_comment = f.read()
    with open("prompts/filter_argument.md", "r") as f:
        system_prompt_filter_argument = f.read()
    with open("prompts/generate_reply_to_argument.md", "r") as f:
        system_prompt_ggenerate_reply_to_argument = f.read()

    return {
        "select_thread": system_prompt_select_thread,
        "select_reply_target": system_prompt_select_reply_target,
        "generate_reply_to_comment": system_prompt_generate_reply_to_comment,
        "generate_reply_to_thread": system_prompt_generate_reply_to_thread,
        "filter_comment": system_prompt_filter_comment,
        "filter_argument": system_prompt_filter_argument,
        "generate_reply_to_argument": system_prompt_ggenerate_reply_to_argument
    }

def select_thread(reddit_data, system_prompt):
    prompt = json.dumps({
        "threads": [
            {
                "id": tid,
                "title": thread["title"],
                "body": thread["body"]
            }
            for tid, thread in reddit_data.items()
        ],
    }, indent=4)
    # print(prompt)

    response = model.answer(
        system_prompt=system_prompt, prompt=prompt)
        
    if response == None:
        return None
    # print(response)

    parsed_response = extract_json_from_response(response)

    return parsed_response["selected_thread_id"]

def select_reply_target(reddit_data, selected_thread_id, system_prompt):
    selected_thread = reddit_data[selected_thread_id]
    
    prompt = json.dumps({
        "post": {
            "title": selected_thread["title"],
            "body": selected_thread["body"],
            "id": selected_thread_id
        },
        "comments": [
            {
                "id": cid,
                "body": c["body"],
                "bot": c["bot"]
            }
            for cid, c in selected_thread["comments"].items()
        ],
    }, indent=4)

    # print(prompt)

    response = model.answer(
        system_prompt=system_prompt, prompt=prompt)
    
    # print(response)
    if response == None:
        return None

    parsed_response = extract_json_from_response(response)

    return parsed_response["reply_target_id"]

def remove_author_recursively(comment):
    if "author" in comment:
        del comment["author"]
    if "replies" in comment:
        for reply in comment["replies"].values():
            remove_author_recursively(reply)


def reply_to_comment(reddit_data, selected_thread_id, selected_comment_id, system_prompt):
    selected_thread = reddit_data[selected_thread_id]
    selected_comment = selected_thread["comments"][selected_comment_id]
    remove_author_recursively(selected_comment)
    
    prompt = json.dumps({
        "post": {
            "title": selected_thread["title"],
            "body": selected_thread["body"],
        },
        "comments": {
            selected_comment_id: selected_comment
        }
        ,
    }, indent=4)


    # print(prompt)

    response = model.answer(
        system_prompt=system_prompt, prompt=prompt)
    
    # print(response)
    if response == None:
        return None, None

    parsed_response = extract_json_from_response(response)

    return parsed_response["reply_id"], parsed_response["comment"]

# def reply_to_thread(reddit_data, selected_thread_id, system_prompt):
#     selected_thread = reddit_data[selected_thread_id]
    
#     prompt = json.dumps({
#         "post": {
#             "title": selected_thread["title"],
#             "body": selected_thread["body"],
#         },
#     }, indent=4)

#     # print(prompt)

#     response = model.answer(
#         system_prompt=system_prompt, prompt=prompt)
    
#     # print(response)

#     return response


def filter_comment(reddit_data, selected_thread_id, filter_argument_system_prompt, filter_comment_system_prompt):
    def traverse_with_parents(node_dict, parent_path):
        def format_subtree(tree):
            """Convert tree to GPT-friendly format"""
            return [
                {
                    "id": cid,
                    "body": cdata["body"],
                    "replies": format_subtree(cdata.get("replies", {}))
                } for cid, cdata in tree.items()
            ]

        def mark_unsupported(tree, target_id):
            """Recursively find and mark the target node"""
            for cid, cdata in tree.items():
                if cid == target_id:
                    cdata["unsupported"] = True
                    return True
                if mark_unsupported(cdata.get("replies", {}), target_id):
                    return True
            return False

        def extract_branch_path(tree, path_ids):
            """Extracts full ancestry path + subtree from root to target node"""
            current_level = tree
            result = {}
            cursor = result

            for cid in path_ids:
                if cid not in current_level:
                    break
                cursor[cid] = deepcopy(current_level[cid])
                cursor = cursor[cid].setdefault("replies", {})
                current_level = current_level[cid].get("replies", {})

            return result

        queue = deque()
        for cid, cnode in node_dict.items():
            queue.append((cid, cnode, parent_path + [(cid, cnode)]))

        while queue:
            cid, cnode, ancestry = queue.popleft()
            if "Moderator" in cnode.get("author", ""):
                continue

            argument_response = model.answer(filter_argument_system_prompt, prompt = cnode.get("body"))
            if argument_response == None:
                return None, None, ""
            parsed_argument_response = extract_json_from_response(argument_response)
            print(cnode.get("body"))
            print(argument_response)
            if not parsed_argument_response.get("is_argument"):
                continue


            # Format subtree for GPT
            gpt_input = {
                "id": cid,
                "body": cnode.get("body"),
                "replies": format_subtree(cnode.get("replies", {}))
            }

            prompt = json.dumps(gpt_input, indent=2)
            response = model.answer(filter_comment_system_prompt, prompt)
            if response == None:
                return None, None, ""
            # print(response)
            parsed_response = extract_json_from_response(response)

            if parsed_response.get("unsupported"):
                tree_copy = deepcopy(node_dict)
                mark_unsupported(tree_copy, cid)
                path_ids = [pid for pid, _ in ancestry]
                return cid, extract_branch_path(tree_copy, path_ids), parsed_response["reason"]

            for child_cid, child_node in cnode.get("replies", {}).items():
                queue.append((child_cid, child_node, ancestry + [(child_cid, child_node)]))

        return None, None, ""

    # Process all top-level comments
    selected_thread = reddit_data.get(selected_thread_id, {})
    # print(json.dumps(selected_thread, indent=2))
    top_comments = selected_thread["comments"]
    reply_id, tree, reasoning = traverse_with_parents(
        top_comments, []
    )
    result = {
        "post": {
            "title": selected_thread["title"],
            "body": selected_thread["body"],
        },
        "comments": tree
    }
    # print(json.dumps(result, indent=2))
    return reply_id, result, reasoning


def reply_to_argument(thread, reason, system_prompt):
    
    prompt = json.dumps({
        "thread": thread,
        "reason": reason
    }, indent=4)

    # print(prompt)

    response = model.answer(
        system_prompt=system_prompt, prompt=prompt)
    
    if response == None:
        return None
    
    # print(response)

    return response