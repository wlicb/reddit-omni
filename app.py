from models.chatgpt_3 import ChatGPT3
from tools.reddit_scrapper import reddit_scrapper
from tools.search_tool import search_tool
from tools.scrape_tool import scrape_tool
from tools.reddit_commenter import reddit_commenter
import json
import time

subreddit_name = 'askbaking'
search_term = ''

def prepare_system_prompts():
    with open("prompts/writer.md", "r") as file:
        system_prompt_writer = file.read()
    return system_prompt_writer


def chain_of_action(model, system_prompt_writer):
    # Scrape reddit posts for questions
    # reddit_scrape = "where will the next olympics be held?"
    questions, post_ids = reddit_scrapper(subreddit_name, 2)

    for i in range(len(questions)):
        question = questions[i]
        post_id = post_ids[i]
        print(f"Question:\n{question}")
        print(f"Question URL: https://www.reddit.com/r/{subreddit_name}/comments/{post_id}/")


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
        print(reddit_commenter(post_id, writer))

        

        time.sleep(10)



if __name__ == "__main__":

    model = ChatGPT3()

    system_prompt_writer = prepare_system_prompts()

    chain_of_action(model, system_prompt_writer=system_prompt_writer)
