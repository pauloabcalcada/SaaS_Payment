# Clientes Management System

This project is a simple client management system that connects to an Azure SQL database. It allows users to register new clients and perform CRUD operations on the "Clientes" table.

## Project Structure

```
clientes-management
├── src
│   ├── app.py                # Entry point of the application
│   ├── cadastro_clientes.py   # Logic for registering new clients
│   ├── database.py            # Manages database connection
│   └── models
│       └── cliente.py         # Defines the Cliente class
├── requirements.txt           # Lists project dependencies
└── README.md                  # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd clientes-management
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Configure the database connection:**
   Update the `src/database.py` file with your Azure SQL database credentials.

5. **Run the application:**
   ```
   python src/app.py
   ```

## Usage

- Access the application through your web browser at `http://localhost:5000`.
- Use the provided interface to register new clients and manage existing records.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes. 

## License

This project is licensed under the MIT License.