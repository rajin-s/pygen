import re

from io import StringIO
import sys
from textwrap import dedent, indent

from os import listdir
from os.path import isdir, join, dirname

from genutil import *

gen_dir = "."
out_dir = ".."

gen_ext = ".py.html"
out_ext = ".html"

# More easily readable regex patterns used in preprocessing
# Two spaces -> one or more whitespace
# One space  -> zero or more whitespace
class pattern_text:
    all_text   = "[\\s\\S]+?"
    local_text = ".+?"

    preprocess = f'<include  src = "({local_text}{re.escape(gen_ext)})" />'
    include    = f'<include  src = "({local_text})" />'

    python_include       = f'<py  src = "({local_text})" />'
    python_block_tag     =  'py|pre py|code py'
    python_block_tag_end =  'py|pre|code'
    
    python_block     = f'<(?:{python_block_tag})>({all_text})</(?:{python_block_tag_end})>'
    python_snippet   = f'(?://)?#`({local_text})`'

# Convert a readable pattern to regex
def to_regex(text):
    return text.replace("  ", "\\s+").replace(" ", "\\s*").replace("/", "\\/")

# Regular expressions used for preprocessing
# note: python patterns grouped together since all need to be parsed in order regardless of type
class pattern:
    # preprocess = re.compile( f"({to_regex(pattern_text.preprocess)})" )
    include    = re.compile( f"({to_regex(pattern_text.include)})" )

    # Any python include / block / snippet / preprocessed include
    # note: match is (original, include_path, block_text, snippet_text)
    python_any = re.compile( f"({to_regex(pattern_text.python_include)}|{to_regex(pattern_text.python_block)}|{to_regex(pattern_text.python_snippet)}|{to_regex(pattern_text.preprocess)})" )

# Process some text
# note: prevent cycles by checking that any includes are not already in the chain
def preprocess(text, cwd, chain, py_globals, py_locals):
    # Do python evaluations and preprocessed includes
    py_elements = re.findall(pattern.python_any, text)
    for (original, include_path, block_text, snippet_text, ppinclude_path) in py_elements:
        exec_text = ""

        # Get python text to execute depending on type of match
        if len(include_path) > 0:
            include_path = join(cwd, include_path)
            exec_text = open(include_path).read()
        elif len(block_text) > 0:
            exec_text = dedent(block_text).strip()
        elif len(snippet_text) > 0:
            exec_text = f"print({snippet_text}, end='')"
        elif len(ppinclude_path) > 0: # Do pre-processed includes (recursively)
            if ppinclude_path in chain:
                print(f"  Cyclic include in {ppinclude_path}!")
                continue
            
            if ppinclude_path.startswith("/"):
                ppinclude_path = "." + ppinclude_path
            else:
                ppinclude_path = join(cwd, ppinclude_path)
            file_text = open(ppinclude_path).read()
            file_text = preprocess(file_text, dirname(ppinclude_path), chain + [ppinclude_path], py_globals, py_locals)
            text = text.replace(original, file_text)

        if len(exec_text) > 0:
            # Redirect standard output to print to the result
            old_stdout = sys.stdout
            sys.stdout = result_text_stream = StringIO()
            try:
                exec(exec_text, py_globals, py_locals)
                sys.stdout = old_stdout
            except Exception as e:
                sys.stdout = old_stdout
                print(f"  error in exec: {e}")
                print(indent(exec_text, "  > "))
            
            text = text.replace(original, result_text_stream.getvalue())
    
    # Do basic includes
    includes = re.findall(pattern.include, text)
    for (original, path) in includes:
        if path.startswith("/"):
            path = "." + path
        else:
            path = join(cwd, path)

        file_text = open(path).read()
        text = text.replace(original, file_text)

    return text

# Get an output template format from file or default
output_template = "$doc"
try:
    output_template = open(".doctemplate.html").read()
    print("Using .doctemplate.html")
except:
    print("No .doctemplate.html given, using default")

# Generate output files for all input files in a directory and recursively traverse subdirectories
def generate(folder):
    for path in listdir(folder):
        full_path = join(folder, path)

        # Skip folders/files that start with . (.import, etc.)
        if path.startswith("."):
            continue

        # Recurse into subdirectories
        if isdir(full_path):
            generate(full_path)
        else:
            # Handle generating files
            if full_path.endswith(gen_ext):
                try:
                    output_path = full_path.replace(gen_dir, out_dir, 1).replace(gen_ext, out_ext)
                    print(f"Processing {path} (out: {output_path})")

                    file_text = open(full_path).read()

                    # Environments to use for python evaluations (potentially modified by each exec call)
                    # note: import functions from genutil for convenience
                    py_globals = {}
                    py_locals = {}
                    exec("from genutil import *", py_globals, py_globals)

                    output_text = preprocess(file_text, folder, [full_path], py_globals, py_locals)
                    output_text = output_template.replace("$doc", output_text)
                    open(output_path, 'w').write(output_text)
                except FileNotFoundError as e:
                    print(f"<!> Output file could not be written, make sure the target directory exists: {e}")
                    continue
                except Exception as e:
                    print(f"<!> An error occurred: {e}")
                    continue
                except:
                    print(f"<!> An error occurred: {sys.exc_info()[0]}")
                    continue

# Start generation in the current directory
generate(".")
print("")
print("Finished generating html")