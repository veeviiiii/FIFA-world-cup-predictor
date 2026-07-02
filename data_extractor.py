import requests
import pandas as pd

def main():
    # URL for World Cup player statistics on FBref
    url = 'https://fbref.com/en/comps/1/stats/World-Cup-Stats'
    
    # Standard Chrome User-Agent header to prevent 403 Forbidden errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Fetch the HTML content
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        
        # Extract tables from the raw HTML using Pandas
        tables = pd.read_html(response.text)
        
        if not tables:
            print("No tables found at the specified URL.")
            return

        # Target the primary player statistics table (index 0)
        df = tables[0]

        # Flatten multi-level column headers if present
        if isinstance(df.columns, pd.MultiIndex):
            new_cols = []
            for col in df.columns:
                # Filter out 'Unnamed' levels which are common in pandas read_html multi-indexes
                cleaned_levels = [str(level).strip() for level in col if 'Unnamed' not in str(level)]
                # Join the remaining levels with an underscore
                new_cols.append('_'.join(cleaned_levels))
            df.columns = new_cols
        else:
            # Strip whitespace if it's a single level index
            df.columns = [str(col).strip() for col in df.columns]

        # Save the resulting DataFrame to a CSV file without the index
        output_file = 'raw_wc_player_stats.csv'
        df.to_csv(output_file, index=False)

        # Print a success message displaying the total number of rows extracted
        print(f"Success! Extracted {len(df)} rows and saved to {output_file}.")

    except requests.exceptions.RequestException as e:
        # Basic try-except error handling for the network request
        print(f"Error fetching data from the URL: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
