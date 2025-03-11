from models.chatgpt_3 import ChatGPT3
from tools.reddit_scrapper import reddit_scrapper
from tools.search_tool import search_tool
from tools.scrape_tool import scrape_tool
from tools.reddit_commenter import reddit_commenter
import json
import time
import os

subreddit_name = 'Python'
search_term = ''

log_file="answered_questions.json"

questions_to_answer = 5

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

        # Load existing log file if available
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                try:
                    answered_questions = json.load(f)
                except json.JSONDecodeError:
                    answered_questions = {}
        else:
            answered_questions = {}


        if post_id in answered_questions:
            print(f"Question answered.")
            continue

        if "title" not in question:
            print("Malformed question.")
            continue


        # Use the writer
        writer_prompt = f"""
        {{
            "question_title": "{question["title"]}",
            "question_body": "{question["body"]}"
        }}
        """

        writer = model.answer(
            system_prompt=system_prompt_writer, prompt=writer_prompt, json=False)
        print("Answer:", writer)

        # Use the reddit_poster tool
        reddit_commenter(post_id, writer)

        # Log the answered question
        answered_questions[post_id] = {
            "title": question["title"],
            "body": question["body"],
            "url": question_url,
            "answer": writer
        }
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(answered_questions, f, indent=2, ensure_ascii=False)

        answered_count += 1

        if answered_count >= questions_to_answer:
            break

        time.sleep(10)

if __name__ == "__main__":

    model = ChatGPT3()

    system_prompt_writer = prepare_system_prompts()

    chain_of_action(model, system_prompt_writer=system_prompt_writer)
