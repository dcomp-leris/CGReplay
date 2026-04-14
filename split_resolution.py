import pandas as pd

def split_srv_resolution(input_csv, output_csv):
    # Read the CSV file
    df = pd.read_csv(input_csv)
    
    # Split the 'srv_resolution' column into 'width' and 'height'
    df[['width', 'height']] = df['srv_resolution'].str.extract(r'\((\d+),\s*(\d+)\)')
    
    # Convert 'width' and 'height' to integers
    df['width'] = df['width'].astype(int)
    df['height'] = df['height'].astype(int)
    
    # Save the modified dataframe to a new CSV file
    df.to_csv(output_csv, index=False)

# Use the function to process the file
split_srv_resolution('Experiment/Fortnite/enc_1M10GLQ.csv', 'Experiment/Fortnite/enc_1M10GLQ_modified.csv')
