# How to Run the Application Locally

## Setup Instructions

1. **Clone or download this repository**

2. **Install required dependencies using**
`pip install -r requirements.txt`
3. **Get an SEA-LION API key following the guide from https://docs.sea-lion.ai/guides/inferencing/api**
4. **Run the application with the following syntax:**

`book_translation.py --language {indonesian,filipino,tamil,thai,vietnamese} [--api-key API_KEY] [--output OUTPUT]`

For example, a valid syntax would be:
`python book_translation.py --language tamil --api-key sk-xxxxxxxxxxxxxxxxxxx`

The argument of api-key and language is compulsory, whereas the output argument is optional, representing the name of the output file, and can be represented by "some_text.txt" for example. 

You may run `book_translation.py -h` to display the help message in the terminal.

5. **You will find a new directory named "output" with a translated txt file inside.**

## DISCLAIMER: The logging, exceptions/errors, argument parsing, the definition of functions, and single line comments are done by ChatGPT. The main logic of the functions and classes are mostly implemented by me (download_book is done by ChatGPT however).

