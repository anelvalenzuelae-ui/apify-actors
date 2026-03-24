"""
Lead Generation Tool for Apify Store
Busca y extrae contactos de empresas mexicanas
Optimizado para B2B sales
"""

import asyncio
import json
import re
from typing import Optional, List, Dict
from datetime import datetime
from apify_client import ApifyClient
from playwright.async_api import async_playwright, Browser, Page

class LeadGenerationTool:
    """Herramienta para generar leads de empresas"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        
    async def init_browser(self):
        """Inicializar navegador Playwright"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        
    async def extract_emails(self, text: str) -> List[str]:
        """Extraer emails de texto"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    async def extract_phones(self, text: str) -> List[str]:
        """Extraer números telefónicos mexicanos"""
        phone_patterns = [
            r'\+52\s?\d{1,2}\s?\d{4}\s?\d{4}',  # +52 XX XXXX XXXX
            r'\+52\d{10}',  # +52XXXXXXXXXX
            r'\(?\d{2,3}\)?\s?\d{4}\s?\d{4}',  # (XX) XXXX XXXX
            r'\d{2,3}\s?\d{4}\s?\d{4}',  # XX XXXX XXXX
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))
    
    async def search_company_leads(self, industry: str, state: str = "Mexico", max_results: int = 20) -> List[Dict]:
        """
        Buscar leads de empresas
        
        Args:
            industry: Industria (ej: "tecnología", "construcción")
            state: Estado mexicano
            max_results: Máximo de resultados
            
        Returns:
            Lista de leads con contactos
        """
        page = await self.browser.new_page()
        
        try:
            # Buscar en directorios empresariales
            search_urls = [
                f"https://www.paginasamarillas.com.mx/search?q={industry}+{state}",
                f"https://www.empresas.com.mx/search?q={industry}",
            ]
            
            leads = []
            
            for search_url in search_urls:
                try:
                    await page.goto(search_url, wait_until="networkidle", timeout=10000)
                    
                    # Extraer empresas
                    companies = await page.evaluate("""
                    (maxResults) => {
                        const companies = [];
                        const items = document.querySelectorAll('[data-company-item], .company-item, .business-listing');
                        
                        items.forEach((item, idx) => {
                            if (idx < maxResults) {
                                const data = {};
                                
                                // Nombre
                                const nameEl = item.querySelector('h2, h3, .company-name');
                                data.name = nameEl ? nameEl.textContent.trim() : null;
                                
                                // Descripción
                                const descEl = item.querySelector('.description, p');
                                data.description = descEl ? descEl.textContent.trim() : null;
                                
                                // Teléfono
                                const phoneEl = item.querySelector('[data-phone], .phone');
                                data.phone = phoneEl ? phoneEl.textContent.trim() : null;
                                
                                // Email
                                const emailEl = item.querySelector('[data-email], .email');
                                data.email = emailEl ? emailEl.textContent.trim() : null;
                                
                                // Dirección
                                const addressEl = item.querySelector('[data-address], .address');
                                data.address = addressEl ? addressEl.textContent.trim() : null;
                                
                                // Sitio web
                                const websiteEl = item.querySelector('a[href*="http"]');
                                data.website = websiteEl ? websiteEl.getAttribute('href') : null;
                                
                                if (data.name) {
                                    companies.push(data);
                                }
                            }
                        });
                        
                        return companies;
                    }
                    """, max_results)
                    
                    leads.extend(companies)
                    
                except Exception as e:
                    continue
            
            # Enriquecer con información adicional
            enriched_leads = []
            for lead in leads[:max_results]:
                # Extraer emails y teléfonos del texto
                full_text = f"{lead.get('name', '')} {lead.get('description', '')} {lead.get('address', '')}"
                
                emails = await self.extract_emails(full_text)
                phones = await self.extract_phones(full_text)
                
                lead['emails'] = emails
                lead['phones'] = phones
                lead['industry'] = industry
                lead['state'] = state
                lead['scraped_at'] = datetime.now().isoformat()
                
                enriched_leads.append(lead)
            
            return enriched_leads
            
        finally:
            await page.close()
    
    async def search_linkedin_companies(self, company_name: str) -> Dict:
        """
        Buscar información de empresa en LinkedIn
        
        Args:
            company_name: Nombre de la empresa
            
        Returns:
            Datos de la empresa
        """
        page = await self.browser.new_page()
        
        try:
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
            await page.goto(search_url, wait_until="networkidle", timeout=10000)
            
            company_data = await page.evaluate("""
            () => {
                const data = {};
                
                const firstResult = document.querySelector('[data-test-id="company-card"]');
                if (firstResult) {
                    const nameEl = firstResult.querySelector('h3');
                    data.name = nameEl ? nameEl.textContent.trim() : null;
                    
                    const descEl = firstResult.querySelector('p');
                    data.description = descEl ? descEl.textContent.trim() : null;
                    
                    const followersEl = firstResult.querySelector('[data-test-id="followers"]');
                    data.followers = followersEl ? followersEl.textContent.trim() : null;
                }
                
                return data;
            }
            """)
            
            company_data['source'] = 'linkedin'
            company_data['scraped_at'] = datetime.now().isoformat()
            
            return company_data
            
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
        
        industry = actor_input.get('industry', 'tecnología')
        state = actor_input.get('state', 'Mexico')
        max_results = actor_input.get('max_results', 20)
        
        # Inicializar herramienta
        tool = LeadGenerationTool()
        await tool.init_browser()
        
        try:
            # Buscar leads
            leads = await tool.search_company_leads(industry, state, max_results)
            
            # Guardar resultados
            await Actor.push_data(leads)
            
            # Log
            await Actor.log.info(f"Generados {len(leads)} leads")
            
        finally:
            await tool.close()


if __name__ == "__main__":
    asyncio.run(main())
