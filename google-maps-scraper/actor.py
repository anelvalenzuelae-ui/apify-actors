"""
Google Maps Business Scraper for Apify Store
Extrae datos de negocios, ubicaciones, reseñas de Google Maps
Optimizado para mercado mexicano
"""

import asyncio
import json
from typing import Optional, List, Dict
from datetime import datetime
from apify_client import ApifyClient
from playwright.async_api import async_playwright, Browser, Page

class GoogleMapsScraper:
    """Scraper para datos de negocios en Google Maps"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        
    async def init_browser(self):
        """Inicializar navegador Playwright"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        
    async def search_businesses(self, query: str, location: str = "Mexico", max_results: int = 20) -> List[Dict]:
        """
        Buscar negocios en Google Maps
        
        Args:
            query: Tipo de negocio (ej: "restaurantes", "farmacias")
            location: Ubicación (ej: "Mexico City", "Guadalajara")
            max_results: Máximo de resultados
            
        Returns:
            Lista de negocios con datos
        """
        page = await self.browser.new_page()
        
        try:
            # Construir URL de búsqueda
            search_url = f"https://www.google.com/maps/search/{query}+in+{location}"
            await page.goto(search_url, wait_until="networkidle")
            
            # Esperar a que carguen los resultados
            await page.wait_for_selector('[role="listbox"]', timeout=10000)
            
            businesses = []
            
            # Extraer datos de cada negocio
            for i in range(max_results):
                try:
                    # Click en el negocio
                    business_items = await page.query_selector_all('[role="option"]')
                    
                    if i >= len(business_items):
                        break
                    
                    await business_items[i].click()
                    await page.wait_for_timeout(1000)
                    
                    # Extraer información
                    business_data = await page.evaluate("""
                    () => {
                        const data = {};
                        
                        // Nombre
                        const nameEl = document.querySelector('h1');
                        data.name = nameEl ? nameEl.textContent.trim() : null;
                        
                        // Rating
                        const ratingEl = document.querySelector('[aria-label*="stars"]');
                        data.rating = ratingEl ? ratingEl.getAttribute('aria-label') : null;
                        
                        // Número de reseñas
                        const reviewsEl = document.querySelector('[aria-label*="reviews"]');
                        data.reviews_count = reviewsEl ? reviewsEl.textContent.trim() : null;
                        
                        // Dirección
                        const addressEl = document.querySelector('[data-item-id="address"]');
                        data.address = addressEl ? addressEl.textContent.trim() : null;
                        
                        // Teléfono
                        const phoneEl = document.querySelector('[data-item-id="phone"]');
                        data.phone = phoneEl ? phoneEl.textContent.trim() : null;
                        
                        // Sitio web
                        const websiteEl = document.querySelector('[data-item-id="website"]');
                        data.website = websiteEl ? websiteEl.getAttribute('href') : null;
                        
                        // Horario
                        const hoursEl = document.querySelector('[data-item-id="hours"]');
                        data.hours = hoursEl ? hoursEl.textContent.trim() : null;
                        
                        // Categoría
                        const categoryEl = document.querySelector('[data-item-id="type"]');
                        data.category = categoryEl ? categoryEl.textContent.trim() : null;
                        
                        // Ubicación (lat/lng)
                        const url = window.location.href;
                        const match = url.match(/@([^,]+),([^,]+)/);
                        if (match) {
                            data.latitude = parseFloat(match[1]);
                            data.longitude = parseFloat(match[2]);
                        }
                        
                        return data;
                    }
                    """)
                    
                    if business_data.get('name'):
                        business_data['scraped_at'] = datetime.now().isoformat()
                        businesses.append(business_data)
                    
                except Exception as e:
                    continue
            
            return businesses
            
        except Exception as e:
            return []
        finally:
            await page.close()
    
    async def get_business_details(self, business_url: str) -> Dict:
        """
        Obtener detalles completos de un negocio
        
        Args:
            business_url: URL de Google Maps del negocio
            
        Returns:
            Diccionario con detalles del negocio
        """
        page = await self.browser.new_page()
        
        try:
            await page.goto(business_url, wait_until="networkidle")
            
            details = await page.evaluate("""
            () => {
                const data = {};
                
                // Información básica
                const nameEl = document.querySelector('h1');
                data.name = nameEl ? nameEl.textContent.trim() : null;
                
                const ratingEl = document.querySelector('[aria-label*="stars"]');
                data.rating = ratingEl ? ratingEl.getAttribute('aria-label') : null;
                
                // Contacto
                const phoneEl = document.querySelector('[data-item-id="phone"]');
                data.phone = phoneEl ? phoneEl.textContent.trim() : null;
                
                const websiteEl = document.querySelector('[data-item-id="website"]');
                data.website = websiteEl ? websiteEl.getAttribute('href') : null;
                
                const addressEl = document.querySelector('[data-item-id="address"]');
                data.address = addressEl ? addressEl.textContent.trim() : null;
                
                // Horario de operación
                const hoursEl = document.querySelector('[data-item-id="hours"]');
                data.hours = hoursEl ? hoursEl.textContent.trim() : null;
                
                // Fotos
                data.photos = [];
                const photoEls = document.querySelectorAll('[role="button"][jsname="Bz112c"]');
                photoEls.forEach((el, idx) => {
                    if (idx < 5) {
                        const style = el.getAttribute('style');
                        if (style && style.includes('url')) {
                            data.photos.push(style);
                        }
                    }
                });
                
                // Reseñas recientes
                data.recent_reviews = [];
                const reviewEls = document.querySelectorAll('[role="article"]');
                reviewEls.forEach((el, idx) => {
                    if (idx < 5) {
                        const author = el.querySelector('[data-review-id]');
                        const text = el.querySelector('[data-review-text]');
                        const rating = el.querySelector('[role="img"]');
                        
                        data.recent_reviews.push({
                            author: author ? author.textContent.trim() : null,
                            text: text ? text.textContent.trim() : null,
                            rating: rating ? rating.getAttribute('aria-label') : null
                        });
                    }
                });
                
                return data;
            }
            """)
            
            details['url'] = business_url
            details['scraped_at'] = datetime.now().isoformat()
            
            return details
            
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
        
        query = actor_input.get('query', 'restaurantes')
        location = actor_input.get('location', 'Mexico City')
        max_results = actor_input.get('max_results', 20)
        
        # Inicializar scraper
        scraper = GoogleMapsScraper()
        await scraper.init_browser()
        
        try:
            # Buscar negocios
            businesses = await scraper.search_businesses(query, location, max_results)
            
            # Guardar resultados
            await Actor.push_data(businesses)
            
            # Log
            await Actor.log.info(f"Scrapados {len(businesses)} negocios")
            
        finally:
            await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
