#!/usr/bin/env python3
"""
Streamlit UI for HIVE to Snowflake SQL Converter

This script provides a web interface using Streamlit for converting HIVE SQL scripts to Snowflake SQL.
"""

import os
import streamlit as st
import tempfile
from pathlib import Path
import logging
from hive_to_snowflake_converter import HiveToSnowflakeConverter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="HIVE to Snowflake SQL Converter",
    page_icon="❄️",
    layout="wide",
)

# Store converted SQL in session state so it can be accessed across reruns
if 'converted_sql' not in st.session_state:
    st.session_state.converted_sql = None

def list_directories(base_path=None, max_depth=2, current_depth=0):
    """
    List directories recursively starting from base_path up to max_depth.
    Returns a list of directories with their full paths.
    """
    if base_path is None:
        # On macOS, start from home directory if no base path is provided
        base_path = os.path.expanduser("~")
    
    # Convert to Path object for easier manipulation
    base = Path(base_path)
    
    result = []
    
    # Check if this is a valid directory
    if not base.is_dir():
        return result
    
    # Add the base directory itself
    result.append(str(base))
    
    # Stop recursion if we've reached max depth
    if current_depth >= max_depth:
        return result
    
    # List subdirectories
    try:
        for item in base.iterdir():
            if item.is_dir() and not item.name.startswith('.'):  # Skip hidden directories
                # Recursively add subdirectories
                result.extend(list_directories(item, max_depth, current_depth + 1))
    except (PermissionError, OSError):
        # Skip directories we don't have permission to access
        pass
        
    return result

def directory_browser(key="dir_browser"):
    """
    Create a directory browser interface for selecting folders.
    Returns the selected directory path.
    """
    col1, col2 = st.columns([1, 2])
    
    # Start with the home directory
    home_dir = os.path.expanduser("~")
    
    # Get common directories
    common_dirs = []
    
    # Add standard macOS locations
    for dir_name in ["Desktop", "Documents", "Downloads"]:
        path = os.path.join(home_dir, dir_name)
        if os.path.isdir(path):
            common_dirs.append(path)
    
    # Add current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    if current_dir not in common_dirs:
        common_dirs.append(current_dir)
    
    # Get the full directory list (limited depth to avoid performance issues)
    all_dirs = list_directories(max_depth=2)
    
    # Let user select a common directory or browse manually
    with col1:
        st.write("Common Locations:")
        selected_common_dir = st.radio(
            "Quick Access",
            options=common_dirs,
            format_func=lambda x: f"{os.path.basename(x)} {'(current folder)' if x == current_dir else ''}",
            key=f"{key}_common"
        )
    
    # Provide manual directory selection
    with col2:
        st.write("Browse Directories:")
        
        # Filter directories to show based on search term
        search_term = st.text_input("Search directories", key=f"{key}_search")
        filtered_dirs = [d for d in all_dirs if search_term.lower() in d.lower()] if search_term else all_dirs
        
        # Limit the number of directories shown to avoid UI clutter
        max_dirs_to_show = 10
        dirs_to_show = filtered_dirs[:max_dirs_to_show]
        
        if filtered_dirs:
            selected_dir = st.selectbox(
                "Select Directory",
                options=dirs_to_show,
                format_func=lambda x: f"{os.path.basename(x)} ({x})",
                key=f"{key}_select"
            )
        else:
            selected_dir = None
            st.warning("No matching directories found.")
    
    # User can choose either the common directory or manually selected one
    custom_dir = st.text_input("Or enter directory path manually:", key=f"{key}_custom")
    
    # Determine which directory to use
    if custom_dir and os.path.isdir(custom_dir):
        final_dir = custom_dir
    elif selected_dir:
        final_dir = selected_dir
    else:
        final_dir = selected_common_dir
        
    # Show the selected directory
    st.info(f"Selected directory: {final_dir}")
    
    # Create directory if it doesn't exist
    if st.checkbox("Create directory if it doesn't exist", value=True, key=f"{key}_create"):
        if not os.path.exists(final_dir):
            try:
                os.makedirs(final_dir)
                st.success(f"Created directory: {final_dir}")
            except Exception as e:
                st.error(f"Error creating directory: {str(e)}")
    
    return final_dir

