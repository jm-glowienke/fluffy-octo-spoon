from pathlib import Path

import pandas as pd
from typer import Typer

from fluffy_octo_spoon.transaction_classifier import TransactionClassifier

app = Typer()


@app()
def process_transactions(config_file_path: Path, transactions_input_path: Path, classifications_output_path: Path):
    """Classify transactions provided in csv file"""
    classifier = TransactionClassifier(yaml_path=config_file_path)

    classifier.process_transactions(input_path=transactions_input_path, output_path=classifications_output_path)

    # Read the classified transactions CSV file

    df = pd.read_csv(classifications_output_path, delimiter=";", encoding="utf-8")

    # Preprocess the data
    df["Buchungsdatum"] = pd.to_datetime(df["Buchungsdatum"], format="%Y-%m-%d")
    # df["Buchungsdatum"] = pd.to_datetime(df["Buchungsdatum"], format="%d.%m.%y")
    df["Monat"] = df["Buchungsdatum"].dt.to_period("M").astype(str)  # Convert Period to string
    df["Kategorie"] = df["Kategorie"].fillna("Sonstiges")

    monthly_category_sums = df.groupby(["Monat", "Kategorie"])["Einzelbetrag"].sum().abs().reset_index()

    return monthly_category_sums
