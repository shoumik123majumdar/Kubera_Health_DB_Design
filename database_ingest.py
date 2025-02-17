from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import re


load_dotenv()
password = os.getenv('MYSQL_PASSWORD') #Get SQL password from environment variable

#Load data.csv into dataframe, and then convert dataframe into dictionary for easy access to key_value pairs
df = pd.read_csv("data.csv",skiprows=1,header=None,names = ['Key','Value'])
df['Value'] = df['Value'].apply(lambda x: None if pd.isna(x) else x) # Convert Nan values into None for SQl insertions
contract_info = dict(zip(df['Key'], df['Value']))

# Initialize contract_essential_terms dictionary with essential terms for Contract insertions
contract_essential_terms = {
    'effective_date': contract_info.get('Effective Date'),
    'payor_name': contract_info.get('Payor Name'),
    'termination_period': contract_info.get('Termination Notice Period'),
    'stop_loss_threshold': contract_info.get('Stop Loss Threshold')
}

#Clean effective date
effective_date_str = contract_info.get('Effective Date')
effective_date = datetime.strptime(effective_date_str, '%d-%b-%y')
contract_essential_terms['effective_date'] = effective_date

#Clean termination_date
def convert_termination_period(termination_period):
    # Use regex to find the number in the string
    match = re.search(r'(\d+)', termination_period)
    
    if match:
        # Convert the matched string to an integer
        return int(match.group(1))
    else:
        return None 
    
contract_essential_terms["termination_period"] = convert_termination_period(contract_essential_terms["termination_period"])

#Clean stop_loss_threshold into a decimal value
def clean_money_value(money_str):
    # Remove the dollar sign and commas
    cleaned_value = money_str.replace('$', '').replace(',', '')
    
    try:
        # Convert to float (or Decimal if needed for precision)
        return float(cleaned_value)
    except ValueError:
        raise ValueError(f"Invalid money value: {money_str}")
contract_essential_terms['stop_loss_threshold'] = clean_money_value(contract_essential_terms['stop_loss_threshold'])

# Store the file_path for Document insertions
file_path = contract_info.get('PDF_filename')

# Group the rest of the contract terms into contract_terms
contract_terms = {key: value for key, value in contract_info.items() if key not in contract_essential_terms and key != 'PDF_filename'}


#Database Instantiation 
engine = create_engine(f'mysql+pymysql://root:{password}@localhost/kubera_db', echo=True) #Connect to database
#Reflect the database, database schema already manually added to database
metadata = MetaData()
metadata.reflect(bind=engine)
Base = automap_base(metadata=metadata)
Base.prepare()
print(Base.classes.keys())  # Print all mapped table names
# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Access tables as ORM models
Healthcare_Provider = Base.classes.healthcare_providers
Contract = Base.classes.contracts  # Example
Payor = Base.classes.payors
Document = Base.classes.documents
Contract = Base.classes.contracts
Contract_Terms = Base.classes.contract_terms
Amendments = Base.classes.amendments
Contract_Term_Revisions = Base.classes.contract_term_revisions

#Get healthcare provider (manually added one beforehand for the sake of the example)
provider = session.query(Healthcare_Provider).filter_by(name="ABC Healthcare").first()

#Get payor information
#Check if Payor exists, and insert if not
payor_name = contract_essential_terms['payor_name']
payor = session.query(Payor).filter(Payor.name == payor_name).first()
if not payor:
    # If Payor does not already exist, insert a new Payor
    payor = Payor(name=payor_name)
    session.add(payor)
    session.commit()  # Commit to get the payor_id
    print(f"Inserted new payor: {payor_name}")


#Create and add the document s3 storage filepath to the documents table
document = Document(file_path=file_path)
session.add(document)
session.commit()

#Create and add the contract to the database
contract = Contract(
    effective_date=contract_essential_terms['effective_date'],
    payor_id=payor.payor_id,
    provider_id = provider.provider_id,
    document_id = document.document_id,
    termination_notice_period=contract_essential_terms['termination_period'],
    stop_loss_threshold=contract_essential_terms['stop_loss_threshold'],
    created_at=datetime.now() 
)
session.add(contract)
session.commit()

#Add the rest of the contract terms to the database
for key, value in contract_terms.items():
    if value is not None:
        contract_term = Contract_Terms(
            contract_id=contract.contract_id,
            term_name=key,  # The name of the contract term
            term_value=value,  # The value of the term (can be None or an actual value)
            created_at = datetime.now()
        )
        session.add(contract_term)
session.commit()