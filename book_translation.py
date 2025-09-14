"""
Book Translation Application using SEA-LION API

This application downloads and translates the book "The Art of Public Speaking" from Project Gutenberg
to one of the supported Southeast Asian languages using the SEA-LION API.

Supported languages: Indonesian, Filipino, Tamil, Thai, Vietnamese

Author: Book Translator
"""

import os
import sys
import requests
import argparse
import logging
import time
from typing import List, Optional
from openai import OpenAI

# client = OpenAI(api_key="sk-Q5kerfMhzqVUq2K0RKdL9g", base_url="https://api.sea-lion.ai/v1")
# models = client.models.list()
# print(models)

# SyncPage[Model](data=[Model(id='aisingapore/Llama-SEA-LION-v3.5-70B-R', created=1677610602, object='model', owned_by='openai'), 
# Model(id='aisingapore/Llama-SEA-LION-v3.5-8B-R', created=1677610602, object='model', owned_by='openai'), 
# Model(id='aisingapore/Gemma-SEA-LION-v3-9B-IT', created=1677610602, object='model', owned_by='openai'), 
# Model(id='aisingapore/Llama-SEA-LION-v3-70B-IT', created=1677610602, object='model', owned_by='openai'), 
# Model(id='swiss-ai/Apertus-8B-Instruct-2509', created=1677610602, object='model', owned_by='openai'), 
# Model(id='swiss-ai/Apertus-70B-Instruct-2509', created=1677610602, object='model', owned_by='openai'), 
# Model(id='aisingapore/Gemma-SEA-LION-v4-27B-IT', created=1677610602, object='model', owned_by='openai'), 
# Model(id='aisingapore/Llama-SEA-Guard-Prompt-v1', created=1677610602, object='model', owned_by='openai'), 
# Model(id='BAAI/bge-m3', created=1677610602, object='model', owned_by='openai')], object='list')


# I have previously ran this chunk of code above to find out the list of models, and from https://docs.sea-lion.ai/models/sea-lion-v4, 
# I would be using the latest Gemma-SEA-LION-v4-27B-IT which "is suited for knowledge-intensive tasks, 
# and for high-demand contexts where comprehensive language comprehension are essential."


