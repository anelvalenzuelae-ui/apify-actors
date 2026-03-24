#!/bin/bash

# Script para publicar todos los Actors en Apify Store
# Uso: ./publish_actors.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Apify Actors Publisher ===${NC}"
echo ""

# Verificar que Apify CLI está instalado
if ! command -v apify &> /dev/null; then
    echo -e "${RED}Error: Apify CLI no está instalado${NC}"
    echo "Instálalo con: npm install -g apify-cli"
    exit 1
fi

# Verificar que estamos autenticados
echo -e "${YELLOW}Verificando autenticación...${NC}"
if ! apify info &> /dev/null; then
    echo -e "${RED}Error: No estás autenticado en Apify${NC}"
    echo "Ejecuta: apify login"
    exit 1
fi

echo -e "${GREEN}✓ Autenticado en Apify${NC}"
echo ""

# Array de Actors
ACTORS=(
    "linkedin-scraper"
    "google-maps-scraper"
    "lead-generation"
    "price-monitor"
    "whatsapp-scraper"
)

# Publicar cada Actor
for actor in "${ACTORS[@]}"; do
    echo -e "${YELLOW}Publicando: $actor${NC}"
    
    if [ -d "$actor" ]; then
        cd "$actor"
        
        # Verificar que existe actor.json
        if [ ! -f "actor.json" ]; then
            echo -e "${RED}✗ Error: No existe actor.json en $actor${NC}"
            cd ..
            continue
        fi
        
        # Publicar
        if apify push; then
            echo -e "${GREEN}✓ $actor publicado exitosamente${NC}"
        else
            echo -e "${RED}✗ Error al publicar $actor${NC}"
        fi
        
        cd ..
    else
        echo -e "${RED}✗ Directorio $actor no encontrado${NC}"
    fi
    
    echo ""
done

echo -e "${GREEN}=== Publicación completada ===${NC}"
echo ""
echo "Tus Actors están disponibles en:"
echo "https://apify.com/store?search=xerophylous_xyloidin"
echo ""
echo "Para ver ganancias:"
echo "https://console.apify.com/account/billing"
