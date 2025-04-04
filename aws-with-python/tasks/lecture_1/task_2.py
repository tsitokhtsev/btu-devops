import argparse
import re


def main():
    parser = argparse.ArgumentParser(description="Split a string into numbers")
    parser.add_argument("string", type=str, help="String to split")
    args = parser.parse_args()

    string = args.string
    floatList = []
    oddList = []
    evenList = []

    float_pattern = re.findall(r"\d+\.\d+", string)

    for num in float_pattern:
        floatList.append(float(num))
        string = string.replace(num, "")

    int_pattern = re.findall(r"\d+", string)

    for num in int_pattern:
        if int(num) % 2 == 0:
            evenList.append(int(num))
        else:
            oddList.append(int(num))

    print("Floats:", floatList)
    print("Odds:", oddList)
    print("Evens:", evenList)


if __name__ == "__main__":
    main()
