#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from process_utils import LyricsPreprocessor

root_path = 'data_init'
output_path = 'data_processed'

preprocessor = LyricsPreprocessor(root_path, output_path)
preprocessor.preprocess_files()

print(f'Number of processing errors: {preprocessor.count_errors}')
print(f'Number of successful processings: {preprocessor.count_ok}')

preprocessor.find_duplicates(threshold=0.1)

LyricsPreprocessor.delete_empty_dirs(output_path)
LyricsPreprocessor.delete_duplicate_first_word_files(output_path)
LyricsPreprocessor.delete_empty_dirs(output_path)

dataset_processed = preprocessor.generate_dataset()
output_file = 'dataset_processed.json'

LyricsPreprocessor.save_as_json(dataset_processed, output_file)