def save_to_disk(output_folder, snowflake_sql, filename):
    """Helper function to save the converted SQL to disk"""
    try:
        if not output_folder:
            st.error("No output folder selected")
            return False
            
        # Make sure the output directory exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        full_path = os.path.join(output_folder, filename)
        
        # Write the file
        with open(full_path, "w") as f:
            f.write(snowflake_sql)
        
        return full_path
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        logger.error(f"Error saving file: {str(e)}")
        return False

def validate_converted_sql(sql_code):
    """Validates the converted SQL for Snowflake syntax."""
    from sqlfluff import lint
    from sqlfluff.core import FluffConfig

    config = FluffConfig(configs={'dialect': 'snowflake'})
    linting_result = lint(sql_code, config=config)

    if linting_result:
        errors = []
        for file_result in linting_result:
            for error in file_result['errors']:
                errors.append(f"- {error['description']} at line {error['line_no']}, column {error['line_pos']}")
        return errors
    return None

def main():
    st.title("❄️ HIVE to Snowflake SQL Converter")
    st.write("Upload a HIVE SQL script and convert it to Snowflake SQL using OpenAI's LLM")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("OpenAI API Key", type="password", 
                               help="Enter your OpenAI API key or set OPENAI_API_KEY env variable")
        
        model = st.selectbox(
            "Select OpenAI Model",
            ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            index=0,
            help="Select the OpenAI model to use for conversion"
        )
        
        # Add prompt template selection
        st.subheader("Prompt Template")
        template_option = st.radio(
            "Choose Prompt Template Source",
            ["Default Template", "Upload Custom Template", "Edit Template"],
            index=0,
            help="Use the default template or provide your own"
        )
        
        prompt_template_path = None
        custom_prompt_content = None
        
        if template_option == "Upload Custom Template":
            uploaded_prompt = st.file_uploader("Upload Prompt Template", type=["txt"])
            if uploaded_prompt is not None:
                try:
                    # Save the uploaded prompt template to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
                        tmp_file.write(uploaded_prompt.getvalue())
                        prompt_template_path = tmp_file.name
                    
                    st.success("Custom prompt template loaded")
                    
                    # Show preview of the prompt
                    with st.expander("Preview Prompt Template"):
                        st.code(uploaded_prompt.getvalue().decode("utf-8"))
                except Exception as e:
                    st.error(f"Error loading template: {str(e)}")
                    logger.error(f"Error loading uploaded template: {str(e)}")
        
        elif template_option == "Edit Template":
            # Try to load the default template first
            default_template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                               "conversion_prompt_template.txt")
            default_content = ""
            
            try:
                if os.path.exists(default_template_path):
                    with open(default_template_path, 'r', encoding='utf-8') as f:
                        default_content = f.read()
            except Exception as e:
                logger.warning(f"Could not load default template: {str(e)}")
                default_content = """Convert the following HIVE SQL script to Snowflake SQL. Pay special attention to:

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

Please respond with only the converted Snowflake SQL, with no additional comments or explanations."""
            
            # Allow editing the template
            custom_prompt_content = st.text_area("Edit Prompt Template", 
                                              default_content, 
                                              height=300,
                                              help="Make sure to keep the {hive_sql} placeholder")
            
            if custom_prompt_content:
                if "{hive_sql}" not in custom_prompt_content:
                    st.warning("Warning: Template must contain the {hive_sql} placeholder")
                else:
                    try:
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
                            tmp_file.write(custom_prompt_content.encode('utf-8'))
                            prompt_template_path = tmp_file.name
                    except Exception as e:
                        st.error(f"Error saving template: {str(e)}")
                        logger.error(f"Error saving edited template: {str(e)}")
        
        st.divider()
        st.markdown("### About")
        st.markdown("""
        This tool uses OpenAI's language models to convert HIVE SQL to Snowflake SQL.
        
        The conversion process handles:
        - HIVE-specific syntax
        - Data type differences
        - File paths and external tables
        - Function translations
        - Partitioning syntax
        - Performance optimization directives
        """)

    # Main content area
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Input")
        uploaded_file = st.file_uploader("Upload HIVE SQL file", type=["sql", "hql", "txt"])
        
        input_sql = ""
        if uploaded_file is not None:
            try:
                input_sql = uploaded_file.getvalue().decode("utf-8")
                st.code(input_sql, language="sql", line_numbers=True)
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        
        manual_input = st.checkbox("Or enter SQL manually")
        if manual_input:
            input_sql = st.text_area("Enter HIVE SQL:", height=300)
    
    with col2:
        st.header("Output")
        
        # Directory selection for output - only using the folder browser now
        st.subheader("Output Location")
        with st.expander("Select Output Folder", expanded=True):
            output_folder = directory_browser(key="output_dir")
        
        # Use API key from input or environment variable
        api_key_to_use = api_key or os.environ.get("OPENAI_API_KEY")
        
        convert_button = st.button("Convert to Snowflake SQL", 
                                  type="primary", 
                                  disabled=(not input_sql or not api_key_to_use))
        
        if convert_button and input_sql and api_key_to_use:
            with st.spinner("Converting SQL..."):
                try:
                    # Initialize the converter with the prompt template if provided
                    converter = HiveToSnowflakeConverter(
                        api_key=api_key_to_use,
                        prompt_template_path=prompt_template_path
                    )
                    
                    # Convert the SQL
                    snowflake_sql = converter.convert_to_snowflake(input_sql, model=model)
                    
                    # Store in session state for access across reruns
                    st.session_state.converted_sql = snowflake_sql
                    
                    # Display the converted SQL
                    st.code(snowflake_sql, language="sql", line_numbers=True)
                    
                    # Clean up the temporary prompt template file if it was created
                    if prompt_template_path and os.path.exists(prompt_template_path) and template_option != "Default Template":
                        try:
                            os.unlink(prompt_template_path)
                        except Exception:
                            pass
                
                except Exception as e:
                    st.error(f"Error during conversion: {str(e)}")
        
        # Save functionality (separated from conversion logic)
        if st.session_state.converted_sql is not None:
            st.subheader("Save Options")
            col_download, col_save = st.columns(2)
            
            with col_download:
                st.download_button(
                    label="Download SQL",
                    data=st.session_state.converted_sql,
                    file_name="converted_snowflake.sql",
                    mime="text/plain",
                )
            
            with col_save:
                save_filename = "converted_snowflake.sql"
                if uploaded_file is not None:
                    save_filename = os.path.splitext(uploaded_file.name)[0] + "_snowflake.sql"
                
                if st.button("Save to Selected Folder", key="save_to_disk_btn"):
                    saved_path = save_to_disk(output_folder, st.session_state.converted_sql, save_filename)
                    if saved_path:
                        st.success(f"Saved to: {saved_path}")
    
    # Add validation to the Streamlit app
    if st.session_state.converted_sql is not None:
        st.subheader("Validation Results")
        validation_errors = validate_converted_sql(st.session_state.converted_sql)

        if validation_errors:
            st.error("Validation errors found in the converted SQL:")
            for error in validation_errors:
                st.text(error)
        else:
            st.success("The converted SQL is valid for Snowflake syntax.")
    
    # Add helpful information about the converter
    st.divider()
    st.subheader("Tips for conversion")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("""
        **Handling complex queries:**
        - Make sure complete CREATE TABLE statements are included
        - Include all necessary query components
        - Check for proper formatting and syntax in HIVE SQL
        """)
    
    with tips_col2:
        st.markdown("""
        **After conversion:**
        - Review data types for appropriate mappings
        - Verify file paths and external table formats
        - Test on smaller datasets before production use
        - Check JOIN optimizations and partitioning
        """)
        
    # Add information about customizing the prompt template
    st.divider()
    st.subheader("About Custom Prompt Templates")
    
    st.markdown("""
    You can use a custom prompt template file to guide the AI in converting your SQL.
    The template must include the placeholder `{hive_sql}` where your HIVE SQL code will be inserted.
    
    Example template format:
    ```
    Convert this HIVE SQL to Snowflake SQL:
    
    {hive_sql}
    
    Make sure to handle these specific aspects in your conversion...
    ```
    """)

if __name__ == "__main__":
    main()