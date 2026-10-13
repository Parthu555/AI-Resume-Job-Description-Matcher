import re
from typing import List, Tuple

class TextPreprocessor:
    def __init__(self, chunk_size: int = 120, chunk_overlap: int = 30):
        self.chunk_size = chunk_size  # In words
        self.chunk_overlap = chunk_overlap

    def clean_text(self, text: str) -> str:
        """Removes noise, non-printable characters, and normalizes spacing."""
        if not text:
            return ""
        # Remove null characters and non-printable control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Normalize various bullet points
        text = re.sub(r"^[\s\*\-\u2022\u2023\u25e6\u2043\u2219\uf0b7]+", "- ", text, flags=re.MULTILINE)
        # Normalize whitespace
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def split_into_sentences(self, text: str) -> List[str]:
        """Splits text into meaningful sentences or bullet points."""
        cleaned = self.clean_text(text)
        if not cleaned:
            return []
        
        # Split by newlines or sentence-ending punctuation followed by whitespace
        raw_units = re.split(r"(?:\n+|\.(?:\s+|$))", cleaned)
        sentences = []
        for unit in raw_units:
            clean_unit = unit.strip(" -*•\t\r\n")
            if len(clean_unit) > 10:  # Ignore fragments
                sentences.append(clean_unit)
        return sentences

    def create_overlapping_chunks(self, text: str) -> List[str]:
        """Splits document into overlapping word chunks so no context is cut off."""
        cleaned = self.clean_text(text)
        words = cleaned.split()
        if not words:
            return []
        
        if len(words) <= self.chunk_size:
            return [cleaned]

        chunks = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        for i in range(0, len(words), step):
            chunk_words = words[i:i + self.chunk_size]
            chunks.append(" ".join(chunk_words))
            if i + self.chunk_size >= len(words):
                break
        return chunks

    def extract_snippets(self, text: str, keyword: str, context_words: int = 15) -> List[str]:
        """Finds sentence or context snippets mentioning a given skill or keyword."""
        pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
        snippets = []
        
        # Check per line/bullet first
        lines = text.split("\n")
        for line in lines:
            line_str = line.strip(" -*•\t")
            if pattern.search(line_str) and len(line_str) > 5:
                snippets.append(line_str)
                if len(snippets) >= 2:
                    return snippets

        # Fallback to word context window if not matched on clean line
        if not snippets:
            words = text.split()
            for idx, word in enumerate(words):
                clean_word = re.sub(r"[^\w\+\#]", "", word.lower())
                if clean_word == keyword.lower():
                    start = max(0, idx - context_words)
                    end = min(len(words), idx + context_words + 1)
                    snippets.append("... " + " ".join(words[start:end]) + " ...")
                    if len(snippets) >= 2:
                        break

        return snippets
