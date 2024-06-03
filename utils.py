from aqt import mw

def takoboto_link_word(word: str, id: int) -> str:
    # TODO: if intent not supported, fallback to browser (on windows: below link will not open in browser but ask to open in app)
    link = f'intent:#Intent;package=jp.takoboto;action=jp.takoboto.WORD;i.word={id};S.browser_fallback_url=http%3A%2F%2Ftakoboto.jp%2F%3Fw%3D{id};end'
    if (config.get("CSS_Class") and config.get("CSS_Class") != ""):
        return f'<a href="{link}" class="{config.get("CSS_Class")}">{word}</a>'
    else:
        return f'<a href="{link}">{word}</a>'


def log(msg: str):
    print("[Takoboto Addon]", msg)


config = mw.addonManager.getConfig(__name__)
log("Config loaded: %s" % config)