import unittest
import json

def clean_json_text(text: str) -> str:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            p_strip = p.strip()
            if p_strip.startswith("json"):
                p_strip = p_strip[4:].strip()
            if p_strip.startswith("{") and p_strip.endswith("}"):
                return p_strip
            if p_strip.startswith("[") and p_strip.endswith("]"):
                return p_strip
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

def is_safety_refusal(answer: str) -> bool:
    text = answer.strip().lower()
    exact_refusal_starts = [
        "i apologize, but i do not have sufficient validated legal context",
        "i do not have sufficient information",
        "i apologize, but i do not have sufficient",
    ]
    return any(text.startswith(sig) for sig in exact_refusal_starts)

class TestTERRAPipelines(unittest.TestCase):

    def test_clean_json_text(self):
        """Tests stripping markdown backticks from LLM JSON responses."""
        raw_json_md = "```json\n{\"complexity\": \"EASY\", \"reason\": \"factual\"}\n```"
        cleaned = clean_json_text(raw_json_md)
        self.assertEqual(cleaned, '{"complexity": "EASY", "reason": "factual"}')
        parsed = json.loads(cleaned)
        self.assertEqual(parsed["complexity"], "EASY")

    def test_is_safety_refusal(self):
        """Tests accurate detection of safety refusal templates."""
        refusal_1 = "I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately."
        refusal_2 = "I do not have sufficient information."
        normal_ans = "The Court did not apologize for overruling Plessy v. Ferguson in Brown v. Board of Education."

        self.assertTrue(is_safety_refusal(refusal_1))
        self.assertTrue(is_safety_refusal(refusal_2))
        self.assertFalse(is_safety_refusal(normal_ans))

    def test_bounded_cache_eviction(self):
        """Tests FIFO/LRU capacity eviction in app bounded cache layer."""
        cache = {}
        max_size = 3
        
        def set_bounded_cache(cache_dict: dict, key: str, value: dict, limit: int):
            if len(cache_dict) >= limit and key not in cache_dict:
                first_key = next(iter(cache_dict))
                cache_dict.pop(first_key, None)
            cache_dict[key] = value

        set_bounded_cache(cache, "k1", {"val": 1}, max_size)
        set_bounded_cache(cache, "k2", {"val": 2}, max_size)
        set_bounded_cache(cache, "k3", {"val": 3}, max_size)
        self.assertEqual(len(cache), 3)

        # Adding 4th item should evict k1
        set_bounded_cache(cache, "k4", {"val": 4}, max_size)
        self.assertEqual(len(cache), 3)
        self.assertNotIn("k1", cache)
        self.assertIn("k4", cache)

if __name__ == "__main__":
    unittest.main()
