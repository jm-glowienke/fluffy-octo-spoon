# Swiss Bank Transaction Classifier

A Python tool to automatically classify bank transactions from CSV files using keyword-based categorization.

## Features

- Processes Swiss bank transaction CSV files
- Supports custom category mapping via YAML configuration
- Maintains existing transaction IDs and categories when reprocessing
- Handles Swiss number format (1'234.56)
- Detailed logging for transaction processing
- Preserves CSV headers and metadata
- Type-hinted code base with mypy validation
- Follows PEP 8 style guidelines enforced by ruff

## Prerequisites

- Python 3.13+
- Poetry for dependency management

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/swiss-transaction-classifier.git
    cd swiss-transaction-classifier
    ```

2. Install dependencies using Poetry:
    ```bash
    poetry install
    ```

## Configuration

### Category Mapping

Create a `category_mapping.yaml` file in the project root. Define your categories and associated keywords in this file. Example structure:

```yaml
CategoryName:
  - "keyword1"
  - "keyword2"
  - "keyword3"
```

### Input CSV Format
The tool expects CSV files with the following columns:

```
Abschlussdatum;Abschlusszeit;Buchungsdatum;Valutadatum;Währung;Belastung;Gutschrift;Einzelbetrag;Saldo;Transaktions-Nr.;Beschreibung1;Beschreibung2;Beschreibung3;Fussnoten
```

## Usage
1. Place your transaction CSV file as transactions.csv in the project root.
1. Run the classifier:
    ```
    poetry run python transaction_classifier.py
    ```
The classified transactions will be saved in classified_transactions.csv.

## Development
### Code Style and Type Checking
The project uses ruff for code style enforcement and mypy for type checking.

1. Run ruff:
    ```
    poetry run ruff check .
    ```
2. Run mypy:
    ```
    poetry run mypy .
    ```

## Project Structure
### Code
<!-- TODO: update this to the correct format -->
```
swiss-transaction-classifier/
├── pyproject.toml           # Poetry and tool configuration
├── transaction_classifier.py # Main script
├── category_mapping.yaml    # Category definitions
├── README.md               # This file
└── .gitignore             # Git ignore file
```

### Dependencies
Project dependencies are managed through Poetry and defined in pyproject.toml.

### Logging
The script provides comprehensive logging at different levels:

- DEBUG: Detailed transaction processing information
- INFO: General processing status and results
- WARNING: Category conflicts and potential issues
- ERROR: Processing errors and exceptions
To adjust logging level, modify the _setup_logging() method in the script.

## Contributing
1. Fork the repository
1. Create your feature branch (git checkout -b feature/amazing-feature)
1. Run code style checks:
```bash
poetry run ruff check .
poetry run mypy .
```
1. Commit your changes (git commit -m 'Add amazing feature')
1. Push to the branch (git push origin feature/amazing-feature)
1. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Author
@jm-glowienke
Created: 2024-01-22