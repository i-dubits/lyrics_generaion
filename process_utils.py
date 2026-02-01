#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import re
from collections import Counter
import json
from difflib import SequenceMatcher

class LyricsPreprocessor:
    def __init__(self, root_path, output_path):
        '''
        Initialize LyricsPreprocessor
        
        Args:
            root_path (str):   directory containing the folders with albums
            output_path (str): directory where processed data will be saved
            
        Attrs:
            count_errors (int): counter for processing errors
            count_ok (int): counter for successful processings
        '''
            
        self.root_path = root_path
        self.output_path = output_path
        self.count_errors = 0
        self.count_ok = 0

    def preprocess_files(self):
        '''
        Initial files processing
        
        Checks if the file contains verses and places all successfully processed files to new folder
        Removes the line above verses
        '''
        if os.path.exists(self.root_path):
            # Iterate through all the folders
            for folder_path in glob.glob(os.path.join(self.root_path, '*')):
                folder_name = os.path.basename(folder_path)
                output_folder_path = os.path.join(self.output_path, folder_name)
                
                # Create the corresponding folder in the output directory
                os.makedirs(output_folder_path, exist_ok=True)
                txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
                
                # Check if there are any .txt files in the folder
                if txt_files:
                    for txt_file_path in txt_files:
                        file_name = os.path.basename(txt_file_path)
                        output_file_path = os.path.join(output_folder_path, file_name)
                        with open(txt_file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        content = re.sub(r'\[Verse 1:.*?\]', '[Verse 1]', content)
                        index = content.find('[Verse 1]')
                        
                        # If '[Verse 1]' is found, clean the content
                        if index != -1:
                            cleaned_content = content[index:]
                            
                            # Write the cleaned content to the corresponding file in the output directory
                            with open(output_file_path, 'w', encoding='utf-8') as file:
                                file.write(cleaned_content)
                            self.count_ok += 1
                        else:
                            print(f"Skipped file (no '[Verse 1]' found): {txt_file_path}")
                            self.count_errors += 1
                else:
                    print(f"No .txt files found in folder: {folder_path}")
        else:
            print(f"Root directory does not exist: {self.root_path}")

    
    @staticmethod
    def similarity_ratio(str1, str2):
        '''
        Calculate similarity of two strings
        
        Args:
            str1 (str): first string
            str2 (str): second string
        '''
        seq_matcher = SequenceMatcher(None, str1, str2)
        return seq_matcher.ratio()

    @staticmethod
    def normalize_content(content):
        '''
        Normalize string before comparison
        
        Removes special characters, replaces all whitespace characters to one space
        and makes the sting lowercased
        
        Args:
            content (str): input string
        '''
            
        content = re.sub(r'[^\w\s]', '', content)
        content = ' '.join(content.split())
        return content.lower()
    
    def find_duplicates(self, threshold=0.1):
        '''
        Find strings which similarity exceeds some threshold
        
        Iterates over different albums, assumes that all texts inside one album are different
        
        Args:
            threshold (float): threshold value
        '''
        # Iterate over each subfolder in the main folder
        subfolders = [folder for folder in glob.glob(os.path.join(self.output_path, '*'))]
        for i in range(len(subfolders)):
            txt_files = {}
            for txt_file_path in glob.glob(os.path.join(subfolders[i], '*.txt')):
                with open(txt_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    content = self.normalize_content(content)
                    txt_files[txt_file_path] = content

            files_to_delete = []
            # Compare files in the current subfolder with files in all other subfolders
            for j in range(i + 1, len(subfolders)):
                for other_txt_file_path in glob.glob(os.path.join(subfolders[j], '*.txt')):
                    with open(other_txt_file_path, 'r', encoding='utf-8') as other_file:
                        other_content = other_file.read()
                        other_content = self.normalize_content(other_content)
                    for txt_file_path, content in txt_files.items():
                        ratio = self.similarity_ratio(content, other_content)
                        # If the ratio is above the threshold, mark the file for deletion
                        if ratio >= threshold:
                            files_to_delete.append(other_txt_file_path)
                            print(f"Marked identical file for removal: {other_txt_file_path}")
            # Remove the marked files
            for file_path in files_to_delete:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")

    @staticmethod
    def delete_empty_dirs(directory):
        '''Delete empty folders'''
        for dirpath, dirnames, files in os.walk(directory, topdown=False):
            if not dirnames and not files:
                try:
                    os.rmdir(dirpath)
                    print(f"Removed empty directory: {dirpath}")
                except OSError as e:
                    print(f"Error while deleting directory {dirpath}: {e}")
    
    @staticmethod
    def delete_duplicate_first_word_files(directory):
        '''
        Delete song texts which has the same word in its name inside one album (folder)

        Keeps the first occurrence (alphabetically) of each first word and deletes subsequent duplicates

        Args:
            directory (str): path to folder
        '''
        for dirpath, dirnames, files in os.walk(directory):
            txt_files = sorted([f for f in files if f.endswith('.txt')])
            seen_first_words = set()

            for f in txt_files:
                first_word = os.path.splitext(f)[0].split('_')[0].lower()

                if first_word in seen_first_words:
                    # This is a duplicate - delete it
                    try:
                        os.remove(os.path.join(dirpath, f))
                        print(f"Removed duplicate file: {os.path.join(dirpath, f)}")
                    except OSError as e:
                        print(f"Error while deleting file {os.path.join(dirpath, f)}: {e}")
                else:
                    # First occurrence - keep it
                    seen_first_words.add(first_word)

    @staticmethod
    def extract_data_from_file(file_path):
        '''
        Helper for dataset generation
        
        Put two first paragrpahs to text and the remaining to summary (summarization task notation)
        
        Args:
            file_path (str): path to file
        
        '''
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            first_bracket = content.find('[')
            second_bracket = content.find('[', first_bracket + 1)
            if second_bracket == -1 or content.find('[', second_bracket + 1) == -1:
                return None
            text = content[:content.find('[', second_bracket + 1)].strip()
            summary = content[content.find('[', second_bracket + 1):].strip()
            return {
                'text': text,
                'summary': summary
            }

    def generate_dataset(self):
        '''Genearate dataset from lyrics'''
        dataset = []
        count = 0
        for root, _, files in os.walk(self.output_path):
            for file in files:
                if file.endswith('.txt'):
                    data = self.extract_data_from_file(os.path.join(root, file))
                    if data:
                        count+=1
                        dataset.append(data)
        print(f'Number of itemrs in dataset: {count}')
        return dataset

    @staticmethod
    def save_as_json(dataset, output_file):
        '''Save dataset as json file'''
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=4)
