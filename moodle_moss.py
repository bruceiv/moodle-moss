#!/usr/bin/python3

# Runs Moss on a Moodle submission file
# 
# Usage:
#   ./moodle_moss.py <moodle_zip_file>
#
# Installation Requirements:
# - Python 3
# - beautifulsoup4 (HTML parsing):
#     pip3 install beautifulsoup4
# - mosspy (Python wrapper for MOSS webservice):
#     [modified version vendored with distribution]
# - tqdm (progress bars):
#     pip3 install tqdm
# - yattag (HTML creation):
#     pip3 install yattag

from bs4 import BeautifulSoup
from collections import defaultdict
import logging
import moss_index
import mosspy
import os
import param
import re
import shutil
import sys
from tqdm import tqdm
from uf import union_find
import zipfile

# flatten the directory src into dst
def flattendir(dst, src):
    src_path = os.path.join(dst, src)
    for f in os.listdir(src_path):
        f_path = os.path.join(src_path, f)
        if os.path.isdir(f_path):
            if f in param.ignore_dirs:
                # shouldn't be processed
                shutil.rmtree(f_path)
                continue
            # recursively flatten
            flattendir(dst, os.path.join(src, f))
        else:
            # move to target dir, prefixing with path if needed
            dst_path = os.path.join(dst, f)
            if os.path.isfile(dst_path):
                long_name = os.path.normpath(f_path).replace(os.sep, "_")
                dst_path = os.path.join(dst, long_name)
                if os.path.isfile(dst_path):
                    print("warning: name collision - deleting file", f_path)
                    global warnings
                    warnings = True
                    os.remove(f_path)
                    continue
            shutil.move(f_path, dst_path)
    os.rmdir(src_path)

def getfileext(filename):
    (f,e) = os.path.splitext(filename)
    if len(e) == 0:
        e = f
    return e.lower()

# Find target directory and unzip Moodle zip file into sub/ as needed

if len(sys.argv) < 2:
    print("usage:", sys.argv[0], "<moodle_file>")
    exit(1)

target = sys.argv[1]
title = ""

if os.path.isdir(target):
    # assume this is a directory containing a pre-expanded submission directory
    target_dir = target
    sub_dir = os.path.join(target_dir, "sub")
    if not os.path.isdir(sub_dir):
        print("invalid target, doesn't have sub/ directory:", target)
        exit(1)
elif zipfile.is_zipfile(target):
    # extract title from zipfile name
    (title, _) = os.path.splitext(os.path.basename(target))
    # assume this is a Moodle-download of all assignments
    target_dir = os.path.dirname(target)
    sub_dir = os.path.join(target_dir, "sub")
    if not os.path.isdir(sub_dir):
        os.mkdir(sub_dir)
        with zipfile.ZipFile(target, 'r') as zip_ref:
            zip_ref.extractall(sub_dir)
else:
    print("invalid target - not a directory or zip file:", target)
    exit(1)

# extract and anonymize student submissions

students = {}
languages = {}
moss_lang = "ascii"

# load previous mappings, if present
map_path = os.path.join(target_dir, "student_names.txt")
if os.path.isfile(map_path):
    with open(map_path, "r") as map_file:
        for ln in map_file.readlines():
            segs = ln.split(None, 1)
            if len(segs) != 2:
                print("warning: invalid mapfile line `", ln, "`")
                continue
            students[segs[0]] = segs[1].rstrip()
    if "language" in students:
        moss_lang = students.pop("language")
    if "title" in students:
        assn_title = students.pop("title")

warnings = False
for student_dir in os.listdir(sub_dir):
    # skip already-processed nodes
    if student_dir in students:
        continue
    
    # skip non-directories
    student_path = os.path.join(sub_dir, student_dir)
    if not os.path.isdir(student_path):
        print("warning: skipping non-directory:", student_dir)
        warnings = True
        continue
    
    # extract student name and submission key
    segs = student_dir.split("_", 2)
    if len(segs) == 3:
        students[segs[1]] = segs[0]
        names = segs[0].split()
        sub_key = segs[1]
    else:
        print("warning: not Moodle dir:", student_dir)
        warnings = True
        students[student_dir] = student_dir
        names = [student_dir]
        sub_key = student_dir
    
    # expand all zip files in submission, deleting afterward
    # zip files may be nested inside other zip files, these should be recursively unzipped
    zip_paths = [student_path]
    zip_index = 0
    while zip_index < len(zip_paths):
        student_path = zip_paths[zip_index]
        zip_index += 1

        for path, dirs, files in os.walk(student_path):
            for student_file in files:
                file_path = os.path.join(path, student_file)
                if not zipfile.is_zipfile(file_path):
                    continue
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(path)
                zip_paths.append(path) # mark path as possibly containing zip files
                os.remove(file_path)

    # flatten directory hierarchy
    for student_file in os.listdir(student_path):
        file_path = os.path.join(student_path, student_file)
        if not os.path.isdir(file_path):
            continue
        if student_file in param.ignore_dirs:
            # shouldn't be processed
            shutil.rmtree(file_path)
            continue
        flattendir(student_path, student_file)
    
    # redact student names from submission
    for student_file in os.listdir(student_path):
        file_path = os.path.join(student_path, student_file)
        ext = getfileext(student_file)
        if ext in param.source_ext:
            # tally language for Moss
            lang = param.source_ext[ext]
            if lang in languages:
                languages[lang] += 1
            else:
                languages[lang] = 1
            
            # redact student name from file
            with open(file_path, 'r') as f:
                try:
                    redacted = f.read()
                except UnicodeDecodeError as e:
                    print("ERROR processing", file_path)
                    warnings = True
                    print(e)
                    continue
            for n in names:
                redacted = redacted.replace(n, 'REDACTED')
            with open(file_path, 'w') as f:
                f.write(redacted)
            continue
        elif ext in param.ignore_ext:
            # ignore irrelevant files
            continue
        else:
            print("warning: unknown file:", file_path)
            warnings = True
            continue
    
    # rename top-level directory to anonymize
    if sub_key != names[0]:
        new_dir = os.path.join(sub_dir, sub_key)
        if os.path.exists(new_dir):
            print("warning: deleting duplicate path:", student_path)
            warnings = True
            shutil.rmtree(student_path)
        else:
            os.rename(student_path, new_dir)

