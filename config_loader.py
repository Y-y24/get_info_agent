import yaml


DEFAULTS = {
    "academic": {
        "arxiv_categories": ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "eess.SP"],
        "keywords": [],
    },
    "tech": {
        "sources": ["hackernews", "github_trending", "paperswithcode"],
    },
    "news": {
        "sources": ["weibo", "zhihu", "36kr"],
    },
    "email": {
        "smtp_host": "smtp.qq.com",
        "smtp_port": 587,
        "from_address": "",
        "to_address": "",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "max_tokens_per_item": 80,
    },
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    config = {}
    for section, defaults in DEFAULTS.items():
        section_data = defaults.copy()
        if section in user_config:
            section_data.update(user_config[section])
        config[section] = section_data

    return config
