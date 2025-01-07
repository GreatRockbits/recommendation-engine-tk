import json
import os
import re
import gzip

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Creates a new metadata_processed.json file with single quotes replaced in the JSON structure.'

    def handle(self, *args, **options):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'metadata.json.gz')
        output_file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'metadata_processed.json')

        def parse(path):
            try:
                with gzip.open(path, 'r') as g:
                    # Read the entire file content
                    file_content = g.read().decode('utf-8')  # Decode if needed

                    # Split the content into individual JSON objects
                    json_objects = file_content.strip().split('\n')

                    for obj in json_objects:
                        try:
                            # Use eval to parse the object
                            yield json.dumps(eval(obj)) + '\n'
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"Error evaluating object: {e} - Object: {obj}"))

            except FileNotFoundError:
                self.stderr.write(self.style.ERROR(f"Error: Input file '{input_file_path}' not found."))
                return
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))
                return

        try:
            with open(output_file_path, 'w') as f:
                for l in parse(input_file_path):
                    f.write(l)
            self.stdout.write(self.style.SUCCESS(f'Successfully wrote data from {input_file_path} to {output_file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred while writing to the output file: {e}"))