class BookTranslator:
    """
    A class to handle book translation using the SEA-LION API.
    """
    
    # As per requirement, this translation supports Indonesian, Filipino, Tamil, Thai and Vietnamese
    SUPPORTED_LANGUAGES = {
        'indonesian': 'Indonesian',
        'filipino': 'Filipino',
        'tamil': 'Tamil',
        'thai': 'Thai',
        'vietnamese': 'Vietnamese'
    }
    
    # Book URL
    # This may not need to be hardcoded; it can be an argument in the constructor below and parsed
    BOOK_URL = "https://www.gutenberg.org/cache/epub/16317/pg16317.txt"
    
    def __init__(self, api_key: str, target_language: str):
        """
        Initialize the BookTranslator.
        
        Args:
            api_key (str): SEA-LION API key
            target_language (str): Target language for translation
        """

        # Model usage justified based on SEA LION documentation as seen above

        # Ideally, the API key should be stored in an .env file, and .gitignore would incloude that .env file to make this API key secure,
        # but I will pass the API key in here through an argument which should be safe as well

        if not api_key:
            raise ValueError("API key is required. Provide it via --api-key argument.")
        
        self.api_key = api_key
        self.target_language = target_language.lower()
        self.model = "aisingapore/Gemma-SEA-LION-v4-27B-IT"
        
        # Validate target language
        if self.target_language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {target_language}. "
                           f"Supported languages: {list(self.SUPPORTED_LANGUAGES.keys())}")
        
        # Initialize OpenAI client with SEA-LION API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.sea-lion.ai/v1"
        )
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def download_book(self) -> str:
        """
        Download the book from Project Gutenberg.
        
        Returns:
            str: The book content as text
        """
        self.logger.info(f"Downloading book from {self.BOOK_URL}")
        
        try:
            response = requests.get(self.BOOK_URL)
            response.raise_for_status()
            
            # Decode content with proper encoding
            content = response.content.decode('utf-8-sig', errors='ignore')
            
            self.logger.info(f"Successfully downloaded book ({len(content)} characters)")
            return content
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to download book: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Clean and prepare text for translation.
        
        Args:
            text (str): Raw text from the book
            
        Returns:
            str: Cleaned text ready for translation
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        # Remove Project Gutenberg header/footer and empty lines
        start_found = False
        
        for line in lines:
            line = line.strip()
            
            # Skip until we find the actual book content
            if not start_found:
                if 'START OF THE PROJECT GUTENBERG' in line.upper():
                    start_found = True
                continue
            
            # Stop when we reach the end
            if 'END OF THE PROJECT GUTENBERG' in line.upper():
                break
            
            # Keep non-empty lines
            if line and not line.startswith('***'):
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        self.logger.info(f"Cleaned text ({len(cleaned_text)} characters)")
        
        return cleaned_text
    
    def split_text(self, text: str, max_chunk_size: int = 3000) -> List[str]:
        """
        Split text into smaller chunks for translation.
        
        Args:
            text (str): Text to split
            max_chunk_size (int): Maximum size of each chunk
            
        Returns:
            List[str]: List of text chunks
        """
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the limit, start a new chunk
            if len(current_chunk) + len(paragraph) + 1 > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += '\n' + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        self.logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def translate_chunk(self, text_chunk: str, chunk_num: int, total_chunks: int) -> str:
        """
        Translate a single chunk of text.
        
        Args:
            text_chunk (str): Text chunk to translate
            chunk_num (int): Current chunk number
            total_chunks (int): Total number of chunks
            
        Returns:
            str: Translated text
        """
        target_lang = self.SUPPORTED_LANGUAGES[self.target_language]
        
        prompt = f"""Please translate the following English text to {target_lang}. 
                    Maintain the original formatting, paragraph structure, and literary style. 
                    Preserve proper nouns and character names appropriately.

                    Text to translate:

                    {text_chunk}"""

        try:
            self.logger.info(f"Translating chunk {chunk_num}/{total_chunks}")
            

            # completion = client.chat.completions.create(
            #     model="aisingapore/Gemma-SEA-LION-v4-27B-IT",
            #     messages=[
            #         {
            #             "role": "user",
            #             "content": "Tell me a Singlish joke!"
            #         }
            #     ]
            # )

            # print(completion.choices[0].message.content)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a professional translator specialising in literary translation to {target_lang}. Maintain the original style and meaning while producing natural, fluent translations."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                # temperature here is set to 0.3 which is low enough to be slightly varied but relatively consistent and is suited for translation
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content
            
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Failed to translate chunk {chunk_num}: {e}")
            # Return original text if translation fails
            return text_chunk
    
    def translate_book(self) -> str:
        """
        Download and translate the entire book.
        
        Returns:
            str: Translated book content
        """
        # Download the book
        book_content = self.download_book()
        
        # Clean the text
        cleaned_content = self.clean_text(book_content)
        
        # Split into chunks
        chunks = self.split_text(cleaned_content)
        
        # Translate each chunk
        translated_chunks = []
        
        for i in range(len(chunks)):
            chunk = chunks[i]
            translated_chunk = self.translate_chunk(chunk, i + 1, len(chunks))
            translated_chunks.append(translated_chunk)

            # Add a small delay between requests to be respectful to the API
            time.sleep(1)
        
        # Combine translated chunks
        translated_book = '\n\n'.join(translated_chunks)
        
        self.logger.info("Translation completed successfully")
        return translated_book
    
    def save_translation(self, translated_text: str, filename: Optional[str] = None) -> str:
        """
        Save the translated book to a file.
        
        Args:
            translated_text (str): Translated book content
            filename (str, optional): Output filename
            
        Returns:
            str: Path to the saved file
        """
        if not filename:
            # Note that the filename here is actually hardcoded. It is possible to not actually hardcode it in this case, 
            # there is Title: The Art of Public Speaking in the text.
            # We could also search through line by line, and do something like 
            # if 'TITLE:' in line.upper():     
            #    title = line.split(":", 1)[1].strip()
            # and filename = f"{title}_translated_{self.target_language}.txt"
            filename = f"the_art_of_public_speaking_translated_{self.target_language}.txt"
        
        # Ensure output directory exists
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"The Art of Public Speaking - Translated to {self.SUPPORTED_LANGUAGES[self.target_language]}\n")
                f.write("="*60 + "\n\n")
                f.write(translated_text)
            
            self.logger.info(f"Translation saved to: {filepath}")
            return filepath
            
        except IOError as e:
            self.logger.error(f"Failed to save translation: {e}")
            raise


def main():
    """
    Main function to run the book translation application.
    """
    parser = argparse.ArgumentParser(
        description="Translate The Art of Public Speaking to Southeast Asian languages using SEA-LION API"
    )
    
    parser.add_argument(
        '--language', '-l',
        type=str,
        required=True,
        choices=list(BookTranslator.SUPPORTED_LANGUAGES.keys()),
        help='Target language for translation'
    )
    
    parser.add_argument(
        '--api-key', '-k',
        type=str,
        help='SEA-LION API key'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output filename (optional)'
    )
    
    args = parser.parse_args()

    api_key = args.api_key

    if not api_key:
        print("Error: API key is required. Provide it via --api-key argument.")
        sys.exit(1)

    try:
        # Initialize translator
        translator = BookTranslator(
            api_key=api_key,
            target_language=args.language
        )
        
        print(f"Starting translation to {BookTranslator.SUPPORTED_LANGUAGES[args.language]}...")
        print(f"Using model: aisingapore/Gemma-SEA-LION-v4-27B-IT")
        
        # Translate the book
        translated_text = translator.translate_book()
        
        # Save the translation
        output_file = translator.save_translation(translated_text, args.output)
        
        print(f"\n Translation completed successfully!")
        print(f"Translated book saved to: {output_file}")
        print(f"Language: {BookTranslator.SUPPORTED_LANGUAGES[args.language]}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


