# Guía de Publicación en Apify Store

Esta guía te ayudará a publicar tus Actors en Apify Store y comenzar a ganar dinero.

## 📋 Requisitos Previos

1. **Cuenta en Apify**
   - Usuario: `xerophylous_xyloidin`
   - Email: `anel.valenzuela.e@gmail.com`

2. **Apify CLI instalado**
   ```bash
   npm install -g apify-cli
   ```

3. **Autenticación en Apify**
   ```bash
   apify login
   ```

## 🚀 Publicación Automática

### Opción 1: Script Automático (Recomendado)

```bash
cd ~/apify-actors
./publish_actors.sh
```

Este script publicará automáticamente todos los 5 Actors.

### Opción 2: Publicación Manual

#### Paso 1: Publicar LinkedIn Scraper

```bash
cd linkedin-scraper
apify push
```

#### Paso 2: Publicar Google Maps Scraper

```bash
cd ../google-maps-scraper
apify push
```

#### Paso 3: Publicar Lead Generation Tool

```bash
cd ../lead-generation
apify push
```

#### Paso 4: Publicar Price Monitor

```bash
cd ../price-monitor
apify push
```

#### Paso 5: Publicar WhatsApp Scraper

```bash
cd ../whatsapp-scraper
apify push
```

## 💰 Configurar Pagos

### Paso 1: Acceder a Apify Console

1. Ve a https://console.apify.com
2. Inicia sesión con tu cuenta

### Paso 2: Configurar Método de Pago

1. Ve a **Settings** → **Billing**
2. Haz clic en **Add Payment Method**
3. Selecciona **PayPal**
4. Autoriza Apify para recibir pagos
5. Guarda los cambios

### Paso 3: Verificar Ganancias

1. Ve a **Account** → **Billing**
2. Verás un resumen de:
   - Ganancias del mes actual
   - Ganancias totales
   - Próxima fecha de pago

## 📊 Monitorear Rendimiento

### En Apify Console

1. Ve a **Actors** → Selecciona un Actor
2. Verás:
   - Número de ejecuciones
   - Resultados generados
   - Ingresos generados

### Estadísticas Importantes

- **Precio por resultado**: Configurado en `actor.json`
- **Comisión de Apify**: 20%
- **Tu ganancia**: 80%
- **Pago mínimo**: Varía según el método

## 🔄 Actualizar Actors

Si necesitas actualizar un Actor:

```bash
cd linkedin-scraper
# Edita el código
git add -A
git commit -m "Update LinkedIn scraper"
git push
apify push
```

## 📈 Estrategias para Aumentar Ingresos

### 1. Optimizar Precios
- Comienza con precios bajos para ganar usuarios
- Aumenta gradualmente según la demanda

### 2. Mejorar Descripción
- Usa palabras clave relevantes
- Incluye casos de uso específicos
- Agrega ejemplos de resultados

### 3. Mantener Calidad
- Responde comentarios de usuarios
- Corrige bugs rápidamente
- Actualiza regularmente

### 4. Promover Actors
- Comparte en redes sociales
- Escribe blog posts
- Participa en comunidades

## 🐛 Troubleshooting

### Error: "Not authenticated"
```bash
apify login
```

### Error: "Actor not found"
Verifica que `actor.json` existe en el directorio.

### Error: "Invalid configuration"
Revisa que `actor.json` tenga la estructura correcta.

### Error: "Build failed"
Revisa los logs:
```bash
apify logs
```

## 📞 Soporte

- **Documentación Apify**: https://docs.apify.com
- **Comunidad Apify**: https://apify.com/community
- **Email**: anel.valenzuela.e@gmail.com

## ✅ Checklist de Publicación

- [ ] Apify CLI instalado
- [ ] Autenticado en Apify
- [ ] Método de pago configurado
- [ ] Todos los Actors tienen `actor.json`
- [ ] Código probado localmente
- [ ] Descripción y precios configurados
- [ ] README actualizado
- [ ] Publicación completada
- [ ] Verificar en Apify Store

## 🎯 Próximos Pasos

1. Publicar todos los Actors
2. Esperar a que se indexen (24-48 horas)
3. Monitorear rendimiento
4. Optimizar basado en datos
5. Crear nuevos Actors

---

**Última actualización:** Marzo 2026
