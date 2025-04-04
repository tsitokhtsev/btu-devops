data = []
words = ["moon", "sun"]


def is_int(data):
    try:
        int(data)
        return True
    except ValueError:
        return False


def find_in(data, words):
    count = 0

    for word in words:
        for d in data:
            if is_int(d):
                print(f"{d} is integer")
                continue

            if word in d:
                count += 1
                print(f"{word} is in the data")
                break
        else:
            print(f"{word} is not in the data")

    return count


data = ["moon is beautiful", "sun is shining", "earth is round"]
print(find_in(data, words), "\n")


data = ["beautiful", "sun is shining", 123]
print(find_in(data, words))
