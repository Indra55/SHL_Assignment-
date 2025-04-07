import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import markdown
from typing import List, Set, Dict
from huggingface_hub import login

login(st.secrets["token"])
try:
    project_root = Path(__file__).resolve().parent.parent
    src_path = project_root / "src"
    sys.path.append(str(project_root))
    from src.embeddings.product_embeddings import ProductEmbeddings
except ImportError:
    st.error("Failed to import ProductEmbeddings. Please ensure src/embeddings/product_embeddings.py exists.")
    st.stop()
except Exception as e:
    st.error(f"Error setting up paths or imports: {e}")
    st.stop()

def get_graded_relevance(results: List[dict]) -> Dict[str, float]:
    """Convert similarity scores to relevance scores (0-1 scale)"""
    if not results:
        return {}
    
    max_score = max(r.get('similarity_score', 0) for r in results) or 1
    return {r['url']: (r.get('similarity_score', 0) / max_score) ** 2 for r in results if 'url' in r}

def graded_recall_at_k(relevant_scores: Dict[str, float], retrieved: List[str], k: int) -> float:
    """Calculate recall where items contribute proportionally to relevance"""
    top_k = retrieved[:k]
    total_relevance = sum(relevant_scores.values())
    if total_relevance == 0:
        return 0.0
    retrieved_relevance = sum(relevant_scores.get(url, 0) for url in top_k)
    return retrieved_relevance / total_relevance

def graded_average_precision(relevant_scores: Dict[str, float], retrieved: List[str], k: int) -> float:
    """Calculate graded average precision"""
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
    """Initialize Genai client"""
    try:
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            st.warning("GOOGLE_API_KEY not found. GenAI features disabled.")
            return None
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {str(e)}")
        return None

# --- Formatting Functions ---
def format_results(results, query):
    """Format search results for genai"""
    formatted = f"Query: {query}\n\nRelevant Products:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result['title']}\n"
        formatted += f"   Score: {result.get('similarity_score', 0.0):.3f}\n"
        formatted += f"   Job Level: {result.get('job_level', 'N/A')}\n"
        formatted += f"   Test Types: {', '.join(result.get('test_types', [])) or 'N/A'}\n"
        formatted += f"   Description: {result.get('description', '')[:200]}...\n\n"
    return formatted

def get_genai_response(client, search_results, query):
    """Get enhanced response from genai"""
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

def main():
    st.set_page_config(page_title="SHL Assessment Explorer", layout="wide")
    st.title("SHL Assessment Solutions Explorer")

    try:
        embedder = ProductEmbeddings()
        products_path = src_path / "data" / "shl_products.json"
        embedder.load_products(str(products_path))
        
        index_path = src_path / "embeddings" / "products.index"
        if index_path.exists():
            embedder.load_index(str(index_path))
        else:
            with st.spinner("Generating embeddings..."):
                embedder.generate_embeddings()
                embedder.save_index(str(index_path))
                
        genai_client = init_genai()
    except Exception as e:
        st.error(f"Initialization error: {str(e)}")
        st.stop()

    # Search interface
    query = st.text_input("Search assessments (e.g., 'network engineer')")
    k = st.slider("Number of results", 1, 20, 5)
    
    if query:
        with st.spinner("Searching..."):
            try:
                results = embedder.search(query, k=k)
                
                if not results:
                    st.warning("No results found")
                    st.stop()
                
                # Display raw results
                with st.expander("View Raw Search Results"):
                    if results:
                        for i, result in enumerate(results, 1):
                            st.write(f"\n### {i}. {result.get('title', 'No Title')}")
                            st.write(f"**Similarity Score:** {result.get('similarity_score', 0.0):.3f}")
                            st.write(f"**Job Level:** {result.get('job_level', 'N/A')}")
                            st.write(f"**Languages:** {result.get('languages', 'N/A')}")
                            st.write(f"**Completion Time:** {result.get('completion_time', 'N/A')} minutes")
                            test_types = result.get('test_types', [])
                            st.write(f"**Test Types:** {', '.join(test_types) if test_types else 'N/A'}")
                            st.write(f"**Remote Testing:** {result.get('remote_testing', 'N/A')}")
                            pdf_links = result.get('pdf_links')
                            if pdf_links:
                                st.write("**Documentation:**")
                                for pdf in pdf_links:
                                    st.write(f"- [{pdf.get('name', 'Link')}]({pdf.get('url', '#')})") # Safer access
                            st.write(f"**Description:**\n{result.get('description', 'No description available.')}")
                            st.write("---")
                    else:

                # GenAI analysis
                        st.markdown("## AI Analysis")
                if genai_client:
                    analysis = get_genai_response(
                        genai_client,
                        format_results(results, query),
                        query
                    )
                    st.markdown(analysis)
                
                graded_relevance = get_graded_relevance(results)
                retrieved = [r['url'] for r in results if 'url' in r]
                
                st.sidebar.markdown("### Graded Metrics")
                st.sidebar.metric(
                    "Recall@K", 
                    f"{graded_recall_at_k(graded_relevance, retrieved, k):.1%}",
                    help="Weighted by similarity scores"
                )
                st.sidebar.metric(
                    "Avg Precision", 
                    f"{graded_average_precision(graded_relevance, retrieved, k):.1%}",
                    help="Precision weighted by relevance"
                )
                
            except Exception as e:
                st.error(f"Search error: {str(e)}")

if __name__ == "__main__":
    main()