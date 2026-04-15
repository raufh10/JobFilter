import tiktoken
from .models import TokenCount, BatchTokenCount

class TokenCounter:
  def __init__(self, model_name: str = "gpt-5.4-nano"):
    """Initializes the encoder for a specific model."""
    try:
      self.encoder = tiktoken.encoding_for_model(model_name)
    except KeyError:
      self.encoder = tiktoken.get_encoding("cl100k_base")

  def count_tokens(self, text: str) -> TokenCount:
    """Counts tokens for a single string."""
    count = len(self.encoder.encode(text))
    return TokenCount(text=text, token_count=count)

  def count_batch(self, texts: list[str]) -> BatchTokenCount:
    """Counts tokens for a list of strings and calculates the total."""
    counts = [self.count_tokens(t) for t in texts]
    total = sum(c.token_count for c in counts)
    return BatchTokenCount(counts=counts, total_tokens=total)
