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
                    for l in g:
                        yield json.dumps(eval(l)) + '\n'
            except FileNotFoundError:
                self.stderr.write(self.style.ERROR(f"Error: Input file '{input_file_path}' not found."))
                return
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))
                return

        try:
            with open(output_file_path, 'w') as f:
                for l in parse(input_file_path):
                    f.write(l + '\n')
            self.stdout.write(self.style.SUCCESS(f'Successfully wrote data from {input_file_path} to {output_file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred while writing to the output file: {e}"))