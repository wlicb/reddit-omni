import praw
import json
from dotenv import dotenv_values

def reddit_commenter(comment, post_id, reply_id=None):
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


    try:
        bot_id = reddit.user.me().id
        if reply_id:
            # Reply to an existing comment
            parent = reddit.comment(id=reply_id)
        else:
            # Reply to the main post
            parent = reddit.submission(id=post_id)

        replied = parent.reply(comment)
        reply_id = replied.id

        try:
            with open("reddit_comments.json", "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}

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

        # Insert into the JSON structure
        if reply_id:
            # reply to a specific reply
            if post_id in data and "comments" in data[post_id]:
                inserted = insert_reply(data[post_id]["comments"], reply_id, new_comment_data)
                if not inserted:
                    print("Parent comment not found in JSON, adding it at the root level.")
                    data[post_id]["comments"][reply_id] = new_comment_data
        else:
            # reply to the whole question
            if post_id in data:
                data[post_id]["comments"][reply_id] = new_comment_data
            else:
                data[post_id] = {
                    "title": parent.title,
                    "body": parent.selftext,
                    "comments": {reply_id: new_comment_data}
                }

        with open("reddit_comments.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        print(f"Successfully commented: {replied.permalink} and updated JSON")
        return True

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False