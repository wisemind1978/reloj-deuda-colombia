# Reloj de la Deuda Nacional de Colombia

Página web pública que muestra la deuda del Gobierno Nacional Central de Colombia
y otros indicadores macroeconómicos, con contadores que corren al segundo.

Inspirado en el [U.S. National Debt Clock](https://www.usdebtclock.org/), pero para Colombia.

## ⚠️ Cómo leer las cifras

Los números **corren al segundo, pero NO son streaming en vivo** de las entidades.
Son **proyecciones lineales** calibradas con el dato oficial más reciente. La deuda
pública se publica con 1–2 meses de rezago, así que el reloj muestra siempre la fecha
del último dato oficial + una proyección sobre la tasa de crecimiento observada.

La única cifra realmente en vivo es la **TRM (dólar)**, que se consulta a diario desde
la API oficial de datos.gov.co.

## Fuentes oficiales

| Indicador | Fuente |
|---|---|
| Deuda GNC, composición | Ministerio de Hacienda |
| TRM (dólar) | datos.gov.co (Superintendencia Financiera) |
| PIB, población, hogares | DANE |
| Tasa de política, inflación | Banco de la República / DANE |
| Calificación soberana | S&P, Moody's, Fitch |
| Cultivos de coca | UNODC · SIMCI |

## Cómo se mantiene actualizado

Una **GitHub Action** (`.github/workflows/actualizar-datos.yml`) corre a diario,
consulta las fuentes con API disponible y actualiza `data.json`, que el sitio lee
para renderizar. Los datos sin API (la mayoría) se actualizan manualmente cuando las
entidades publican.

## Estructura

```
index.html   · el reloj (HTML/CSS/JS vanilla, sin frameworks)
data.json    · todos los datos (lo que el robot y los humanos actualizan)
assets/      · imágenes
scripts/     · los "cerebros" que leen las fuentes (Python, solo stdlib)
.github/     · la automatización (GitHub Actions)
```

## Aviso

Proyecto cívico de transparencia. **No está afiliado a ninguna entidad gubernamental.**
Para cifras exactas a una fecha dada, consulte directamente las fuentes oficiales.
