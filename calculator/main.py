import operations


def main():
    a, b = 10, 4
    print(f"{a} + {b} = {operations.add(a, b)}")
    print(f"{a} - {b} = {operations.subtract(a, b)}")


if __name__ == "__main__":
    main()
