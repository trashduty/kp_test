#!/usr/bin/env python3
"""
Convert spreads_lookup_combined.csv to JSON format for client-side usage.
"""

import csv
import json

def convert_csv_to_json(csv_file, json_file):
    """Convert CSV file to JSON format."""
    data = []
    
    with open(csv_file, 'r') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            # Convert string values to appropriate types
            data.append({
                'total_category': int(row['total_category']),
                'market_spread': float(row['market_spread']),
                'model_spread': float(row['model_spread']),
                'cover_prob': float(row['cover_prob']),
                'push_prob': float(row['push_prob']),
                'not_cover_prob': float(row['not_cover_prob'])
            })
    
    # Write to JSON file
    with open(json_file, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    
    print(f"Successfully converted {csv_file} to {json_file}")
    print(f"Total records: {len(data)}")

if __name__ == '__main__':
    csv_file = 'spreads_lookup_combined.csv'
    json_file = 'docs/spreads_lookup_combined.json'
    convert_csv_to_json(csv_file, json_file)
