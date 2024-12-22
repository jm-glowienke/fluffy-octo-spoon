import csv
import logging
from decimal import Decimal
from pathlib import Path
from typing import Dict, List

import yaml


class TransactionClassifier:
    """A class to classify Swiss bank transactions based on keyword mapping."""

    def __init__(self, yaml_path: Path):
        """
        Initialize the TransactionClassifier.

        Args:
            yaml_path: Path to the YAML file containing category mappings
        """
        self.categories: Dict[str, List[str]] = self._load_category_mapping(yaml_path)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the classifier."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _load_category_mapping(yaml_path: Path) -> Dict[str, List[str]]:
        """
        Load category mappings from YAML file.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            Dictionary containing category mappings
        """
        try:
            with open(yaml_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise RuntimeError(f"Failed to load YAML file: {e}")

    def _parse_amount(self, debit: str, credit: str) -> Decimal:
        """
        Parse transaction amount from debit or credit field.

        Args:
            debit: Debit amount string
            credit: Credit amount string

        Returns:
            Decimal amount (negative for debits, positive for credits)
        """
        try:
            if debit:
                # In case the debit string is already negative, keep it as negative amount
                # by first taking the absolute value
                return -abs(Decimal(debit.replace("'", "").replace(",", ".")))
            elif credit:
                return Decimal(credit.replace("'", "").replace(",", "."))
            return Decimal("0")
        except Exception as e:
            self.logger.warning(f"Could not parse amount: {e}")
            return Decimal("0")

    def classify_transaction(self, description: str, amount: Decimal) -> str:
        """
        Classify a transaction based on its description and amount.

        Args:
            description: Transaction description to classify
            amount: Transaction amount

        Returns:
            Classified category or 'Unknown' if no match is found
        """
        description = description.lower()

        for category, keywords in self.categories.items():
            if any(keyword.lower() in description for keyword in keywords):
                return category

        self.logger.info(
            f"Could not classify transaction with description {description} and amount {amount}. "
            "Using Amount-based Classification"
        )
        # Amount-based classification
        if amount > 0:
            if amount > 3000:
                return "Gehalt"
        elif amount < 0:
            if abs(amount) > 1000:
                return "Grosse Ausgaben"

        self.logger.info("No category identified, adding category 'Sonstiges'")
        return "Sonstiges"

    def process_transactions(self, input_path: Path, output_path: Path) -> None:
        """
        Process transactions from input CSV and write classified results to output CSV.

        Args:
            input_path: Path to input CSV file
            output_path: Path to output CSV file
        """
        try:
            transactions = []
            with open(input_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file, delimiter=";")
                for row in reader:
                    # Combine all description fields for better classification
                    combined_description = " ".join(
                        filter(
                            None,
                            [row.get("Beschreibung1", ""), row.get("Beschreibung2", ""), row.get("Beschreibung3", "")],
                        )
                    )

                    # Parse amount
                    amount = self._parse_amount(row.get("Belastung", ""), row.get("Gutschrift", ""))

                    category = self.classify_transaction(combined_description, amount)
                    row["Kategorie"] = category
                    transactions.append(row)

            # Write classified transactions to output file
            if transactions:
                fieldnames = list(transactions[0].keys())
                with open(output_path, "w", encoding="utf-8", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
                    writer.writeheader()
                    writer.writerows(transactions)

                self.logger.info(f"Erfolgreich {len(transactions)} Transaktionen verarbeitet")
            else:
                self.logger.warning("Keine Transaktionen zum Verarbeiten gefunden")

        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Transaktionen: {e}")
            raise


def main():
    """Main function to run the transaction classifier."""
    # Define paths
    base_path = Path.cwd()
    yaml_path = base_path / "category_mapping.yaml"
    input_path = base_path / "transactions.csv"
    output_path = base_path / "classified_transactions.csv"

    # Initialize and run classifier
    classifier = TransactionClassifier(yaml_path)
    classifier.process_transactions(input_path, output_path)


if __name__ == "__main__":
    main()
