from models.chatgpt_3 import ChatGPT3
from tools.reddit_scrapper import reddit_scrapper
from tools.search_tool import search_tool
from tools.scrape_tool import scrape_tool
from tools.reddit_commenter import reddit_commenter
import json
import time
import os

subreddit_name = 'askbaking'
search_term = ''

log_file="answered_questions.json"

questions_to_answer = 1

def prepare_system_prompts():
    with open("prompts/writer.md", "r") as file:
        system_prompt_writer = file.read()
    return system_prompt_writer


def chain_of_action(model, system_prompt_writer):
    answered_count = 0
    # Scrape reddit posts for questions
    # reddit_scrape = "where will the next olympics be held?"
    questions = reddit_scrapper(subreddit_name)


    for post_id, question in questions.items():
        question_url = f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}/"
        print(f"Question URL: {question_url}")


        if "title" not in question:
            print("Malformed question.")
            continue


        # Use the writer
        writer_prompt = json.dumps(question)
        print(writer_prompt)

        writer = model.answer(
            system_prompt=system_prompt_writer, prompt=writer_prompt, json=False)

        parsed_response = json.loads(writer)

        reply_id = parsed_response.get("reply_id")
        comment_text = parsed_response.get("comment")
        print("reply id:", reply_id)
        print("comment:", comment_text)

        # # Use the reddit_poster tool
        # if reply_id == "":
            # reddit_commenter(comment_text, post_id)
        # else:
            # reddit_commenter(comment_text, post_id, reply_id)

        answered_count += 1

        if answered_count >= questions_to_answer:
            break

        time.sleep(10)

if __name__ == "__main__":

    model = ChatGPT3()

    system_prompt_writer = prepare_system_prompts()

    chain_of_action(model, system_prompt_writer=system_prompt_writer)
