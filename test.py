import tiktoken
import pandas as pd
from jobspy import scrape_jobs

def filter_jobs(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
  term = search_term.lower()
  mask = (
    df['title'].str.lower().str.contains(term, na=False) | 
    df['description'].str.lower().str.contains(term, na=False)
  )
  return df[mask].copy()

def count_tokens(text, encoding):
  if not isinstance(text, str) or not text:
    return 0
  return len(encoding.encode(text))

def main(roles: list[str]):
  all_processed_jobs = []
  role_stats = {}

  # Tiktoken setup for GPT-5.4-nano (o200k_base)
  try:
    encoding = tiktoken.encoding_for_model("gpt-5.4-nano")
  except KeyError:
    encoding = tiktoken.get_encoding("o200k_base")

  for role in roles:
    print(f"--- Scraping Indeed Jakarta for: {role} ---")
    
    # 1. Scrape Jobs (90 days / 500 results)
    jobs_df = scrape_jobs(
      site_name=["indeed"],
      search_term=role,
      #location="Jakarta, Indonesia",
      results_wanted=500,
      hours_old=2160, 
      country_indeed='USA',
    )

    # 2. Apply Custom Filter
    filtered_jobs = filter_jobs(jobs_df, role)

    if not filtered_jobs.empty:
      # 3. Process Tokens
      filtered_jobs['description_tokens'] = filtered_jobs['description'].apply(
        lambda x: count_tokens(x, encoding)
      )
      
      # Track for specific role reporting
      role_stats[role] = {
        'count': len(filtered_jobs),
        'total_tokens': filtered_jobs['description_tokens'].sum(),
        'avg_tokens': filtered_jobs['description_tokens'].mean()
      }
      
      all_processed_jobs.append(filtered_jobs)
    else:
      print(f"No results for '{role}'.")

  # 4. Generate General and Specific Reports
  if all_processed_jobs:
    general_df = pd.concat(all_processed_jobs).drop_duplicates(subset=['job_url'])
    
    print("\n" + "="*40)
    print("SPECIFIC ROLE DATA (GPT-5.4-NANO)")
    print("="*40)
    for role, stats in role_stats.items():
      print(f"Role: {role.upper()}")
      print(f"  - Jobs Found: {stats['count']}")
      print(f"  - Total Tokens: {stats['total_tokens']}")
      print(f"  - Avg Tokens/Job: {stats['avg_tokens']:.1f}")
      print("-" * 20)

    print("\n" + "="*40)
    print("GENERAL SUMMARY (DEDUPLICATED)")
    print("="*40)
    print(f"Total Unique Jobs: {len(general_df)}")
    print(f"Total Combined Tokens: {general_df['description_tokens'].sum()}")
    print(f"Average Token Count: {general_df['description_tokens'].mean():.1f}")
    
    print("\nTop 5 Largest Descriptions (by token count):")
    print(general_df[['company', 'title', 'description_tokens']].sort_values(by='description_tokens', ascending=False).head(5).to_string(index=False))
  else:
    print("No jobs found across all roles.")

if __name__ == "__main__":
  #target_roles = ["software engineer", "data engineer", "devops", "data analyst", "ai engineer"]
  target_roles = ["rust"]
  main(roles=target_roles)
