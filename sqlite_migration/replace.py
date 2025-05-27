import pandas as pd

# Load the CSV file into a DataFrame
file_path = "Pagamentos.csv"
df = pd.read_csv(file_path)

# Replace "," with "." in the Valor_da_Conta column
df["Valor_da_Conta"] = df["Valor_da_Conta"].str.replace(",", ".", regex=False)

# Save the updated DataFrame back to the CSV file
df.to_csv(file_path, index=False)
print(f"Updated 'Valor_da_Conta' column in {file_path}.")