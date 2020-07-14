## moodle-moss ##
`moodle-moss.py` is a single-command script to run the [Moss](https://theory.stanford.edu/~aiken/moss/) code plagiarism detection tool on a downloaded submission file from the Moodle LMS.

`moodle-moss` takes a zip file from Moodle's "Download all submissions" feature, recursively extracts student code from zip files, makes some effort to redact student names from their submissions, submits the code to Moss, downloads the results, and generates a de-anonymized index page with students clustered by similar submissions and a graphical indicator of code similarity for easy visual inspection.

### Installation ###
`moodle-moss` is written in Python 3, and requires the following packages (installable via `pip`):
- `beautifulsoup4` (HTML parsing)
- `tqdm` (progress bars)
- `yattag` (HTML creation)
- `moodle-moss` also contains a vendored version of [`moss.py`](https://github.com/soachishti/moss.py), modified to support upload and download progress bars (included, no need for installation).

After downloading `moodle-moss`, you should replace `userid = None` in `param.py` with `userid = 1234567` (where `1234567` is replaced with your own Moss user ID.) A Moss user ID can be acquired according to the regisration instructions on the [homepage](https://theory.stanford.edu/~aiken/moss/), your individual user ID can be found in the `$userid` variable in the provided Perl script.

There is as-yet no install script for `moodle-moss` itself (_pull requests welcome from more experienced Pythonistas_).

### Usage ###
1. Download the assignment zip file from Moodle using the "Download all submissions" option in the assignment administration menu (gear in the upper-left corner of the assignment page).
2. From the directory where `moodle_moss` is located, run `./moodle_moss.py path/to/submission/assn7.zip`.
3. `moodle_moss` will extract the assignment files under `path/to/submission/sub/`, with de-anonymization information in `path/to/submission/student_names.txt` and Moss results under `path/to/submission/moss/`
4. Summary results can be viewed by opening `path/to/submission/moss/index.html` in any modern web browser.

User-configurable parameters are in `param.py` in Python syntax; the following values are configurable:
- **userid** - Moss user ID for submissions (should be an integer value)
- **threshold** - Minimum code-similarity percentage for clustering results (should be an integer value, default 25)
- **source_ext** - a dictionary of source-code file extensions, mapped to their Moss language value. Moss language values are in the `@languages` array of the Moss-provided `moss.pl` script (The `ascii` language code works for non-Moss-supported languages). `moodle-moss` automatically picks the language belonging to the most files in the submission.
- **ignore_ext** - list of file extensions expected to occur in submissions which should not be submitted to Moss (e.g. images, documentation, source control files).
- **ignore_dirs** - list of directories to skip in student submissions (e.g. source control, trash files)

Any submission files which are not included in either `source_ext`, `ignore_ext`, or `ignore_dirs` will result in a warning. By default, such a warning ends the script before submission to Moss, allowing the user to modify the student code in the `sub/` directory to fix the errors. If you wish to ignore the warnings and proceed to Moss submission, enter any string starting with 'y' at the prompt. The directories in `sub/` will be named after the numeric code in the original `Student Name_123456_assignsubmission_file_` directory (this mapping also exists in `student_names.txt`). Re-running `./moodle_moss.py path/to/submission/assn7.zip` or `./moodle_moss.py path/to/submission/` will detect the existing `sub/` directory and proceed to submitting it to Moss.

### Contributing ###
`moodle_moss` is licensed under the MIT licence (see `LICENCE`); pull requests and bug reports are welcome, contributors assert that they are legally permitted to assign copyright on contributed code and assent to its release under the MIT licence of the project.