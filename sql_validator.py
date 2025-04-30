from sqlfluff import lint
from sqlfluff.core import FluffConfig

def lint_snowflake_sql(sql_code):
    """Lints SQL code using sqlfluff with the Snowflake dialect."""
    config = FluffConfig(configs={'dialect': 'snowflake'})

    result = lint(sql_code, config=config)
    return result

# Example usage
if __name__ == "__main__":
    sql_file_path = input("Enter the path to the SQL file to validate: ")
    try:
        with open(sql_file_path, 'r') as sql_file:
            sql_code_to_check = sql_file.read()

        linting_result = lint_snowflake_sql(sql_code_to_check)

        if linting_result:
            print("Linting errors found:")
            for file_result in linting_result:
                for error in file_result['errors']:
                    print(f"- {error['description']} at line {error['line_no']}, column {error['line_pos']}")
        else:
            print("No linting errors found.")
    except FileNotFoundError:
        print("The specified file was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")