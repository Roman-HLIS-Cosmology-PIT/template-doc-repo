# This code was written by ChatGPT for the Roman HLIS Cosmolgy PIT
# Delverable Reports document at 
# https://github.com/Roman-HLIS-Cosmology-PIT/deliverable-reports-pipeline
# with modifications by Dida Markovic, June 2025
#
# You may need to do `conda install bibtexparser` before running.
# Run simply with `python clean_bib.py`.

import re
from collections import defaultdict
from pathlib import Path

# Load your .bib file
input_file = "references_messy.bib"
output_file = "references.bib"

with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# Extract @ARTICLE entries
article_entries = re.findall(r'@ARTICLE{.*?\n}\n', content, flags=re.DOTALL)
non_articles = re.sub(r'@ARTICLE{.*?\n}\n', "", content, flags=re.DOTALL)

# Clean up the top of the file
topstr = "% PASTE NON-PAPER REFS HERE AT THE TOP IN ALPHABETICAL ORDER"
bottomstr = "% PASTE JOURNAL ARTICLES BELOW IN ALPHABETICAL ORDER AS SPECIFIED AT THE START OF THE FILE"
file_header, top_lines = non_articles.split(topstr)
top_entries, section_spearators = top_lines.split(bottomstr)
#non_articles = "\n".join(line for line in top_entries.splitlines() if line.strip())
non_articles = f"{file_header}{topstr}{top_entries}{bottomstr}"

# Extract author and year for sorting and renaming
def extract_info(entry):
    author_match = re.search(r'author\s*=\s*{{([^}]+)}', entry)
    year_match = re.search(r'year\s*=\s*(\d{4})', entry)
    if not author_match or not year_match:
        key = re.search(r'@ARTICLE{([^,]+),',entry)
        print('ERROR for '+key.group(1))
        return "Unknown", "0000"
    #print('NO ERR for '+author_match.group(1)+year_match.group(1))
    first_author = author_match.group(1).split(",")[0].strip().strip("{")
    year = year_match.group(1)
    return first_author, year

# Prepare entries for renaming and sorting
key_counter = defaultdict(list)
parsed_entries = []

for i,entry in enumerate(article_entries):
    author, year = extract_info(entry)
    key_base = f"{author}{year}"
    key_base = "".join(key_base.split(" "))
    key_base = key_base.replace("TheLSSTDarkEnergyScienceCollaboration","DESC")
    key_base = key_base.replace("Collaboration","")
    if '{' in key_base or '\\' in key_base:
        key_base = key_base.replace("{","")
        key_base = key_base.replace("\\","")
        print('ERROR: '+key_base+' needs manual checking!')
    
    # Now append a,b,c if same first author in same year
    key_counter[key_base].append(i)
    if len(key_counter[key_base])==2: # Add "a" to the first repetition if needed
        rep_ind = key_counter[key_base][0]
        parsed_entries[rep_ind][1] = f"{parsed_entries[rep_ind][1]}a"
    suffix = chr(96 + len(key_counter[key_base])) if len(key_counter[key_base]) > 1 else ""
    new_key = f"{key_base}{suffix}"
    parsed_entries.append([author.lower(), new_key, entry.strip()])

# Sort by author
parsed_entries.sort(key=lambda x: x[0])

# Format and align
def align_entry(entry, new_key):
    entry = re.sub(r'@ARTICLE{[^,]+,', f"@ARTICLE{{{new_key},", entry, count=1)
    lines = entry.splitlines()
    header = lines[0]
    body = lines[1:]
    kv_pairs = []
    for line in body:
        match = re.match(r'\s*([a-zA-Z]+)\s*=\s*(.*)', line)
        if match:
            key, val = match.groups()
            kv_pairs.append((key.strip(), val.strip()))
        else:
            kv_pairs.append(("", line.strip()))
    max_len = max((len(k) for k, v in kv_pairs if k), default=0)
    aligned = []
    for key, val in kv_pairs:
        if key:
            padding = " " * (max_len - len(key))
            aligned.append(f"       {key}{padding} = {val}")
        else:
            aligned.append(f"       {val}")
    return "\n".join([header] + aligned)

# Group by first letter and assemble
output_sections = []
grouped = defaultdict(list)
for author, new_key, entry in parsed_entries:
    first_letter = author[0].upper()
    grouped[first_letter].append(align_entry(entry, new_key))

for letter in sorted(grouped):
    section = f"\n%%%%%%%%%%%%%%%%%%%%%%%%%%%% {letter}{letter}{letter}\n\n"
    section += "\n\n".join(grouped[letter])
    output_sections.append(section)

# Final output
final_content = non_articles.strip() + "\n\n" + "\n\n".join(output_sections)
with open(output_file, "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"Cleaned .bib file saved as {output_file}")
