"""Trend Analysis Agent - Analyzes keywords and generates trending hashtags."""

import logging
import re
from typing import List, Dict, Tuple
from pytrends.request import TrendReq
import time
import random

logger = logging.getLogger(__name__)


class TrendAnalysisAgent:
    """Agent for analyzing keyword trends and generating hashtags."""
    
    def __init__(self):
        """Initialize the trend analysis agent."""
        self.pytrends = None
        self._init_pytrends()
    
    def _init_pytrends(self):
        """Initialize PyTrends with retry logic."""
        try:
            self.pytrends = TrendReq(hl='tr-TR', tz=180, timeout=(10, 25))
            logger.info("PyTrends initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize PyTrends: {e}")
            self.pytrends = None
    
    def normalize_keywords(self, keywords: List[str]) -> List[str]:
        """
        Normalize and clean keywords.
        
        Args:
            keywords: Raw keyword list
            
        Returns:
            Normalized keyword list
        """
        normalized = []
        for keyword in keywords[:50]:  # Limit to first 50
            # Clean and normalize
            cleaned = keyword.strip().lower()
            cleaned = re.sub(r'[^\w\s-]', '', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            
            if cleaned and len(cleaned) > 2:
                normalized.append(cleaned)
        
        return normalized
    
    def get_trend_scores(self, keywords: List[str]) -> List[Tuple[str, float]]:
        """
        Get trend scores for keywords using PyTrends.
        
        Args:
            keywords: List of normalized keywords
            
        Returns:
            List of (keyword, score) tuples sorted by score
        """
        scores = []
        
        if self.pytrends and keywords:
            try:
                # Process in batches of 5 (PyTrends limit)
                for i in range(0, len(keywords), 5):
                    batch = keywords[i:i+5]
                    
                    if not batch:
                        continue
                    
                    try:
                        # Get 7-day trends
                        self.pytrends.build_payload(
                            batch,
                            timeframe='now 7-d',
                            geo='TR'
                        )
                        interest_7d = self.pytrends.interest_over_time()
                        
                        # Get 30-day trends
                        self.pytrends.build_payload(
                            batch,
                            timeframe='today 1-m',
                            geo='TR'
                        )
                        interest_30d = self.pytrends.interest_over_time()
                        
                        # Calculate weighted scores
                        for keyword in batch:
                            score_7d = 0
                            score_30d = 0
                            
                            if not interest_7d.empty and keyword in interest_7d.columns:
                                score_7d = interest_7d[keyword].mean()
                            
                            if not interest_30d.empty and keyword in interest_30d.columns:
                                score_30d = interest_30d[keyword].mean()
                            
                            # Weighted combination: 70% recent, 30% monthly
                            final_score = (0.7 * score_7d) + (0.3 * score_30d)
                            scores.append((keyword, final_score))
                        
                        # Small delay to avoid rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.warning(f"Error getting trends for batch {batch}: {e}")
                        # Add with fallback score
                        for keyword in batch:
                            scores.append((keyword, self._fallback_score(keyword)))
                
            except Exception as e:
                logger.error(f"Error in trend analysis: {e}")
                # Use fallback for all keywords
                scores = [(kw, self._fallback_score(kw)) for kw in keywords]
        else:
            # Fallback scoring when PyTrends is unavailable
            logger.info("Using fallback scoring (PyTrends unavailable)")
            scores = [(kw, self._fallback_score(kw)) for kw in keywords]
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:15]  # Return top 15
    
    def _fallback_score(self, keyword: str) -> float:
        """
        Generate deterministic fallback score based on keyword properties.
        
        Args:
            keyword: The keyword to score
            
        Returns:
            Fallback score between 0 and 100
        """
        # Simple deterministic scoring based on keyword properties
        base_score = 50.0
        
        # Bonus for shorter keywords (more likely to be popular)
        if len(keyword) <= 5:
            base_score += 20
        elif len(keyword) <= 8:
            base_score += 10
        
        # Bonus for common gaming terms
        gaming_terms = ['game', 'play', 'mobile', 'online', 'rpg', 'fps', 'mmo', 'pvp']
        for term in gaming_terms:
            if term in keyword:
                base_score += 15
                break
        
        # Add some variation based on alphabetical position
        base_score += (ord(keyword[0]) - ord('a')) * 0.5
        
        return min(100, max(0, base_score))
    
    def generate_hashtags(self, keywords: List[Tuple[str, float]]) -> List[str]:
        """
        Generate hashtag variations from scored keywords.
        
        Args:
            keywords: List of (keyword, score) tuples
            
        Returns:
            List of hashtags
        """
        hashtags = set()
        
        for keyword, score in keywords:
            # Clean keyword for hashtag use
            clean_kw = keyword.replace(' ', '').replace('-', '')
            
            # Base hashtag
            hashtags.add(f"#{clean_kw}")
            
            # Variations
            if score > 50:  # High-scoring keywords get more variations
                hashtags.add(f"#{clean_kw}game")
                hashtags.add(f"#mobile{clean_kw}")
            
            if score > 70:  # Very high-scoring keywords
                hashtags.add(f"#{clean_kw}gaming")
                hashtags.add(f"#{clean_kw}tr")
            
            # Stop if we have enough
            if len(hashtags) >= 20:
                break
        
        return list(hashtags)[:20]
    
    def analyze(self, aso_keywords_path: str) -> Dict:
        """
        Main analysis method.
        
        Args:
            aso_keywords_path: Path to ASO keywords file
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Read keywords
            keywords = []
            try:
                with open(aso_keywords_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Handle both comma and newline separated
                    if ',' in content:
                        keywords = content.split(',')
                    else:
                        keywords = content.split('\n')
            except Exception as e:
                logger.error(f"Error reading keywords file: {e}")
                # Use sample keywords as fallback
                keywords = [
                    "mobile game", "rpg", "action", "adventure", "strategy",
                    "puzzle", "casual", "multiplayer", "online", "battle"
                ]
            
            # Normalize keywords
            normalized = self.normalize_keywords(keywords)
            logger.info(f"Normalized {len(normalized)} keywords")
            
            # Get trend scores
            scored = self.get_trend_scores(normalized)
            logger.info(f"Scored {len(scored)} keywords")
            
            # Generate hashtags
            hashtags = self.generate_hashtags(scored)
            logger.info(f"Generated {len(hashtags)} hashtags")
            
            return {
                'status': 'success',
                'keywords_analyzed': len(normalized),
                'top_keywords': [
                    {'keyword': kw, 'score': score}
                    for kw, score in scored
                ],
                'hashtags': hashtags,
                'summary': f"Analyzed {len(normalized)} keywords, identified {len(scored)} trending terms, generated {len(hashtags)} hashtags"
            }
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'keywords_analyzed': 0,
                'top_keywords': [],
                'hashtags': ['#mobilegame', '#gaming', '#game', '#play', '#fun'],
                'summary': 'Trend analysis failed, using default hashtags'
            }