# save student mapping
with open(map_path, "w") as map_file:
    for k,v in students.items():
        print(k, v, file=map_file)
    # calculate and save MOSS language
    if len(languages) > 0:
        moss_lang = max(languages, key=languages.get)
    print("language", moss_lang, file=map_file)
    # save title
    if title:
        print("title", title, file=map_file)

if warnings:
    answer = input("Continue despite warnings? [y/N] ")
    if (not answer) or (answer[0].lower() != 'y'):
        exit(0)

# submit student code to Moss
moss_dir = os.path.join(target_dir, "moss")
report_path = os.path.join(moss_dir, "report.html")
if not os.path.isdir(moss_dir):
    os.mkdir(moss_dir)

    moss = mosspy.Moss(param.userid, moss_lang)
    moss.setDirectoryMode(1)

    for student_dir in students:
        student_path = os.path.join(sub_dir, student_dir)
        # find student submission files
        for student_file in os.listdir(student_path):
            file_path = os.path.join(student_path, student_file)
            ext = getfileext(student_file)
            if ext in param.source_ext:
                moss.addFile(file_path)

    # submit to MOSS
    progress = tqdm(desc="  Uploading", total=len(moss.files) + len(moss.base_files))
    moss_url = moss.send(lambda fp, dn: progress.update())
    progress.close()
    moss.saveWebPage(moss_url, report_path)
    
    # download reports
    n_students = len(students)
    max_matches = n_students*(n_students-1)/2 # n choose 2
    def update_match(url):
        progress.update()
        global max_matches
        max_matches -= 1
    
    progress = tqdm(desc="Downloading", total=max_matches)
    mosspy.download_report(moss_url, os.path.join(moss_dir, "report/"), connections=8, log_level=logging.WARNING, on_read=update_match)
    progress.update(max_matches)
    progress.close()

# build summary report

vals = re.compile(r'sub/(\d+)/ \((\d+)%\)')
pages = re.compile(r'match\d+\.html')
clusters = union_find()
results = defaultdict(list)

class moss_result:
    def __init__(self, c0, n0, c1, n1, s, p):
        self.code0 = c0
        self.name0 = n0
        self.code1 = c1
        self.name1 = n1
        self.similarity = s
        self.page = p

with open(report_path) as r:
    report = r.read()

soup = BeautifulSoup(report, 'lxml')
for row in soup.find_all('tr'):
    cells = row.find_all('a')
    # skip rows that don't match the three-column format
    if len(cells) != 2:
        continue
    # extract similarity match
    vals0 = vals.search(cells[0].string)
    vals1 = vals.search(cells[1].string)
    page0 = pages.search(cells[0]['href'])
    if vals0 == None or vals1 == None or page0 == None:
        continue
    similarity0 = int(vals0.group(2))
    similarity1 = int(vals1.group(2))
    similarity = max(similarity0, similarity1)
    page = page0.group()
    # get student names for anon codes
    code0 = vals0.group(1)
    code1 = vals1.group(1)
    name0 = students.get(code0, code0)
    name1 = students.get(code1, code1)
    # add moss result to results list
    results[code0].append(moss_result(code0, name0, code1, name1, similarity, page))
    # skip clustering rows below threshold
    if similarity < param.threshold:
        continue
    clusters.try_insert(code0)
    clusters.try_insert(code1)
    clusters.merge(code0, code1)

# sort clusters by similarity
cluster_matches = []

for root in clusters.roots:
    cluster = clusters.report(root)
    matches = []
    for code in cluster:
        for result in results[code]:
            if result.similarity >= param.threshold:
                matches.append(result)
    matches.sort(key=lambda m: -m.similarity)
    cluster_matches.append((matches, matches[0].similarity))

cluster_matches.sort(key=lambda c: -c[1])

# provide sorted list of all matches
all_matches = []
for per_student in results.values():
    for result in per_student:
        all_matches.append(result)

all_matches.sort(key=lambda m: -m.similarity)

# generate index page for results and write to index.html
index_path = os.path.join(moss_dir, "index.html")
with open(index_path, "w") as index_file:
    index_file.write(moss_index.generate_html(title, cluster_matches, all_matches))
