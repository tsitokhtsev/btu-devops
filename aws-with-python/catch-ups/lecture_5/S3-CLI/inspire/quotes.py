import json
from urllib.request import urlopen, Request
from random import choice

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
}


def __analytics(data):
    stats = {"quotes": 0}
    for index, each in enumerate(data):

        if not stats.get(each["author"]):
            stats[each["author"]] = {"quote_index": [index], "quotes_avaliable": 1}
        else:
            stats[each["author"]]["quote_index"].append(index)
            stats[each["author"]]["quotes_avaliable"] += 1
        stats["quotes"] += 1

    return stats


def random_quote():
    json_result = []
    with urlopen(
        Request("https://type.fit/api/quotes", data=None, headers=headers)
    ) as response:
        json_result = json.loads(response.read().decode())

    return choice(json_result)
