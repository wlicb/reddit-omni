from models.chatgpt_3 import ChatGPT3
from tools.reddit_scrapper import reddit_scrapper
from tools.search_tool import search_tool
from tools.scrape_tool import scrape_tool
from tools.reddit_commenter import reddit_commenter
import json
import time
import os
from actions import *
import random

# subreddit_name = 'science'
subreddit_name = 'EverythingScience'
search_term = ''

log_file="answered_questions.json"

#we set the number of questions to answer to 5 for now, because usually there will not be more than 5 posts in an hour
questions_to_answer = 5

def random_strategy(reddit_data, thread_id, system_prompts):
    target_id = select_reply_target(reddit_data, thread_id, system_prompts["select_reply_target"])
    reply_id, comment_text = reply_to_comment(reddit_data, thread_id, target_id, system_prompts["generate_reply_to_comment"])
    return reply_id, comment_text

def simple_strategy(reddit_data, thread_id, system_prompts):
    reply_id, subtree, reasoning = filter_comment(reddit_data, thread_id, system_prompts["filter_argument"], system_prompts["filter_comment"])
    if not reply_id or not subtree or not reasoning:
        print("Fall back to random strategy.")
        return random_strategy(reddit_data, thread_id, system_prompts)
    else:
        comment_text = reply_to_argument(subtree, reasoning, system_prompts["generate_reply_to_argument"])
    return reply_id, comment_text


def chain_of_action(system_prompts):
    # Scrape reddit posts for questions
    # reddit_scrape = "where will the next olympics be held?"
    reddit_data = reddit_scrapper(subreddit_name, questions_to_answer)

    # thread_id = select_thread(reddit_data, system_prompts["select_thread"])
    thread_ids = [thread_id for thread_id in reddit_data.keys()]
    #we only get the first 6 threads to answer, because the bot need 10 minutes interval to answer a question, or it will unsuccessfully post the comment
    if len(thread_ids) > 2:
        thread_ids = thread_ids[:2]
    print("Need to answer:", len(thread_ids), "threads")
    # time.sleep(5)
    random_questions = random.sample(thread_ids, len(thread_ids) // 2)
    for thread_id in thread_ids:
        # split the questions
        if thread_id in random_questions:
            print("Using random strategy to comment on thread", thread_id)
            reply_id, comment_text = random_strategy(reddit_data, thread_id, system_prompts)
            if not reply_id or not comment_text:
                print("No reply id or comment text provided.")
            print("commented on thread", thread_id, reply_id, ":", comment_text)
            # reddit_commenter(comment_text, subreddit_name, thread_id, "random", reply_id)
        else:
            print("Using simple strategy to comment on thread", thread_id)
            reply_id, comment_text = simple_strategy(reddit_data, thread_id, system_prompts)
            if not reply_id or not comment_text:
                print("No reply id or comment text provided.")
            print("commented on thread", thread_id, reply_id, ":", comment_text)
            # reddit_commenter(comment_text, subreddit_name, thread_id, "simple", reply_id)

        time.sleep(63*10)

if __name__ == "__main__":


    system_prompts = prepare_system_prompts()
    while True:
        chain_of_action(system_prompts)
        # print("waiting for 600 seconds...")
        time.sleep(3600 * 6)
        # time.sleep(5)