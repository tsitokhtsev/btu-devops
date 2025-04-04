import argparse


def is_armstrong(num):
    power = len(str(num))
    sum = 0

    for digit in str(num):
        sum += int(digit) ** power

    return num == sum


def recursive_sum(numbers):
    if len(numbers) == 1:
        return numbers[0]

    return numbers[0] + recursive_sum(numbers[1:])


def main():
    parser = argparse.ArgumentParser(
        description="Find Armstrong numbers in a given range."
    )
    parser.add_argument(
        "--start", type=int, default=9, help="Start of range (default: 9)"
    )
    parser.add_argument(
        "--end", type=int, default=9999, help="End of range (default: 9999)"
    )
    args = parser.parse_args()

    start = max(1, args.start)
    end = args.end

    if start > end:
        print("Error: Start value must be less than end value")
        return

    numbers = []

    for i in range(start, end):
        if is_armstrong(i):
            numbers.append(i)

    print("Armstrong numbers in range:", numbers)
    if numbers:
        total = recursive_sum(numbers)
        print(f"Sum of Armstrong numbers: {total}")
    else:
        print("No Armstrong numbers found in the given range.")


if __name__ == "__main__":
    main()
