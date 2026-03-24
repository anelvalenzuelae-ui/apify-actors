"""
WhatsApp Business Scraper for Apify Store
Extrae números de WhatsApp Business de empresas mexicanas
Optimizado para marketing y ventas
"""

import asyncio
import json
import re
from typing import Optional, List, Dict
from datetime import datetime
from apify_client import ApifyClient
from playwright.async_api import async_playwright, Browser, Page

class WhatsAppBusinessScraper:
    """Scraper para números de WhatsApp Business"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        
    async def init_browser(self):
        """Inicializar navegador Playwright"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        
    async def extract_whatsapp_numbers(self, text: str) -> List[str]:
        """Extraer números de WhatsApp de texto"""
        # Patrones para números mexicanos
        patterns = [
            r'(?:wa\.me/)?(?:\+?52)?[\s.-]?(\d{1,2})[\s.-]?(\d{4})[\s.-]?(\d{4})',
            r'(?:whatsapp|whatsapp\.com)?[\s/]*(?:\+?52)?[\s.-]?(\d{1,2})[\s.-]?(\d{4})[\s.-]?(\d{4})',
            r'https?://wa\.me/52(\d{10})',
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    number = ''.join(match)
                else:
                    number = match
                
                # Validar que sea un número válido
                if len(number) >= 10:
                    numbers.append(f"+52{number[-10:]}")
        
        return list(set(numbers))
    
    async def scrape_business_whatsapp(self, business_type: str, location: str = "Mexico", max_results: int = 20) -> List[Dict]:
        """
        Scrape números de WhatsApp de negocios
        
        Args:
            business_type: Tipo de negocio
            location: Ubicación
            max_results: Máximo de resultados
            
        Returns:
            Lista de negocios con WhatsApp
        """
        page = await self.browser.new_page()
        
        try:
            # Buscar en Google Maps (muchos negocios tienen WhatsApp)
            search_url = f"https://www.google.com/maps/search/{business_type}+in+{location}"
            await page.goto(search_url, wait_until="networkidle")
            
            businesses = []
            
            # Extraer negocios
            for i in range(max_results):
                try:
                    # Click en negocio
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
                        
                        // Teléfono
                        const phoneEl = document.querySelector('[data-item-id="phone"]');
                        data.phone = phoneEl ? phoneEl.textContent.trim() : null;
                        
                        // Sitio web
                        const websiteEl = document.querySelector('[data-item-id="website"]');
                        data.website = websiteEl ? websiteEl.getAttribute('href') : null;
                        
                        // Dirección
                        const addressEl = document.querySelector('[data-item-id="address"]');
                        data.address = addressEl ? addressEl.textContent.trim() : null;
                        
                        // Descripción/Bio
                        const descEl = document.querySelector('[data-item-id="description"]');
                        data.description = descEl ? descEl.textContent.trim() : null;
                        
                        // Obtener todo el texto visible para buscar WhatsApp
                        data.full_text = document.body.innerText;
                        
                        return data;
                    }
                    """)
                    
                    if business_data.get('name'):
                        # Extraer números de WhatsApp
                        full_text = f"{business_data.get('name', '')} {business_data.get('phone', '')} {business_data.get('website', '')} {business_data.get('full_text', '')}"
                        
                        whatsapp_numbers = await self.extract_whatsapp_numbers(full_text)
                        
                        business_data['whatsapp_numbers'] = whatsapp_numbers
                        business_data['has_whatsapp'] = len(whatsapp_numbers) > 0
                        business_data['scraped_at'] = datetime.now().isoformat()
                        
                        # Limpiar full_text
                        del business_data['full_text']
                        
                        businesses.append(business_data)
                    
                except Exception as e:
                    continue
            
            return businesses
            
        except Exception as e:
            return []
        finally:
            await page.close()
    
    async def search_whatsapp_directory(self, category: str, max_results: int = 20) -> List[Dict]:
        """
        Buscar en directorios de WhatsApp Business
        
        Args:
            category: Categoría de negocio
            max_results: Máximo de resultados
            
        Returns:
            Lista de contactos WhatsApp
        """
        page = await self.browser.new_page()
        
        try:
            # Buscar en directorios mexicanos
            search_urls = [
                f"https://www.directorio-empresarial.com/search?q={category}+whatsapp",
                f"https://www.paginasamarillas.com.mx/search?q={category}",
            ]
            
            results = []
            
            for search_url in search_urls:
                try:
                    await page.goto(search_url, wait_until="networkidle", timeout=10000)
                    
                    # Extraer contactos
                    contacts = await page.evaluate("""
                    (maxResults) => {
                        const contacts = [];
                        const items = document.querySelectorAll('.business-item, .company-listing, [data-business]');
                        
                        items.forEach((item, idx) => {
                            if (idx < maxResults) {
                                const data = {};
                                
                                // Nombre
                                const nameEl = item.querySelector('h2, h3, .name');
                                data.name = nameEl ? nameEl.textContent.trim() : null;
                                
                                // Teléfono
                                const phoneEl = item.querySelector('[data-phone], .phone');
                                data.phone = phoneEl ? phoneEl.textContent.trim() : null;
                                
                                // Categoría
                                const categoryEl = item.querySelector('[data-category], .category');
                                data.category = categoryEl ? categoryEl.textContent.trim() : null;
                                
                                // Ubicación
                                const locationEl = item.querySelector('[data-location], .location');
                                data.location = locationEl ? locationEl.textContent.trim() : null;
                                
                                // Obtener todo el texto
                                data.full_text = item.innerText;
                                
                                if (data.name) {
                                    contacts.push(data);
                                }
                            }
                        });
                        
                        return contacts;
                    }
                    """, max_results)
                    
                    for contact in contacts:
                        # Extraer WhatsApp
                        full_text = f"{contact.get('name', '')} {contact.get('phone', '')} {contact.get('full_text', '')}"
                        whatsapp_numbers = await self.extract_whatsapp_numbers(full_text)
                        
                        contact['whatsapp_numbers'] = whatsapp_numbers
                        contact['has_whatsapp'] = len(whatsapp_numbers) > 0
                        contact['scraped_at'] = datetime.now().isoformat()
                        
                        if 'full_text' in contact:
                            del contact['full_text']
                        
                        results.append(contact)
                    
                except Exception as e:
                    continue
            
            return results[:max_results]
            
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
        
        business_type = actor_input.get('business_type', 'restaurantes')
        location = actor_input.get('location', 'Mexico City')
        max_results = actor_input.get('max_results', 20)
        
        # Inicializar scraper
        scraper = WhatsAppBusinessScraper()
        await scraper.init_browser()
        
        try:
            # Scrape
            businesses = await scraper.scrape_business_whatsapp(business_type, location, max_results)
            
            # Guardar resultados
            await Actor.push_data(businesses)
            
            # Log
            whatsapp_count = sum(1 for b in businesses if b.get('has_whatsapp'))
            await Actor.log.info(f"Scrapados {len(businesses)} negocios, {whatsapp_count} con WhatsApp")
            
        finally:
            await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
