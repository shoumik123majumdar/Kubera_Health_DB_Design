import os
import re
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base


# Load environment variables
load_dotenv()
password = os.getenv('MYSQL_PASSWORD')  # Get SQL password from environment variable

# Helper function to load CSV data into a dictionary
def load_contract_data(csv_path="data.csv"):
    df = pd.read_csv(csv_path, skiprows=1, header=None, names=['Key', 'Value'])
    df['Value'] = df['Value'].apply(lambda x: None if pd.isna(x) else x)  # Convert NaN values into None for SQL insertions
    return dict(zip(df['Key'], df['Value']))


# Helper function to clean date string into a datetime object
def clean_effective_date(date_str):
    return datetime.strptime(date_str, '%d-%b-%y')


# Helper function to extract number from a string (e.g., Termination Period)
def convert_termination_period(termination_period):
    match = re.search(r'(\d+)', termination_period)
    return int(match.group(1)) if match else None


# Helper function to clean monetary value into a float
def clean_money_value(money_str):
    cleaned_value = money_str.replace('$', '').replace(',', '')
    try:
        return float(cleaned_value)
    except ValueError:
        raise ValueError(f"Invalid money value: {money_str}")


class ContractHandler:
    """
    A class to handle the insertion of contract-related data into the database.

    This class provides methods for adding new contracts and associated data, 
    including payors, healthcare providers, documents, and contract terms, 
    into the database. 
    """
    def __init__(self, engine, session):
        self.engine = engine
        self.session = session
        self.metadata = MetaData()
        self.metadata.reflect(bind=engine)
        self.Base = automap_base(metadata=self.metadata)
        self.Base.prepare()

        # Map tables to ORM classes
        self.Healthcare_Provider = self.Base.classes.healthcare_providers
        self.Payor = self.Base.classes.payors
        self.Contract = self.Base.classes.contracts
        self.Document = self.Base.classes.documents
        self.Contract_Terms = self.Base.classes.contract_terms

    def get_or_create_payor(self, payor_name):
        """
        Given a payor_name, returns the Payor SQLAlchemy object. If the payor does not exist, 
        it creates a new Payor and returns the newly created object.

        Parameters:
        payor_name (str): The name of the payor.

        Returns:
        Payor: The Payor SQLAlchemy object, either existing or newly created.
        """
        payor = self.session.query(self.Payor).filter(self.Payor.name == payor_name).first()
        if not payor:
            payor = self.Payor(name=payor_name)
            self.session.add(payor)
            self.session.commit()  # Commit to get the payor_id
            print(f"Inserted new payor: {payor_name}")
        return payor

    def get_healthcare_provider(self, provider_name):
        """
        Retrieves a healthcare provider by its name from the database.

        Parameters:
        provider_name (str): The name of the healthcare provider.

        Returns:
        Healthcare_Provider: The Healthcare_Provider SQLAlchemy object corresponding to the provider name.
        """
        return self.session.query(self.Healthcare_Provider).filter_by(name=provider_name).first()

    def add_document(self, file_path):
        """
        Adds a new document record to the database with the given file path.

        Parameters:
        file_path (str): The file path of the document to be added.

        Returns:
        Document: The newly created Document SQLAlchemy object.
        """
        document = self.Document(file_path=file_path)
        self.session.add(document)
        self.session.commit()
        return document

    def add_contract(self, contract_essential_terms, payor_id, provider_id, document_id):
        """
        Adds a new contract record to the database with the essential contract terms.

        Parameters:
        contract_essential_terms (dict): A dictionary of essential contract terms like 'effective_date', 
                                          'termination_period', and 'stop_loss_threshold'.
        payor_id (int): The ID of the associated payor.
        provider_id (int): The ID of the associated healthcare provider.
        document_id (int): The ID of the associated document.

        Returns:
        Contract: The newly created Contract SQLAlchemy object.
        """
        contract = self.Contract(
            effective_date=contract_essential_terms['effective_date'],
            payor_id=payor_id,
            provider_id=provider_id,
            document_id=document_id,
            termination_notice_period=contract_essential_terms['termination_period'],
            stop_loss_threshold=contract_essential_terms['stop_loss_threshold'],
            created_at=datetime.now()
        )
        self.session.add(contract)
        self.session.commit()
        return contract

    def add_contract_terms(self, contract_id, contract_terms):
        """
        Adds additional contract terms to the database for a given contract.

        Parameters:
        contract_id (int): The ID of the contract to which the terms belong.
        contract_terms (dict): A dictionary of contract terms where keys are term names and values are term values.

        Returns:
        None
        """
        for key, value in contract_terms.items():
            if value is not None:
                contract_term = self.Contract_Terms(
                    contract_id=contract_id,
                    term_name=key,
                    term_value=value,
                    created_at=datetime.now()
                )
                self.session.add(contract_term)
        self.session.commit()


def process_contract_data(csv_path="data.csv"):
    contract_info = load_contract_data(csv_path)
    
    # Initialize contract_essential_terms dictionary with essential terms for Contract insertions
    contract_essential_terms = {
        'effective_date': clean_effective_date(contract_info.get('Effective Date')),
        'payor_name': contract_info.get('Payor Name'),
        'termination_period': convert_termination_period(contract_info.get('Termination Notice Period')),
        'stop_loss_threshold': clean_money_value(contract_info.get('Stop Loss Threshold'))
    }
    
    file_path = contract_info.get('PDF_filename')  # Store the file_path for Document insertions
    contract_terms = {key: value for key, value in contract_info.items() if key not in contract_essential_terms and key != 'PDF_filename'}

    # Database Instantiation
    engine = create_engine(f'mysql+pymysql://root:{password}@localhost/kubera_db', echo=True)  # Connect to database
    Session = sessionmaker(bind=engine)
    session = Session()

    # Initialize contract handler
    handler = ContractHandler(engine, session)

    # Get healthcare provider (manually added one beforehand for the sake of the example)
    provider = handler.get_healthcare_provider("ABC Healthcare")

    # Get payor information
    payor = handler.get_or_create_payor(contract_essential_terms['payor_name'])

    # Create and add the document s3 storage filepath to the documents table
    document = handler.add_document(file_path)

    # Create and add the contract to the database
    contract = handler.add_contract(contract_essential_terms, payor.payor_id, provider.provider_id, document.document_id)

    # Add the rest of the contract terms to the database
    handler.add_contract_terms(contract.contract_id, contract_terms)

process_contract_data()
