from james_web_tool.telegram_bot import set_webhook_from_env


if __name__ == "__main__":
    result = set_webhook_from_env()
    print(result)
