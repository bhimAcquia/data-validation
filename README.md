# SQL Conversion and Validation Tool

A comprehensive toolkit for converting HIVE SQL scripts to Snowflake SQL and validating SQL syntax.

## Features

- **HIVE to Snowflake SQL Conversion**: Converts HIVE SQL scripts to Snowflake compatible syntax using OpenAI's language models
- **Snowflake SQL Validation**: Validates SQL scripts for Snowflake syntax compliance
- **Interactive Web Interface**: User-friendly Streamlit application for easy conversion and validation

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd data-validation
   ```

2. Set up a Python virtual environment (optional but recommended):
   ```bash
   python -m venv project1
   source project1/bin/activate  # On Windows: project1\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Streamlit Web Application

Run the Streamlit application for an interactive interface:

```bash
streamlit run streamlit_app.py
```

The web application allows you to:
- Upload HIVE SQL files for conversion
- Enter SQL manually
- Configure OpenAI API settings
- Save and download converted SQL scripts
- Validate converted SQL for Snowflake syntax compliance

### Command-line SQL Validation

To validate a SQL file for Snowflake syntax:

```bash
python sql_validator.py
```

When prompted, enter the path to the SQL file you want to validate.

### Programmatic Usage

You can also use the converter and validator in your own Python scripts:

```python
from hive_to_snowflake_converter import HiveToSnowflakeConverter
from sql_validator import lint_snowflake_sql

# Initialize converter with OpenAI API key
converter = HiveToSnowflakeConverter(api_key="your-api-key")

# Convert HIVE SQL to Snowflake SQL
with open("your_hive_script.hql", "r") as file:
    hive_sql = file.read()
    
snowflake_sql = converter.convert_to_snowflake(hive_sql, model="gpt-4")

# Validate the converted SQL
validation_results = lint_snowflake_sql(snowflake_sql)
```

## Requirements

- Python 3.6+
- OpenAI API key
- Required Python packages (see requirements.txt)

## Components

- `streamlit_app.py`: Web interface for the conversion tool
- `hive_to_snowflake_converter.py`: Core conversion functionality using OpenAI's API
- `sql_validator.py`: SQL validation using SQLFluff
- `conversion_prompt_template.txt`: Template for the OpenAI prompt used in conversion

## Example Files

- `nw_customer_POST_650.hql`: Sample HIVE SQL file
- `nw_customer_POST_650_snowflake.sql`: Sample converted Snowflake SQL
- `sf_dw_customer_POST_650.sql`: Another Snowflake SQL example

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.