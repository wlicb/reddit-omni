import praw
import json
import os
from dotenv import dotenv_values
from pymongo import MongoClient, UpdateOne


mongo_uri = "mongodb://localhost:27017/"

def reddit_commenter(comment, subreddit_name, post_id, reply_id=None):
    """
    Comments on a given subreddit post or a specific comment.

    Parameters:
    - post_id (str): The ID of the post where the comment should be made.
    - comment (str): The text of the comment to post.
    - reply_id (str, optional): The ID of the comment to reply to. If not provided, it will reply to the post.

    Returns:
    - str: A success message or an error message if something goes wrong.
    """
    CONFIG = dotenv_values("config/.env")

    # Initialize Reddit instance
    reddit = praw.Reddit(
        client_id=CONFIG["CLIENT_ID"],
        client_secret=CONFIG["CLIENT_SECRET"],
        user_agent="Commenter",
        username=CONFIG["USERNAME"],
        password=CONFIG["PASSWORD"]
    )

    client = MongoClient(mongo_uri)
    db = client["reddit_db"]
    collection = db[subreddit_name]


    try:
        bot_id = reddit.user.me().id
        if reply_id:
            # Reply to an existing comment
            parent = reddit.comment(id=reply_id)
        else:
            # Reply to the main post
            parent = reddit.submission(id=post_id)

        replied = parent.reply(comment)
        # reply_id = replied.id


        # Function to insert the reply into the correct place in the tree
        def insert_reply(tree, target_id, new_comment):
            if target_id in tree:  # Found the parent comment
                tree[target_id]["replies"][reply_id] = new_comment
                return True
            for key, value in tree.items():
                if "replies" in value and insert_reply(value["replies"], target_id, new_comment):
                    return True
            return False

        new_comment_data = {
            "author": replied.author.id if replied.author else "[deleted]",
            "body": replied.body,
            "bot": (replied.author.id == bot_id),
            "replies": {}
        }

        post_doc = collection.find_one({"_id": post_id})

        # Insert into the JSON structure
        if reply_id:
            # reply to a specific reply (deep insert – requires fetching and modifying in Python)
            if post_doc and "comments" in post_doc:
                inserted = insert_reply(post_doc["comments"], reply_id, new_comment_data)
                if inserted:
                    collection.update_one(
                        {"_id": post_id},
                        {"$set": {"comments": post_doc["comments"]}}
                    )
                else:
                    print("Parent comment not found in MongoDB, adding it at the root level.")
                    collection.update_one(
                        {"_id": post_id},
                        {"$set": {f"comments.{reply_id}": new_comment_data}}
                    )
        else:
            # reply to the whole post (top-level comment)
            if post_doc:
                collection.update_one(
                    {"_id": post_id},
                    {"$set": {f"comments.{reply_id}": new_comment_data}}
                )
            else:
                # If post doesn't exist, insert it
                new_post_doc = {
                    "_id": post_id,
                    "title": parent.title,
                    "body": parent.selftext,
                    "comments": {reply_id: new_comment_data}
                }
                collection.insert_one(new_post_doc)


        print(f"Successfully commented: {replied.permalink} and updated DB")
        return True

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False