from dotenv import dotenv_values
import praw
import json
import os
from pymongo import MongoClient, UpdateOne


mongo_uri = "mongodb://localhost:27017/"


def get_comment_tree(comment, bot_id):
    comment_data = {
        "author": comment.author.name if comment.author else "[deleted]",
        "body": comment.body,
        "bot": (comment.author.name == bot_id if comment.author else False),
        "replies": {reply.id: get_comment_tree(reply, bot_id) for reply in comment.replies}
    }
    return comment_data

def update_comments(existing_comments, new_comments):
    """
    Merges new comments into the existing comment tree.
    - Keeps all old comments.
    - Adds only new comments that don’t already exist.
    """
    for comment_id, new_comment in new_comments.items():
        if comment_id not in existing_comments:
            existing_comments[comment_id] = new_comment
        else:
            # Recursively update the replies
            update_comments(existing_comments[comment_id]["replies"], new_comment["replies"])


def reddit_scrapper(subreddit_name, num_posts=1):
    """
    Scrapes given subreddit's today's top posts for a number of posts.

    Parameters:
    input_list (list): A list containing the name of the subreddit and the number of tweets to scrape.
        - The first element is the name of the subreddit.
        - The second element is the number of posts to scrape.

        Example format: ["cats", "5"]

    Returns:
    (str): The formatted weather or an error message if something goes wrong.
    """
    CONFIG = dotenv_values("config/.env")

    # Initialize Reddit instance
    reddit = praw.Reddit(
        client_id=CONFIG["CLIENT_ID"],
        client_secret=CONFIG["CLIENT_SECRET"],
        user_agent="Scrapper",
        username=CONFIG["USERNAME"],
        password=CONFIG["PASSWORD"]
    )

    client = MongoClient(mongo_uri)
    db = client["reddit_db"]
    collection = db[subreddit_name]



    try:
        bot_id = reddit.user.me().name


        

        # Get the subreddit
        subreddit = reddit.subreddit(subreddit_name)
        top_posts = subreddit.top(limit=num_posts, time_filter="day")


        for post in top_posts:
            if not post.stickied and post.id:
                post.comments.replace_more(limit=0)

                new_comments = {comment.id: get_comment_tree(comment, bot_id) for comment in post.comments}
                


            post_doc = {
                "_id": post.id,
                "title": post.title,
                "body": post.selftext if post.selftext else 'Empty.',
                "author": post.author.name if post.author else "[deleted]",
                "bot": (post.author.name == bot_id if post.author else False),
                "url": f"https://www.reddit.com/r/{subreddit_name}/comments/{post.id}/",
                "comments": new_comments
            }

            collection.update_one(
                {"_id": post.id},
                {"$set": post_doc},
                upsert=True
            )
        
        data = {doc["_id"]: doc for doc in collection.find({})}

        return data

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}
