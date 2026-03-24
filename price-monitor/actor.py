"""
E-commerce Price Monitor for Apify Store
Monitorea precios en Mercado Libre, Amazon MX y otros marketplaces
Optimizado para mercado mexicano
"""

import asyncio
import json
from typing import Optional, List, Dict
from datetime import datetime
from apify_client import ApifyClient
from playwright.async_api import async_playwright, Browser, Page

class PriceMonitor:
    """Monitor de precios en e-commerce"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        
    async def init_browser(self):
        """Inicializar navegador Playwright"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        
    async def scrape_mercado_libre(self, product_name: str, max_results: int = 20) -> List[Dict]:
        """
        Scrape productos de Mercado Libre
        
        Args:
            product_name: Nombre del producto
            max_results: Máximo de resultados
            
        Returns:
            Lista de productos con precios
        """
        page = await self.browser.new_page()
        
        try:
            # Buscar en Mercado Libre México
            search_url = f"https://listado.mercadolibre.com.mx/{product_name}"
            await page.goto(search_url, wait_until="networkidle")
            
            products = await page.evaluate("""
            (maxResults) => {
                const products = [];
                const items = document.querySelectorAll('ol > li');
                
                items.forEach((item, idx) => {
                    if (idx < maxResults) {
                        const data = {};
                        
                        // Título
                        const titleEl = item.querySelector('h2 a');
                        data.title = titleEl ? titleEl.textContent.trim() : null;
                        data.url = titleEl ? titleEl.getAttribute('href') : null;
                        
                        // Precio
                        const priceEl = item.querySelector('.price-tag-fraction');
                        data.price = priceEl ? priceEl.textContent.trim() : null;
                        
                        // Moneda
                        const currencyEl = item.querySelector('.price-tag-symbol');
                        data.currency = currencyEl ? currencyEl.textContent.trim() : null;
                        
                        // Condición (nuevo/usado)
                        const conditionEl = item.querySelector('[data-condition]');
                        data.condition = conditionEl ? conditionEl.textContent.trim() : null;
                        
                        // Vendedor
                        const sellerEl = item.querySelector('[data-seller-name]');
                        data.seller = sellerEl ? sellerEl.textContent.trim() : null;
                        
                        // Rating
                        const ratingEl = item.querySelector('[data-rating]');
                        data.rating = ratingEl ? ratingEl.getAttribute('data-rating') : null;
                        
                        // Envío
                        const shippingEl = item.querySelector('[data-shipping]');
                        data.shipping = shippingEl ? shippingEl.textContent.trim() : null;
                        
                        // Stock
                        const stockEl = item.querySelector('[data-stock]');
                        data.stock = stockEl ? stockEl.textContent.trim() : null;
                        
                        if (data.title && data.price) {
                            products.push(data);
                        }
                    }
                });
                
                return products;
            }
            """, max_results)
            
            # Agregar metadata
            for product in products:
                product['marketplace'] = 'Mercado Libre'
                product['country'] = 'Mexico'
                product['scraped_at'] = datetime.now().isoformat()
            
            return products
            
        except Exception as e:
            return []
        finally:
            await page.close()
    
    async def scrape_amazon_mx(self, product_name: str, max_results: int = 20) -> List[Dict]:
        """
        Scrape productos de Amazon México
        
        Args:
            product_name: Nombre del producto
            max_results: Máximo de resultados
            
        Returns:
            Lista de productos con precios
        """
        page = await self.browser.new_page()
        
        try:
            # Buscar en Amazon México
            search_url = f"https://www.amazon.com.mx/s?k={product_name}"
            await page.goto(search_url, wait_until="networkidle")
            
            products = await page.evaluate("""
            (maxResults) => {
                const products = [];
                const items = document.querySelectorAll('[data-component-type="s-search-result"]');
                
                items.forEach((item, idx) => {
                    if (idx < maxResults) {
                        const data = {};
                        
                        // Título
                        const titleEl = item.querySelector('h2 a span');
                        data.title = titleEl ? titleEl.textContent.trim() : null;
                        data.url = item.querySelector('h2 a') ? item.querySelector('h2 a').getAttribute('href') : null;
                        
                        // Precio
                        const priceEl = item.querySelector('.a-price-whole');
                        data.price = priceEl ? priceEl.textContent.trim() : null;
                        
                        // Moneda
                        data.currency = '$';
                        
                        // Rating
                        const ratingEl = item.querySelector('.a-icon-star span');
                        data.rating = ratingEl ? ratingEl.textContent.trim() : null;
                        
                        // Número de reviews
                        const reviewsEl = item.querySelector('[data-a-popover] span');
                        data.reviews_count = reviewsEl ? reviewsEl.textContent.trim() : null;
                        
                        // Prime
                        const primeEl = item.querySelector('[aria-label*="Prime"]');
                        data.has_prime = primeEl ? true : false;
                        
                        if (data.title && data.price) {
                            products.push(data);
                        }
                    }
                });
                
                return products;
            }
            """, max_results)
            
            # Agregar metadata
            for product in products:
                product['marketplace'] = 'Amazon'
                product['country'] = 'Mexico'
                product['scraped_at'] = datetime.now().isoformat()
            
            return products
            
        except Exception as e:
            return []
        finally:
            await page.close()
    
    async def compare_prices(self, product_name: str, max_results: int = 10) -> Dict:
        """
        Comparar precios del mismo producto en múltiples marketplaces
        
        Args:
            product_name: Nombre del producto
            max_results: Máximo de resultados por marketplace
            
        Returns:
            Comparación de precios
        """
        ml_products = await self.scrape_mercado_libre(product_name, max_results)
        amazon_products = await self.scrape_amazon_mx(product_name, max_results)
        
        comparison = {
            'product': product_name,
            'mercado_libre': ml_products,
            'amazon': amazon_products,
            'comparison_date': datetime.now().isoformat(),
            'cheapest_option': None
        }
        
        # Encontrar opción más barata
        all_products = ml_products + amazon_products
        if all_products:
            cheapest = min(all_products, key=lambda x: float(x.get('price', '0').replace('$', '').replace(',', '')))
            comparison['cheapest_option'] = cheapest
        
        return comparison
    
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
        
        product_name = actor_input.get('product_name', 'laptop')
        max_results = actor_input.get('max_results', 20)
        compare_prices = actor_input.get('compare_prices', True)
        
        # Inicializar monitor
        monitor = PriceMonitor()
        await monitor.init_browser()
        
        try:
            if compare_prices:
                # Comparar precios
                result = await monitor.compare_prices(product_name, max_results)
                await Actor.push_data([result])
            else:
                # Solo Mercado Libre
                products = await monitor.scrape_mercado_libre(product_name, max_results)
                await Actor.push_data(products)
            
            # Log
            await Actor.log.info(f"Monitoreo completado para: {product_name}")
            
        finally:
            await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
