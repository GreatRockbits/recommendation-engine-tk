import json
import os
import re

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Creates a new metadata_processed.json file with single quotes replaced in the JSON structure.'

    def handle(self, *args, **options):
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Construct the input and output file paths
        input_file_path = os.path.join(project_root, 'data_files', 'metadata.json') 
        output_file_path = os.path.join(project_root, 'data_files', 'metadata_processed.json') 

        with open(input_file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
            for line in infile:
                # Use regex to replace single quotes in JSON structure
                line = re.sub(r"(\s*)'([^':]+)'(\s*):", r'\1"\2"\3:', line)  
                line = re.sub(r"(\s*)'([^']+)'(\s*[,}])", r'\1"\2"\3', line)
                outfile.write(line)

        self.stdout.write(self.style.SUCCESS('Successfully created metadata_processed.json'))