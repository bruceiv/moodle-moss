# Parameters to modify

# MOSS user id
userid = None
# Threshold for percent similarity to include in summary report
threshold = 25
# Extensions of valid source file types, mapped to corresponding MOSS language
source_ext = {
    ".c": "c", 
    ".cpp": "cc", 
    ".h": "c", 
    ".hpp": "cc", 
    ".hs": "haskell", 
    ".java": "java", 
    ".rs": "ascii", # not supported by MOSS
    }
# Extensions of files to ignore
ignore_ext = {".bluej", ".bmp", ".class", ".css", ".ctxt", ".doc", ".docx", ".ds_store", "element-list", ".gif", ".heic", ".html", ".jpg", ".jpeg", ".js", "package-list", ".pages", ".pdf", ".pkg", ".pkh", ".png", ".prefs", ".rels", ".svg", ".txt", ".xml"}
# Directories that shouldn't be processed
ignore_dirs = {".git", "__MACOSX", "META-INF"}
