import csv
import io
import logging
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class TransactionClassifier:
    """A class to classify Swiss bank transactions based on keyword mapping."""

    EXPECTED_COLUMNS = [
        "Abschlussdatum",
        "Abschlusszeit",
        "Buchungsdatum",
        "Valutadatum",
        "Währung",
        "Belastung",
        "Gutschrift",
        "Einzelbetrag",
        "Saldo",
        "Transaktions-Nr.",
        "Beschreibung1",
        "Beschreibung2",
        "Beschreibung3",
        "Fussnoten",
    ]

    def __init__(self, yaml_path: Path):
        """
        Initialize the TransactionClassifier.

        Args:
            yaml_path: Path to the YAML file containing category mappings
        """
        self.categories: Dict[str, List[str]] = self._load_category_mapping(yaml_path)
        self._setup_logging()
        self.logger.debug(f"Loaded {len(self.categories)} categories from YAML file")

    def _setup_logging(self) -> None:
        """Configure logging for the classifier."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger("TransactionClassifier")

    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID."""
        return str(uuid.uuid4())

    def _clean_csv_content(self, file_path: Path) -> Tuple[str, List[str]]:
        """
        Remove header information and find the actual CSV content starting with column names.

        Args:
            file_path: Path to the input CSV file

        Returns:
            Tuple containing cleaned CSV content and list of existing column names
        """
        self.logger.debug(f"Reading CSV file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.readlines()

        # Find the line containing the column headers
        header_index = -1
        existing_columns = []
        for i, line in enumerate(content):
            columns = line.strip().split(";")
            matches = sum(1 for col in columns if col in self.EXPECTED_COLUMNS)
            if matches >= len(self.EXPECTED_COLUMNS) * 0.8:  # 80% match threshold
                header_index = i
                existing_columns = columns
                break

        if header_index == -1:
            raise ValueError("Could not find the column headers in the CSV file")

        self.logger.info(f"Found header row at line {header_index + 1}")
        self.logger.debug(f"Existing columns: {existing_columns}")

        # Return only the content from the header row onwards
        cleaned_content = "".join(content[header_index:])
        return cleaned_content, existing_columns

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
                categories = yaml.safe_load(file)
                logging.getLogger("TransactionClassifier").debug(
                    f"Loaded categories from {yaml_path}: {list(categories.keys())}"
                )
                return categories
        except Exception as e:
            raise RuntimeError(f"Failed to load YAML file: {e}")

    def _parse_amount(self, debit: str, credit: str, transaction_id: str) -> Decimal:
        """
        Parse transaction amount from debit or credit field.

        Args:
            debit: Debit amount string
            credit: Credit amount string
            transaction_id: Unique transaction ID for logging

        Returns:
            Decimal amount (negative for debits, positive for credits)
        """
        try:
            if debit:
                # In case the debit string is already negative, keep it as negative amount
                # by first taking the absolute value
                amount = -abs(Decimal(debit.replace("'", "").replace(",", ".")))
                self.logger.debug(f"[{transaction_id}] Parsed debit amount: {amount}")
                return amount
            elif credit:
                amount = Decimal(credit.replace("'", "").replace(",", "."))
                self.logger.debug(f"[{transaction_id}] Parsed credit amount: {amount}")
                return amount

            self.logger.warning(f"[{transaction_id}] No amount found in transaction")
            return Decimal("0")
        except Exception as e:
            self.logger.error(f"[{transaction_id}] Could not parse amount: {e}")
            return Decimal("0")

    def classify_transaction(  # noqa: C901
        self, description: str, amount: Decimal, transaction_id: str, existing_category: Optional[str] = None
    ) -> str:
        """
        Classify a transaction based on its description and amount.

        Args:
            description: Transaction description to classify
            amount: Transaction amount
            transaction_id: Unique transaction ID for logging
            existing_category: Existing category if present

        Returns:
            Classified category or 'Unknown' if no match is found
        """
        self.logger.debug(f"[{transaction_id}] Classifying transaction: {description[:50]}...")

        if existing_category:
            new_category = None
            description = description.lower()

            # Check if the existing category would be classified differently
            for category, keywords in self.categories.items():
                if any(keyword.lower() in description for keyword in keywords):
                    new_category = category
                    break

            if new_category and new_category != existing_category:
                self.logger.warning(
                    f"[{transaction_id}] Category conflict: existing='{existing_category}' "
                    f"new='{new_category}'. Using new category."
                )
                return new_category

            self.logger.debug(f"[{transaction_id}] Using existing category: {existing_category}")
            return existing_category

        description = description.lower()
        for category, keywords in self.categories.items():
            if any(keyword.lower() in description for keyword in keywords):
                self.logger.debug(f"[{transaction_id}] Matched category '{category}' based on keywords")
                return category

        # Amount-based classification
        if amount > 0:
            if amount > 3000:
                self.logger.debug(f"[{transaction_id}] Classified as 'Gehalt' based on amount")
                return "Gehalt"
        elif amount < 0:
            if abs(amount) > 1000:
                self.logger.debug(f"[{transaction_id}] Classified as 'Grosse Ausgaben' based on amount")
                return "Grosse Ausgaben"

        self.logger.debug(f"[{transaction_id}] No category match found, using 'Sonstiges'")
        return "Sonstiges"

    def process_transactions(self, input_path: Path, output_path: Path) -> None:
        """
        Process transactions from input CSV and write classified results to output CSV.

        Args:
            input_path: Path to input CSV file
            output_path: Path to output CSV file
        """
        try:
            # Clean the CSV content first
            cleaned_content, existing_columns = self._clean_csv_content(input_path)

            # Process the cleaned content
            transactions = []
            csv_file = io.StringIO(cleaned_content)
            reader = csv.DictReader(csv_file, delimiter=";")

            # Check for existing ID and Category columns
            has_id_column = "ID" in existing_columns
            has_category_column = "Kategorie" in existing_columns

            self.logger.info(
                f"Processing CSV with existing columns - ID: {has_id_column}, " f"Category: {has_category_column}"
            )

            for row in reader:
                # Use existing ID or generate new one
                transaction_id = row.get("ID", self._generate_transaction_id())

                self.logger.debug(f"Processing transaction [{transaction_id}]")

                # Combine all description fields for better classification
                combined_description = " ".join(
                    filter(
                        None, [row.get("Beschreibung1", ""), row.get("Beschreibung2", ""), row.get("Beschreibung3", "")]
                    )
                )

                # Parse amount
                amount = self._parse_amount(row.get("Belastung", ""), row.get("Gutschrift", ""), transaction_id)

                # Classify transaction
                existing_category = row.get("Kategorie") if has_category_column else None
                category = self.classify_transaction(combined_description, amount, transaction_id, existing_category)

                # Update row with ID and category
                row["ID"] = transaction_id
                row["Kategorie"] = category
                transactions.append(row)

            # Write classified transactions to output file
            if transactions:
                fieldnames = list(transactions[0].keys())
                with open(output_path, "w", encoding="utf-8", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
                    writer.writeheader()
                    writer.writerows(transactions)

                self.logger.info(
                    f"Successfully processed {len(transactions)} transactions. " f"Output written to {output_path}"
                )
            else:
                self.logger.warning("No transactions found to process")

        except Exception as e:
            self.logger.error(f"Error processing transactions: {e}", exc_info=True)
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
