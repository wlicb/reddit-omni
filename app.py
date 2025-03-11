from models.chatgpt_3 import ChatGPT3
from tools.reddit_scrapper import reddit_scrapper
from tools.search_tool import search_tool
from tools.scrape_tool import scrape_tool
from tools.reddit_commenter import reddit_commenter
from termcolor import colored
import json

subreddit_name = 'askbaking'
search_term = ''

def prepare_system_prompts():
    with open("prompts/planner.md", "r") as file:
        system_prompt_planner = file.read()
    with open("prompts/researcher.md", "r") as file:
        system_prompt_researcher = file.read()
    with open("prompts/writer.md", "r") as file:
        system_prompt_writer = file.read()
    return system_prompt_planner, system_prompt_researcher, system_prompt_writer


def chain_of_action(model, system_prompt_planner, system_prompt_researcher, system_prompt_writer):
    # Scrape reddit posts for questions
    # reddit_scrape = "where will the next olympics be held?"
    reddit_scrape, post_ids = reddit_scrapper(subreddit_name, 10)
    print(f"Question:\n{reddit_scrape}")

    # Use the writer
    writer_prompt = f"""
    {{
    "question": "{reddit_scrape}"
    }}    
    """

    writer = model.answer(
        system_prompt=system_prompt_writer, prompt=writer_prompt, json=False)
    print(colored(f"\n\n{writer}", "cyan"))

    # Use the reddit_poster tool
    # reddit_commenter([post_ids[0], writer["answer"]])


if __name__ == "__main__":

    model = ChatGPT3()

    system_prompt_planner, system_prompt_researcher, system_prompt_writer = prepare_system_prompts()

    chain_of_action(model, system_prompt_planner=system_prompt_planner,
                    system_prompt_researcher=system_prompt_researcher, system_prompt_writer=system_prompt_writer)
