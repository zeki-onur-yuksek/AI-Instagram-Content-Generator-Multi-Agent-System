"""Content Generation Agent - Generates social media post content."""

import os
import logging
import json
from typing import Dict, List, Optional
import openai
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class ContentGenerationAgent:
    """Agent for generating social media content."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the content generation agent.
        
        Args:
            api_key: OpenAI API key (optional)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                openai.api_key = self.api_key
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.info("No OpenAI API key provided, will use fallback generation")
    
    def generate_with_openai(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate content using OpenAI API.
        
        Args:
            prompt: The prompt for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            if not self.client:
                return None
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative social media content creator specializing in gaming content. Generate engaging Turkish content for Instagram."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return None
    
    def fallback_generation(self, trend_data: Dict, content_data: Dict) -> List[Dict]:
        """
        Generate content using deterministic fallback templates.
        
        Args:
            trend_data: Trend analysis results
            content_data: Content understanding results
            
        Returns:
            List of generated post candidates
        """
        templates = [
            {
                'title': '🎮 En Yeni Mobil Oyun Deneyimi!',
                'caption': """🎮 Muhteşem bir oyun deneyimi sizi bekliyor!

Bu oyunda neler var?
✨ Etkileyici grafikler ve görsel efektler
🎯 Sürükleyici oynanış mekanikleri  
🏆 Rekabetçi çok oyunculu modlar
🎨 Benzersiz sanat tasarımı

Oyunun öne çıkan özellikleri:
• Kolay öğrenilir, ustalaşması zor oynanış
• Düzenli içerik güncellemeleri
• Aktif oyuncu topluluğu
• Free-to-play model

Hemen indir ve maceraya katıl! 🚀
Arkadaşlarını etiketle ve birlikte oynayın! 👥

📲 Şimdi ücretsiz indir!""",
                'hashtags': ['#mobiloyun', '#oyun', '#gaming', '#mobilegaming', '#yenioyun', '#türkiyegaming', '#oyunsever', '#mobilgame', '#gametr', '#oyunönerisi', '#ücretsizoyun', '#eğlence']
            },
            {
                'title': '🔥 Kaçırılmayacak Oyun Fırsatı!',
                'caption': """🔥 Bu oyunu mutlaka denemelisiniz!

Neden bu oyun?
🌟 Özgün hikaye ve karakterler
⚔️ Aksiyon dolu sahneler
🗺️ Geniş keşif alanları
💎 Ödüllendirici ilerleme sistemi

Oyuncular ne diyor?
"Yılın en iyi mobil oyunu!" ⭐⭐⭐⭐⭐
"Bağımlılık yapıyor!" 
"Grafikler muhteşem!"

Özel özellikler:
• PvP ve PvE modları
• Klan sistemi ve takım savaşları
• Haftalık etkinlikler ve turnuvalar
• Kişiselleştirilebilir karakterler

Sen de bu eğlenceye katıl! 🎊
Yorumlarda düşüncelerini paylaş! 💬

🎮 Hemen oynamaya başla!""",
                'hashtags': ['#oyuntavsiyesi', '#mobiloyunlar', '#gameoftheday', '#oyunzamanı', '#türkoyun', '#gamer', '#mobilegamer', '#yenioyunlar', '#oyundünyası', '#gaming', '#oyuncu', '#mobilgaming']
            },
            {
                'title': '⚡ Mobil Oyun Dünyasının Yeni Yıldızı!',
                'caption': """⚡ Herkesin konuştuğu oyun burada!

Oyunun büyüleyici dünyası:
🏰 Epik maceralar ve görevler
🐉 Efsanevi yaratıklar ve bosslar
⚡ Güçlü yetenekler ve büyüler
🎁 Günlük ödüller ve sürprizler

Neler yapabilirsiniz?
• Kendi kahramanınızı yaratın
• Arkadaşlarınızla guild kurun
• Dünya çapında oyuncularla yarışın
• Eşsiz itemler toplayın

Topluluk özellikleri:
👥 Canlı sohbet sistemi
🤝 Takım kurma ve işbirliği
🏅 Liderlik tabloları
🎯 Haftalık challengelar

Maceranız başlasın! 🚀
Hangi seviyeye ulaşabilirsiniz? 💪

⬇️ Ücretsiz indirin ve oynayın!""",
                'hashtags': ['#mobilegame', '#oyunlar', '#gamingcommunity', '#oyunaşkı', '#mobiloyunum', '#gamerlife', '#oyunbağımlısı', '#newgame', '#türkgamer', '#oyunönerisi', '#mobilegames', '#oyuntürkiye']
            }
        ]
        
        # Select templates based on some variation
        selected = random.sample(templates, min(3, len(templates)))
        
        # Add trending hashtags if available
        if trend_data and 'hashtags' in trend_data:
            trending_tags = trend_data['hashtags'][:5]
            for post in selected:
                # Mix trending with template hashtags
                mixed_tags = trending_tags + post['hashtags'][:7]
                post['hashtags'] = mixed_tags[:12]
        
        return selected
    
    def create_prompt(self, trend_data: Dict, content_data: Dict) -> str:
        """
        Create a prompt for content generation.
        
        Args:
            trend_data: Trend analysis results
            content_data: Content understanding results
            
        Returns:
            Formatted prompt string
        """
        # Extract key information
        top_keywords = []
        if trend_data and 'top_keywords' in trend_data:
            top_keywords = [kw['keyword'] for kw in trend_data['top_keywords'][:5]]
        
        video_summary = ""
        if content_data and 'video' in content_data:
            video_summary = content_data['video'].get('transcript', '')[:500]
        
        image_captions = []
        if content_data and 'screenshots' in content_data:
            captions = content_data['screenshots'].get('captions', [])
            image_captions = [cap['caption'] for cap in captions[:3]]
        
        game_summary = ""
        if content_data and 'text' in content_data:
            game_summary = content_data['text'].get('summary', '')[:300]
        
        prompt = f"""Generate an engaging Turkish Instagram post for a mobile game with the following information:

