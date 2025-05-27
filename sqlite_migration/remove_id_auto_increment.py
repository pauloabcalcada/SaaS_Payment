import pandas as pd

# List of CSV files to process
csv_files = ["Clientes.csv", "Configuracoes.csv", "Pagamentos.csv"]

# Process each CSV file
for csv_file in csv_files:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Remove the first column
    df = df.iloc[:, 1:]

    # Save the updated DataFrame back to the same file
    df.to_csv(csv_file, index=False)
    print(f"Removed the first column from {csv_file} and saved the updated file.")