import json
import requests
import graphviz
import streamlit as st
from collections import defaultdict

#--------------------------
# Salesforce Territory Visualizer

# Author: Mohan Chinnappan 

# Maintain author's name in your copies
#--------------------------

def load_auth(auth_file):
    """
    Load authentication data from a JSON file.
    
    Parameters:
        auth_file (file-like object): A file-like object containing Salesforce authentication details in JSON format.
    
    Returns:
        dict: A dictionary containing Salesforce authentication data.
    """
    return json.load(auth_file)

def query_salesforce(auth_data, query):
    """
    Execute a SOQL query against Salesforce and return the results.
    
    Parameters:
        auth_data (dict): Dictionary containing Salesforce authentication data.
        query (str): SOQL query string.
    
    Returns:
        list of dict: A list of dictionaries representing the query results.
    """
    headers = {
        'Authorization': f'Bearer {auth_data["access_token"]}',
        'Content-Type': 'application/json'
    }
    url = f"{auth_data['instance_url']}/services/data/v60.0/query/"
    params = {'q': query}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an error if the request was unsuccessful
    return response.json()['records']

def determine_levels(territories):
    """
    Determine the hierarchical levels of territories based on their parent-child relationships.
    
    Parameters:
        territories (list of dict): List of territories, each represented as a dictionary with Id, Name, and ParentTerritory2Id.
    
    Returns:
        dict: A dictionary mapping territory IDs to their hierarchical levels.
    """
    levels = {}
    children = defaultdict(list)
    for territory in territories:
        parent = territory['ParentTerritory2Id']
        if parent:
            children[parent].append(territory['Id'])
        else:
            levels[territory['Id']] = 0

    def assign_levels(node, level):
        """
        Recursive function to assign levels to each territory.
        
        Parameters:
            node (str): The ID of the current node (territory).
            level (int): The level to assign to the node.
        """
        for child in children[node]:
            levels[child] = level + 1
            assign_levels(child, level + 1)

    initial_nodes = list(levels.keys())
    for node in initial_nodes:
        assign_levels(node, 0)

    return levels

def create_graph(territories, levels, output_format, size):
    """
    Create a visual representation of the territory hierarchy and save it to a file.
    
    Parameters:
        territories (list of dict): List of territories with their Id, Name, and ParentTerritory2Id.
        levels (dict): Dictionary mapping territory IDs to their hierarchical levels.
        output_format (str): Format of the output file (png, svg, pdf).
        size (str): Size of the output graph in the format width,height (e.g., 800,800).
    
    Returns:
        str: Path to the saved output file.
    """
    dot = graphviz.Digraph(comment='Salesforce Territories', format=output_format)
    dot.attr(rankdir='LR', size=size, nodesep='1', ranksep='2')
    dot.attr('node', shape='rect', style='filled', color='lightblue2', fontname='Helvetica', fontsize='12')

    colors = ['black', 'blue', 'green', 'red', 'purple', 'orange']
    for territory in territories:
        dot.node(territory['Id'], territory['Name'])
        if territory['ParentTerritory2Id']:
            level = levels[territory['Id']]
            color = colors[level % len(colors)]
            dot.edge(territory['ParentTerritory2Id'], territory['Id'], color=color)

    output_file = '/tmp/territories'
    dot.render(output_file, format=output_format, view=False)
    return output_file + '.' + output_format

def main():
    """
    Main function to run the Streamlit app.
    """

    st.sidebar.title("Salesforce Territory Visualizer")

    # Provide a link to the documentation file in the sidebar
    st.sidebar.markdown("""
    ## Documentation

Salesforce Territory Visualizer

Author:
     Mohan Chinnappan 

Maintain author's name in your copies

Description:
    This Streamlit application visualizes Salesforce territories as a directed graph. It retrieves territory data
    from Salesforce using a SOQL query, generates a graphical representation of the territory hierarchy using Graphviz,
    and allows users to download the generated graph in various formats.

Dependencies:
    - json: Standard Python library for JSON handling.
    - requests: Python library for making HTTP requests.
    - graphviz: Python interface for the Graphviz graph-drawing software.
    - streamlit: Library for creating web applications for machine learning and data science projects.
    - collections: Standard Python library for specialized container datatypes (used for defaultdict).

Functions:
    - load_auth(auth_file):
        Description: Loads authentication data from a JSON file.
        Parameters:
            - auth_file (file-like object): A file-like object containing Salesforce authentication details in JSON format.
        Returns:
            - A dictionary containing Salesforce authentication data.
    
    - query_salesforce(auth_data, query):
        Description: Executes a SOQL query against Salesforce and returns the results.
        Parameters:
            - auth_data (dict): Dictionary containing Salesforce authentication data.
            - query (str): SOQL query string.
        Returns:
            - A list of dictionaries representing the query results.
    
    - determine_levels(territories):
        Description: Determines the hierarchical levels of territories based on their parent-child relationships.
        Parameters:
            - territories (list of dict): List of territories, each represented as a dictionary with Id, Name, and ParentTerritory2Id.
        Returns:
            - A dictionary mapping territory IDs to their hierarchical levels.
    
    - create_graph(territories, levels, output_format, size):
        Description: Creates a visual representation of the territory hierarchy and saves it to a file.
        Parameters:
            - territories (list of dict): List of territories with their Id, Name, and ParentTerritory2Id.
            - levels (dict): Dictionary mapping territory IDs to their hierarchical levels.
            - output_format (str): Format of the output file (png, svg, pdf).
            - size (str): Size of the output graph in the format width,height (e.g., 800,800).
        Returns:
            - str: Path to the saved output file.

Streamlit Interface:
    - File uploader for `auth.json` file.
    - Dropdown for selecting the output format.
    - Text input for specifying the graph size.
    - Button to generate the graph and provide a download link.

Usage:
    Run the Streamlit application and use the interface to upload the `auth.json` file, select the output format,
    specify the graph size, and visualize the Salesforce territories.

Notes:
    - Ensure that Graphviz is installed on your system to render the graphs. You can download it from Graphviz's official site.
    - The auth.json file must contain valid Salesforce authentication data, including access_token and instance_url.    
    """)


    st.title("Salesforce Territory Visualizer")

    auth_json = st.file_uploader("Upload auth.json file", type=['json'])
    
    if auth_json is not None:
        auth_data = load_auth(auth_json)
        
        output_format = st.selectbox("Select output format", ['png', 'svg', 'pdf'], index=0)
        size = st.text_input("Enter size of the output graph (e.g., 800,800)", value='800,800')
        
        if st.button("Visualize Territories"):
            with st.spinner("Fetching territories from Salesforce..."):
                territories = query_salesforce(auth_data, "SELECT Id, Name, ParentTerritory2Id FROM Territory2")
                levels = determine_levels(territories)
            
            with st.spinner("Creating graph..."):
                output_file_path = create_graph(territories, levels, output_format, size)
                st.graphviz_chart(graphviz.Source.from_file(output_file_path).source)
                
                st.success(f"Graph created and saved to {output_file_path}")

                # Provide download button
                with open(output_file_path, "rb") as file:
                    st.download_button(
                        label="Download Graph",
                        data=file,
                        file_name=f"territories.{output_format}",
                        mime=f"image/{output_format}" if output_format != "pdf" else "application/pdf"
                    )

if __name__ == '__main__':
    main()