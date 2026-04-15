import spacy
from typing import List, Any, Union
from pydantic import BaseModel, ConfigDict
from .patterns import EntityPattern, EntityPatterns
from .models import ExtractedEntity

class SpacyMatcher(BaseModel):
  model_config = ConfigDict(arbitrary_types_allowed=True)
  
  model_name: str = "en_core_web_sm"
  nlp: Any = None

  def model_post_init(self, __context):
    try:
      self.nlp = spacy.load(self.model_name)
    except OSError:
      spacy.cli.download(self.model_name)
      self.nlp = spacy.load(self.model_name)
    
    if "entity_ruler" not in self.nlp.pipe_names:
      self.nlp.add_pipe("entity_ruler", before="ner")

  def add_rules(self, patterns: Union[List[EntityPattern], EntityPatterns]):
    ruler = self.nlp.get_pipe("entity_ruler")
    
    if isinstance(patterns, EntityPatterns):
      rule_list = [p.model_dump() for p in patterns.rules]
    else:
      rule_list = [p.model_dump() for p in patterns]
        
    ruler.add_patterns(rule_list)

  def process_text(self, text: str) -> List[ExtractedEntity]:
    if not text:
      return []
    doc = self.nlp(text)
    return [
      ExtractedEntity(
        text=ent.text,
        label=ent.label_,
        start_char=ent.start_char,
        end_char=ent.end_char
      )
      for ent in doc.ents
    ]
