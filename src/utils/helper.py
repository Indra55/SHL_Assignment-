import os
from dotenv import load_dotenv
from google import genai

def get_graded_relevance(results):
    if not results:
        return {}
    max_score = max(r.get('similarity_score', 0) for r in results) or 1
    return {
        r['url']: (r.get('similarity_score', 0) / max_score) ** 2
        for r in results if 'url' in r
    }

def graded_recall_at_k(relevant_scores, retrieved, k):
    top_k = retrieved[:k]
    total_relevance = sum(relevant_scores.values())
    if total_relevance == 0:
        return 0.0
    retrieved_relevance = sum(relevant_scores.get(url, 0) for url in top_k)
    return retrieved_relevance / total_relevance

def graded_average_precision(relevant_scores, retrieved, k):
    hits = 0
    sum_precisions = 0.0
    total_relevant = sum(1 for score in relevant_scores.values() if score > 0)
    if total_relevant == 0:
        return 0.0
    for i, item in enumerate(retrieved[:k], 1):
        if item in relevant_scores and relevant_scores[item] > 0:
            hits += 1
            precision = hits / i
            sum_precisions += precision * relevant_scores[item]
    return sum_precisions / min(total_relevant, k)

def init_genai():
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def format_results(results, query):
    formatted = f"Query: {query}\n\nRelevant Products:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result['title']}\n"
        formatted += f"   Score: {result.get('similarity_score', 0.0):.3f}\n"
        formatted += f"   Job Level: {result.get('job_level', 'N/A')}\n"
        formatted += f"   Test Types: {', '.join(result.get('test_types', [])) or 'N/A'}\n"
        formatted += f"   Description: {result.get('description', '')[:200]}...\n\n"
    return formatted

def get_genai_response(client, search_results, query):
    if not client:
        return "GenAI client not available."
    
    prompt = f"""Analyze these SHL assessment results for query "{query}":
{search_results}

The test types mean this:

A - Ability & Aptitude  
B - Biodata & Situational Judgement  
C - Competencies  
D - Development & 360  
E - Assessment Exercises  
K - Knowledge & Skills  
P - Personality & Behavior  
S - Simulations  

Provide: 
1. Top matching solutions with explanations
2. Key features and benefits
3. Recommended job levels
4. Usage recommendations"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text if response else "Empty response"
    except Exception as e:
        return f"Error: {str(e)}"
