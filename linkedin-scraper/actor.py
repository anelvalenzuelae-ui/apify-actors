"""
LinkedIn Profile Scraper for Apify Store
Extrae datos de perfiles de LinkedIn sin login
Optimizado para mercado mexicano
"""

import asyncio
import json
from typing import Optional, List
from apify_client import ApifyClient
from playwright.async_api import async_playwright, Browser, Page

# Configuración
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
client = ApifyClient(APIFY_TOKEN)

class LinkedInScraper:
    """Scraper para perfiles públicos de LinkedIn"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.results = []
        
    async def init_browser(self):
        """Inicializar navegador Playwright"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        
    async def scrape_profile(self, profile_url: str) -> dict:
        """
        Scrape un perfil de LinkedIn
        
        Args:
            profile_url: URL del perfil (ej: linkedin.com/in/username)
            
        Returns:
            dict con datos del perfil
        """
        page = await self.browser.new_page()
        
        try:
            await page.goto(profile_url, wait_until="networkidle")
            
            # Extraer datos visibles
            profile_data = await page.evaluate("""
            () => {
                const data = {};
                
                // Nombre
                const nameEl = document.querySelector('h1');
                data.name = nameEl ? nameEl.textContent.trim() : null;
                
                // Título actual
                const titleEl = document.querySelector('[data-test-id="top-card-title"]');
                data.current_title = titleEl ? titleEl.textContent.trim() : null;
                
                // Empresa actual
                const companyEl = document.querySelector('[data-test-id="top-card-company-name"]');
                data.current_company = companyEl ? companyEl.textContent.trim() : null;
                
                // Ubicación
                const locationEl = document.querySelector('[data-test-id="top-card-location"]');
                data.location = locationEl ? locationEl.textContent.trim() : null;
                
                // Bio/Headline
                const bioEl = document.querySelector('[data-test-id="top-card-headline"]');
                data.headline = bioEl ? bioEl.textContent.trim() : null;
                
                // Experiencia (últimos 3 trabajos)
                data.experience = [];
                const expItems = document.querySelectorAll('[data-test-id="experience-item"]');
                expItems.forEach((item, idx) => {
                    if (idx < 3) {
                        const title = item.querySelector('[data-test-id="experience-item-title"]');
                        const company = item.querySelector('[data-test-id="experience-item-company"]');
                        const duration = item.querySelector('[data-test-id="experience-item-duration"]');
                        
                        data.experience.push({
                            title: title ? title.textContent.trim() : null,
                            company: company ? company.textContent.trim() : null,
                            duration: duration ? duration.textContent.trim() : null
                        });
                    }
                });
                
                // Educación
                data.education = [];
                const eduItems = document.querySelectorAll('[data-test-id="education-item"]');
                eduItems.forEach((item, idx) => {
                    if (idx < 2) {
                        const school = item.querySelector('[data-test-id="education-item-school"]');
                        const degree = item.querySelector('[data-test-id="education-item-degree"]');
                        
                        data.education.push({
                            school: school ? school.textContent.trim() : null,
                            degree: degree ? degree.textContent.trim() : null
                        });
                    }
                });
                
                // Habilidades
                data.skills = [];
                const skillItems = document.querySelectorAll('[data-test-id="skill-item"]');
                skillItems.forEach((item, idx) => {
                    if (idx < 10) {
                        data.skills.push(item.textContent.trim());
                    }
                });
                
                return data;
            }
            """)
            
            profile_data['url'] = profile_url
            profile_data['scraped_at'] = datetime.now().isoformat()
            
            return profile_data
            
        except Exception as e:
            return {
                'url': profile_url,
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }
        finally:
            await page.close()
    
    async def scrape_search_results(self, search_query: str, max_results: int = 10) -> List[dict]:
        """
        Buscar perfiles en LinkedIn y scrapearlo
        
        Args:
            search_query: Término de búsqueda (ej: "desarrollador python mexico")
            max_results: Máximo de resultados
            
        Returns:
            Lista de perfiles scrapados
        """
        page = await self.browser.new_page()
        
        try:
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}"
            await page.goto(search_url, wait_until="networkidle")
            
            # Extraer URLs de perfiles
            profile_urls = await page.evaluate("""
            (maxResults) => {
                const urls = [];
                const links = document.querySelectorAll('a[href*="/in/"]');
                
                links.forEach(link => {
                    if (urls.length < maxResults) {
                        const href = link.getAttribute('href');
                        if (href && href.includes('/in/')) {
                            urls.push(href.split('?')[0]);
                        }
                    }
                });
                
                return [...new Set(urls)];
            }
            """, max_results)
            
            # Scrape cada perfil
            results = []
            for url in profile_urls[:max_results]:
                profile_data = await self.scrape_profile(url)
                results.append(profile_data)
                await asyncio.sleep(2)  # Evitar rate limiting
            
            return results
            
        finally:
            await page.close()
    
    async def close(self):
        """Cerrar navegador"""
        if self.browser:
            await self.browser.close()


async def main():
    """Función principal para Apify"""
    from apify import Actor
    
    async with Actor:
        # Obtener input
        actor_input = await Actor.get_input() or {}
        
        search_query = actor_input.get('search_query', 'desarrollador python mexico')
        max_results = actor_input.get('max_results', 10)
        
        # Inicializar scraper
        scraper = LinkedInScraper()
        await scraper.init_browser()
        
        try:
            # Scrape
            results = await scraper.scrape_search_results(search_query, max_results)
            
            # Guardar resultados
            await Actor.push_data(results)
            
            # Log
            await Actor.log.info(f"Scrapados {len(results)} perfiles")
            
        finally:
            await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
