from datetime import datetime
import os
 

def log_search(query, detected_label, log_file_path):
    log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Query: {query}, Detected: {detected_label}\n"
    with open(log_file_path, "a") as log_file:
        log_file.write(log_entry)



