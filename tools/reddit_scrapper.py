from dotenv import dotenv_values
import praw
import json


def get_comment_tree(comment, bot_id):
    comment_data = {
        "author": comment.author.id if comment.author else "[deleted]",
        "body": comment.body,
        "bot": (comment.author.id == bot_id),
        "replies": {reply.id: get_comment_tree(reply, bot_id) for reply in comment.replies}
    }
    return comment_data


def reddit_scrapper(subreddit_name, num_posts=None):
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



    try:
        bot_id = reddit.user.me().id
        # Get the subreddit
        subreddit = reddit.subreddit(subreddit_name)
        top_posts = subreddit.top(limit=num_posts, time_filter="day")

        result = {}
        for post in top_posts:
            if not post.stickied:
                post.comments.replace_more(limit=0)
                result[post.id] = {
                    "title": post.title,
                    "body": post.selftext if post.selftext else 'Empty.',
                    "author": post.author.id if post.author else "[deleted]",
                    "bot": (post.author.id == bot_id),
                    "comments": {comment.id: get_comment_tree(comment, bot_id) for comment in post.comments}
                }
        
        
        json_output = json.dumps(result, indent=4)
        with open("reddit_comments.json", "w", encoding="utf-8") as file:
            file.write(json_output)


        return result

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}
