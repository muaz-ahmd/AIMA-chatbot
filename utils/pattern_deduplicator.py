import json
import os
import sys
from fuzzywuzzy import fuzz

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ChatbotConfig
from core.input_parser import InputParser

def deduplicate_patterns(patterns_file):
    print(f"Loading patterns from {patterns_file}...")
    
    if not os.path.exists(patterns_file):
        print("Patterns file not found.")
        return

    with open(patterns_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    config = ChatbotConfig()
    parser = InputParser(config)
    
    original_count = len(data)
    learned_patterns = {}
    standard_patterns = {}
    
    # Separate learned from standard
    for key, value in data.items():
        if key.startswith("learned"):
            learned_patterns[key] = value
        else:
            standard_patterns[key] = value
            
    print(f"Found {len(standard_patterns)} standard patterns and {len(learned_patterns)} learned patterns.")
    
    processed_patterns = {}
    merged_count = 0
    
    # Process all patterns (standard and learned)
    for key, value in data.items():
        # Collect all unique keywords from all patterns in this entry
        all_keywords = set()
        patterns_list = value.get("patterns", [])
        
        for pat in patterns_list:
            # Clean regex
            clean_pat = pat.replace("\\b", " ").replace("\\", " ").replace(".*", " ").replace("(", " ").replace(")", " ")
            # Split by pipe if present
            sub_patterns = clean_pat.split("|")
            for sp in sub_patterns:
                normalized_sp = parser.normalize_for_pattern(sp)
                if normalized_sp:
                    all_keywords.update(normalized_sp.split())
        
        # If no patterns, fallback to key or original_query
        if not all_keywords:
            query = value.get("original_query", key)
            normalized_q = parser.normalize_for_pattern(query)
            if normalized_q:
                all_keywords.update(normalized_q.split())
        
        tags = sorted(list(all_keywords))
        normalized = " ".join(tags)
        
        if not normalized:
            processed_patterns[key] = value
            continue
            
        # Find if we already have a similar normalized pattern (only merge for learned ones to be safe)
        found_similar = None
        if key.startswith("learned"):
            for p_key, p_value in processed_patterns.items():
                if p_key.startswith("learned"):
                    p_norm = p_value.get("normalized", "")
                    if p_norm:
                        # Use token_sort_ratio and higher threshold for strictness
                        score = fuzz.token_sort_ratio(normalized, p_norm) / 100.0
                        if score >= 0.90:
                            found_similar = p_key
                            break
        
        if found_similar:
            # Merge responses
            existing_responses = processed_patterns[found_similar].get("responses", [])
            new_responses = value.get("responses", [])
            for resp in new_responses:
                if resp not in existing_responses:
                    existing_responses.append(resp)
            processed_patterns[found_similar]["responses"] = existing_responses
            merged_count += 1
        else:
            # Add as new or updated pattern
            tags = normalized.split()
            value["normalized"] = normalized
            value["tags"] = tags
            if "original_query" not in value and key.startswith("learned"):
                value["original_query"] = query
            processed_patterns[key] = value
            
    # Final data
    final_data = processed_patterns
    
    print(f"Processing complete. Merged {merged_count} patterns.")
    print(f"Final count: {len(final_data)} (Original: {original_count})")
    
    # Save back
    with open(patterns_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2)
    print("Patterns saved.")

if __name__ == "__main__":
    config = ChatbotConfig()
    patterns_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local", "patterns.json")
    deduplicate_patterns(patterns_path)
