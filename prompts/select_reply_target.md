# Reddit Bot - Select Reply Target

Decide whether the bot should reply to the original post or one of the comments. Choose the best location for a helpful response. Do **not** choose your own replies, that is, labeled as "bot: true" in the input json file.  

Return a JSON object in the following format:  
```json
{
    "reply_target_type": "'Thread' if reply to the thread directly, 'Comment' if reply to a comment",
    "reply_target_id": "Selected reply target ID. If reply to comments, use the comment ID. If reply to the thread directly, use the thread ID.",
    "reason": "Your reason here."
}
```

