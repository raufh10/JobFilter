from job_filter.packages.llm.src.client import LLMClient

def generate_structured_response(llm: LLMClient, user_input: str):

  """
  Generates a structured response using responses.parse API.
  """

  response = llm.client.responses.parse(
    model=llm.model,
    input=[
      {"role": "system", "content": llm.system_prompt},
      {"role": "user", "content": user_input},
    ],
    text_format=llm.format_schema,
  )

  return response.output_parsed
