from googletrans import Translator
import concurrent.futures
from functools import lru_cache

class ReportTranslator:
    def __init__(self):
        self.translator = Translator()
        self.cache = {}
    
    @lru_cache(maxsize=1000)
    def translate_text(self, text, target_language='en'):
        """Translate text with caching"""
        if target_language == 'en' or not text:
            return text
        
        cache_key = f"{text}_{target_language}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            if target_language == 'hinglish':
                result = self._to_hinglish(text)
            else:
                result = self.translator.translate(text, dest=target_language).text
            
            self.cache[cache_key] = result
            return result
        except:
            return text
    
    def batch_translate(self, texts, target_language='en'):
        """Translate multiple texts efficiently"""
        if target_language == 'en':
            return texts
        
        # Use thread pool for parallel translation
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.translate_text, text, target_language) for text in texts]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return results
    
    def _to_hinglish(self, text):
        """Convert to Hinglish"""
        replacements = {
            'Report': 'Report',
            'Analysis': 'Analysis',
            'Growth': 'Growth',
            'Trend': 'Trend',
            'increase': 'badhna',
            'decrease': 'kam hona',
            'shows': 'dikha raha hai',
            'high': 'zyada',
            'low': 'kam',
            'Recommendations': 'Sujhav',
            'Insights': 'Insights',
            'Market': 'Market'
        }
        
        result = text
        for eng, hin in replacements.items():
            result = result.replace(eng, hin)
        return result