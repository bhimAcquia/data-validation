#!/usr/bin/env python3
"""
HIVE to Snowflake SQL Converter using OpenAI LLM

This script converts HIVE SQL scripts to Snowflake SQL syntax using OpenAI's API.
"""

import argparse
import os
from openai import OpenAI
import logging
from typing import Optional, Dict, Any
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HiveToSnowflakeConverter:
    """Class to handle conversion of HIVE SQL to Snowflake SQL using OpenAI's API."""
    
    DEFAULT_PROMPT_TEMPLATE = "conversion_prompt_template.txt"
    
    def __init__(self, api_key: Optional[str] = None, prompt_template_path: Optional[str] = None):
        """
        Initialize the converter with OpenAI API key.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from environment variable.
            prompt_template_path: Path to a custom prompt template file. If not provided, 
                                 uses the default template.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please provide it or set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Set the prompt template path
        self.prompt_template_path = prompt_template_path or self.DEFAULT_PROMPT_TEMPLATE
        
        # Check if the path is valid
        if self.prompt_template_path and not os.path.isabs(self.prompt_template_path):
            # If it's not an absolute path, make it relative to the script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.prompt_template_path = os.path.join(script_dir, self.prompt_template_path)
            
        logger.info(f"Using prompt template from: {self.prompt_template_path}")
        
    def read_hive_script(self, file_path: str) -> str:
        """
        Read the HIVE SQL script from a file.
        
        Args:
            file_path: Path to the HIVE SQL script file.
            
        Returns:
            The content of the HIVE SQL script.
        """
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
            
    def convert_to_snowflake(self, hive_sql: str, model: str = "gpt-4") -> str:
        """
        Convert HIVE SQL to Snowflake SQL using OpenAI API.
        
        Args:
            hive_sql: HIVE SQL script content.
            model: OpenAI model to use for conversion.
            
        Returns:
            Converted Snowflake SQL script.
        """
        try:
            prompt = self._create_conversion_prompt(hive_sql)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert SQL translator that specializes in converting HIVE SQL to Snowflake SQL."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic results
                max_tokens=4000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error during conversion: {e}")
            raise
            
    def _create_conversion_prompt(self, hive_sql: str) -> str:
        """
        Create a prompt for the LLM to convert HIVE SQL to Snowflake SQL.
        Loads the prompt template from the configured file path and replaces the {hive_sql} placeholder.
        
        Args:
            hive_sql: HIVE SQL script content.
            
        Returns:
            Formatted prompt for the LLM.
        """
        # Default template as fallback
        default_template = """
        Convert the following HIVE SQL script to Snowflake SQL. Pay special attention to:
        
        1. Replace HIVE-specific syntax with Snowflake equivalents
        2. Update data types appropriately (e.g., STRING to VARCHAR, INT to INTEGER)
        3. Modify file paths and external table definitions to use Snowflake patterns
        4. Replace HIVE functions with Snowflake counterparts
        5. Update partitioning syntax to Snowflake's approach
        6. Adjust any JOIN hints or performance optimization directives
        7. Convert any HIVE-specific metadata management statements
        
        Here is the HIVE SQL script:
        
        ```sql
        {hive_sql}
        ```
        
        Please respond with only the converted Snowflake SQL, with no additional comments or explanations.
        """
        
        try:
            # Check if the file exists
            if not os.path.exists(self.prompt_template_path):
                logger.warning(f"Prompt template file not found at {self.prompt_template_path}. Using default template.")
                # Replace the placeholder using string replacement to avoid regex issues
                return default_template.replace("{hive_sql}", hive_sql)
                
            # Load the prompt template from file
            with open(self.prompt_template_path, 'r', encoding='utf-8') as file:
                prompt_template = file.read()
                
            # Simple string replacement instead of regex to avoid escape sequence issues
            return prompt_template.replace("{hive_sql}", hive_sql)
            
        except Exception as e:
            logger.error(f"Error loading prompt template: {str(e)}")
            logger.info("Falling back to default template")
            # Simple string replacement
            return default_template.replace("{hive_sql}", hive_sql)
            
    def save_snowflake_script(self, snowflake_sql: str, output_path: str) -> None:
        """
        Save the converted Snowflake SQL to a file.
        
        Args:
            snowflake_sql: Converted Snowflake SQL script.
            output_path: Path where to save the Snowflake SQL script.
        """
        try:
            # Make directories if they don't exist
            output_dir = os.path.dirname(os.path.abspath(output_path))
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            with open(output_path, 'w') as file:
                file.write(snowflake_sql)
            logger.info(f"Snowflake SQL script saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving file {output_path}: {e}")
            raise

def main() -> None:
    """Main function to run the conversion process."""
    parser = argparse.ArgumentParser(description="Convert HIVE SQL to Snowflake SQL using OpenAI's API.")
    parser.add_argument("input_file", help="Path to the HIVE SQL script file")
    parser.add_argument("--output", "-o", help="Path for the output Snowflake SQL file")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY environment variable)")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use (default: gpt-4)")
    parser.add_argument("--prompt-template", help="Path to a custom prompt template file")
    
    args = parser.parse_args()
    
    # Create output file path if not provided
    if not args.output:
        base_name = os.path.splitext(args.input_file)[0]
        args.output = f"{base_name}_snowflake.sql"
    
    try:
        converter = HiveToSnowflakeConverter(
            api_key=args.api_key,
            prompt_template_path=args.prompt_template
        )
        
        logger.info(f"Reading HIVE SQL from {args.input_file}")
        hive_sql = converter.read_hive_script(args.input_file)
        
        logger.info(f"Converting HIVE SQL to Snowflake SQL using {args.model}...")
        snowflake_sql = converter.convert_to_snowflake(hive_sql, model=args.model)
        
        converter.save_snowflake_script(snowflake_sql, args.output)
        logger.info("Conversion completed successfully!")
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()