Trending Keywords: {', '.join(top_keywords)}
Game Description: {game_summary}
Visual Elements: {', '.join(image_captions)}
Video Content Summary: {video_summary}

Create a post with:
1. A catchy title (max 60 characters)
2. An engaging caption (max 2200 characters) that includes emojis, highlights game features, and ends with a call-to-action
3. Exactly 12 relevant hashtags mixing trending and niche gaming tags

Format the response as JSON with keys: title, caption, hashtags (array)"""
        
        return prompt
    
    def generate(self, trend_data: Dict, content_data: Dict) -> Dict:
        """
        Main generation method.
        
        Args:
            trend_data: Trend analysis results
            content_data: Content understanding results
            
        Returns:
            Generation results with 3 post candidates
        """
        try:
            logger.info("Starting content generation")
            
            candidates = []
            
            if self.client:
                # Try OpenAI generation
                logger.info("Attempting OpenAI generation")
                
                for i in range(3):
                    prompt = self.create_prompt(trend_data, content_data)
                    # Add variation instruction for each candidate
                    if i == 1:
                        prompt += "\nMake this version more casual and friendly."
                    elif i == 2:
                        prompt += "\nMake this version more exciting and action-oriented."
                    
                    result = self.generate_with_openai(prompt)
                    
                    if result:
                        try:
                            # Try to parse as JSON
                            if result.startswith('```json'):
                                result = result[7:-3]  # Remove markdown code block
                            elif result.startswith('```'):
                                result = result[3:-3]
                            
                            post_data = json.loads(result)
                            
                            # Ensure all required fields
                            if 'title' in post_data and 'caption' in post_data and 'hashtags' in post_data:
                                # Ensure hashtags is a list
                                if isinstance(post_data['hashtags'], str):
                                    post_data['hashtags'] = post_data['hashtags'].split()
                                
                                # Ensure hashtags start with #
                                post_data['hashtags'] = [
                                    tag if tag.startswith('#') else f'#{tag}'
                                    for tag in post_data['hashtags']
                                ][:12]
                                
                                candidates.append(post_data)
                                logger.info(f"Generated candidate {i+1} with OpenAI")
                            
                        except json.JSONDecodeError:
                            # Try to extract content manually
                            lines = result.split('\n')
                            post_data = {
                                'title': lines[0][:60] if lines else 'Yeni Oyun Keşfi!',
                                'caption': '\n'.join(lines[1:-1])[:2200] if len(lines) > 2 else result[:2200],
                                'hashtags': ['#mobiloyun', '#gaming', '#oyun', '#game', '#türkiye', '#yenioyun', '#mobilegaming', '#gamer', '#oyunönerisi', '#gametr', '#mobilgame', '#oyuntürkiye']
                            }
                            candidates.append(post_data)
                            logger.info(f"Generated candidate {i+1} with OpenAI (parsed)")
            
            # Use fallback if needed
            if len(candidates) < 3:
                logger.info(f"Using fallback generation for {3 - len(candidates)} candidates")
                fallback_posts = self.fallback_generation(trend_data, content_data)
                candidates.extend(fallback_posts[:3 - len(candidates)])
            
            # Ensure we have exactly 3 candidates
            while len(candidates) < 3:
                candidates.append({
                    'title': f'🎮 Muhteşem Oyun Deneyimi #{len(candidates)+1}',
                    'caption': f'Bu harika oyunu keşfedin! Eğlenceli oynanış, muhteşem grafikler ve daha fazlası sizi bekliyor. Hemen indirin ve oynamaya başlayın! 🚀 #oyun',
                    'hashtags': ['#mobiloyun', '#gaming', '#oyun', '#game', '#türkiye', '#yenioyun', '#mobilegaming', '#gamer', '#oyunönerisi', '#gametr', '#mobilgame', '#oyuntürkiye']
                })
            
            return {
                'status': 'success',
                'candidates': candidates[:3],
                'generation_method': 'openai' if self.client else 'fallback',
                'summary': f'Generated 3 post candidates successfully'
            }
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            
            # Return fallback content
            fallback_posts = self.fallback_generation(trend_data, content_data)
            
            return {
                'status': 'error',
                'error': str(e),
                'candidates': fallback_posts[:3],
                'generation_method': 'fallback',
                'summary': 'Generation failed, using fallback templates'
            }