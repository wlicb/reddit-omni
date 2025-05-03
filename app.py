from models.chatgpt_3 import ChatGPT3
from tools.reddit_scrapper import reddit_scrapper
from tools.search_tool import search_tool
from tools.scrape_tool import scrape_tool
from tools.reddit_commenter import reddit_commenter
import json
import time
import os

subreddit_name = 'science'
search_term = ''

log_file="answered_questions.json"

questions_to_answer = 5

def prepare_system_prompts():
    with open("prompts/select_thread.md", "r") as f:
        system_prompt_select_thread = f.read()
    with open("prompts/select_reply_target.md", "r") as f:
        system_prompt_select_reply_target = f.read()
    with open("prompts/generate_reply_to_comment.md", "r") as f:
        system_prompt_generate_reply_to_comment = f.read()
    with open("prompts/generate_reply_to_thread.md", "r") as f:
        system_prompt_generate_reply_to_thread = f.read()

    return {
        "select_thread": system_prompt_select_thread,
        "select_reply_target": system_prompt_select_reply_target,
        "generate_reply_to_comment": system_prompt_generate_reply_to_comment,
        "generate_reply_to_thread": system_prompt_generate_reply_to_thread
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
        system_prompt=system_prompt, prompt=prompt, json=True)
    # print(response)

    parsed_response = json.loads(response)

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
        system_prompt=system_prompt, prompt=prompt, json=True)
    
    # print(response)

    parsed_response = json.loads(response)

    return parsed_response["reply_target_type"], parsed_response["reply_target_id"]

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
        system_prompt=system_prompt, prompt=prompt, json=True)
    
    # print(response)

    parsed_response = json.loads(response)

    return parsed_response["reply_id"], parsed_response["comment"]

def reply_to_thread(reddit_data, selected_thread_id, system_prompt):
    selected_thread = reddit_data[selected_thread_id]
    
    prompt = json.dumps({
        "post": {
            "title": selected_thread["title"],
            "body": selected_thread["body"],
        },
    }, indent=4)

    # print(prompt)

    response = model.answer(
        system_prompt=system_prompt, prompt=prompt, json=False)
    
    # print(response)

    return response

def chain_of_action(model, system_prompts):
    # Scrape reddit posts for questions
    # reddit_scrape = "where will the next olympics be held?"
    reddit_data = reddit_scrapper(subreddit_name, questions_to_answer)

    # thread_id = select_thread(reddit_data, system_prompts["select_thread"])
    thread_ids = [thread_id for thread_id in reddit_data.keys()]
    if len(thread_ids) > 6:
        thread_ids = thread_ids[:6]
    print("Need to answer:", len(thread_ids), "threads")
    # time.sleep(5)
    for thread_id in thread_ids:
        target_type, target_id = select_reply_target(reddit_data, thread_id, system_prompts["select_reply_target"])
        if target_type == "Comment":
            reply_id, comment_text = reply_to_comment(reddit_data, thread_id, target_id, system_prompts["generate_reply_to_comment"])
        else:
            comment_text = reply_to_thread(reddit_data, thread_id, system_prompts["generate_reply_to_comment"])

        # Use the reddit_poster tool
        if target_type == "Comment":
            reddit_commenter(comment_text, subreddit_name, thread_id, reply_id)
        else:
            reddit_commenter(comment_text, subreddit_name, thread_id)
        
        print("commented on thread: ", thread_id, "waiting for 630 seconds...")
        time.sleep(63*10)

if __name__ == "__main__":

    model = ChatGPT3()

    system_prompts = prepare_system_prompts()
    while True:
        chain_of_action(model, system_prompts)
        print("waiting for 600 seconds...")
        time.sleep(600)
        # time.sleep(5)