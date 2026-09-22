import pandas as pd
import matplotlib.pyplot as plt


def load_data(filepath="creditcard.csv"):
    try:
        data = pd.read_csv(filepath)
        return data
    except FileNotFoundError as e:
        print(f"Error: File not found. {e}. Please ensure '{filepath}' exists in the current directory.")
        return None
    except pd.errors.EmptyDataError as e:
        print(f"Error: The file is empty or not readable. {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while loading data: {e}")
        return None


def display_summary_statistics(data):
    try:
        print("\n--- Summary Statistics ---")
        for column in data.columns:
            mean_val = data[column].mean()
            # Catch errors in case of non-numeric comparisons or similar
            try:
                std_val = data[column].std()
            except TypeError:
                std_val = "N/A"
                
            cardinality = data[column].nunique()
            print(f"Column: {column}")
            print(f"  Mean: {mean_val}")
            print(f"  Std Dev: {std_val}")
            print(f"  Cardinality: {cardinality}")
            print("-" * 20)
    except Exception as e:
        print(f"Error computing statistics: {e}")


def plot_correlation_heatmap(data):
    try:
        # Select numerical columns
        numeric_data = data.select_dtypes(include=["number"])
        
        if numeric_data.empty:
            print("No numerical columns found to generate a heatmap.")
            return
        
        # Compute correlation
        corr = numeric_data.corr()
        
        import seaborn as sns
        ax = plt.figure(figsize=(10, 8))
        sns.heatmap(corr, annot=False, cmap="coolwarm", square=True)
        plt.title("Correlation Heatmap of Numerical Columns")
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error generating correlation heatmap: {e}")


def plot_class_distribution(data):
    try:
        if "Class" not in data.columns:
            print("Error: 'Class' column not found in the dataset.")
            return
            
        class_counts = data["Class"].value_counts()
        
        plt.figure(figsize=(8, 6))
        plt.bar(range(len(class_counts)), class_counts.values, color=['green', 'red'])
        plt.xticks(range(len(class_counts)), class_counts.index)
        plt.ylabel("Frequency")
        plt.title("Transaction Class Distribution")
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error plotting class distribution: {e}")


def main():
    try:
        data = load_data()
        if data is not None:
            display_summary_statistics(data)
            plot_correlation_heatmap(data)
            plot_class_distribution(data)
    except Exception as e:
        print(f"Critical error during data analysis: {e}")


if __name__ == "__main__":
    main()
