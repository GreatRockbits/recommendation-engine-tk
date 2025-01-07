import json
import os
import re
import gzip

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Creates a new metadata_processed.json file with valid JSON format.'

    def handle(self, *args, **options):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'metadata.json.gz')
        output_file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'metadata_processed.json')

        try:
            with gzip.open(input_file_path, 'r') as g, open(output_file_path, 'w') as f:
                f.write('[')  # Write the opening bracket for the array

                first_line = True  # Flag to track the first line
                for line in g:
                    try:
                        # Use eval to parse the object (keeping eval as requested)
                        obj = eval(line.decode('utf-8'))  
                        
                        # Add a comma before the object except for the first one
                        if not first_line:
                            f.write(',' + '\n')
                        first_line = False

                        # Write the JSON object to the output file
                        f.write(json.dumps(obj)) 

                    except Exception as e:  # Catch any errors during eval
                        self.stderr.write(self.style.ERROR(f"Error evaluating object: {e} - Line: {line}"))

                f.write(']')  # Write the closing bracket for the array

            self.stdout.write(self.style.SUCCESS(f'Successfully processed data from {input_file_path} to {output_file_path}'))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"Error: Input file '{input_file_path}' not found."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))