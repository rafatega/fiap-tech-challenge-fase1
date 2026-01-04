import pandas as pd


def main():
    # Create a sample DataFrame
    data = {
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['New York', 'Los Angeles', 'Chicago']
    }
    df = pd.DataFrame(data)

    # Display the DataFrame
    print("Sample DataFrame:")
    print(df)


if __name__ == "__main__":
    main()
