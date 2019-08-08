# pygen
## Static Python-based HTML page generation

Call using `py generate.py` or `generate.bat` to output to a log file instead of the console (on Windows)

Files and directories that start with `.` will not be generated (such as `.include/`), but can still be included from other files.

### .py.html files

Include other files with `<include src="..." />`. Included `.py.html` files will be evaluated and processed before being pasted in.

Integrate Python code using `<py> ... </py>`, `<code py> ... </code py>`, or `<pre py> ... </pre py>` (`code` and `pre` will behave nicer with automated HTML formatting). Call `print(...)` to write to the output `.html` file.

Output short snippets using ``#`...```, which is equivalent to `print(...)`.

Include larger Python scripts with `<py src="..." />`.

### genutils

Python execution inside `.py.html` files can always use the `genutils` package (`genutils/__init__.py`).

Simple elements can be constructed with `element(tag, content, kwargs...)` (ex. `element('div', 'Hello', style='font-weight:bold', width='100')`)

More complex elements can be constructed using template files with `template(path, vars)`. The output will replace `$key` in the original text with the appropriate value for each key in `vars`.

A `vars` dictionary can be gotten from an `.info` file using `get_vars(path)`.

### .info files

`.info` files contian key-value pairs as lines that look like `key : value`, or `key : {value}` for multi-line values.

Multiple values for the same key will result in a list for the dictionary entry instead of a single value.