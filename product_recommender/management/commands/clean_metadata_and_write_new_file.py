import json
import os
import re

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Creates a new metadata_processed.json file with single quotes replaced in the JSON structure.'

    def handle(self, *args, **options):
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__)) 

        # Construct the relative path to metadata.json
        input_file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'metadata.json')
        output_file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'metadata_processed.json') 

        with open(input_file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
            row_count = 0
            for line in infile:
                if row_count >= 100:
                    break  # Stop after processing 100 rows

                # 1. Handle leading double quotes in titles/descriptions
                line = re.sub(r"({'title': |'description': )\"", r"\1'", line)

                # 2. Replace remaining double quotes with a rare character (e.g., Ϯ)
                line = line.replace('"', 'Ϯ') 

                # 3. Replace single quotes with double quotes
                line = re.sub(r"((?<={)\s*\'|(?<=,)\s*\'|\'\s*(?=:)|(?<=:)\s*\'|\'\s*(?=,)|\'\s*(?=[}\]])|(?<=[\[{])\s*\'|\'\s*(?=[\[{]))", '"', line)

                # 4. Replace the rare character with escaped double quotes (using regex)
                line = re.sub(r'Ϯ', r'\\"', line)  

                outfile.write(line)

                row_count += 1  # Increment the row count

        self.stdout.write(self.style.SUCCESS('Successfully created metadata_processed.json'))