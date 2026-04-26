"""
Remy Recipe Pipeline
====================
scrape → LLM extract (Pydantic schema) → post-process (normalize, filter, dedupe)

Architecture mirrors shubham-tequity/recipe-to-cart but adapted for Python.
The key insight from the reference: use a PERMISSIVE schema for LLM output,
then normalize + re-validate against a STRICT schema. This prevents one bad
ingredient (e.g. unit="strand") from blowing up the entire extraction.
"""

import re
import json
import httpx
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from shared.llm_provider import get_llm_response, parse_json_response
from agent_skills.remy.prompts import (
    RECIPE_EXTRACTION_SYSTEM_PROMPT,
    RECIPE_EXTRACTION_SYSTEM_PROMPT_FULL,
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CanonicalUnit(str, Enum):
    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    TSP = "tsp"
    TBSP = "tbsp"
    CUP = "cup"
    PIECE = "piece"
    PINCH = "pinch"
    HANDFUL = "handful"
    TO_TASTE = "to_taste"
    WHOLE = "whole"


# Non-shoppable items to filter out
NON_SHOPPABLE = frozenset([
    "water", "hot water", "cold water", "boiling water", "warm water",
    "ice", "ice cubes", "salt and pepper",  # too generic
])

# Unit normalization — maps LLM inventions to canonical units
UNIT_NORMALIZATION: dict[str, str] = {
    # Exotic units → piece
    "strand": "piece", "blade": "piece", "stick": "piece",
    "stalk": "piece", "sprig": "piece", "sheet": "piece",
    "leaf": "piece", "leaves": "piece", "knob": "piece",
    "bunch": "piece", "pod": "piece", "pack": "piece",
    "slice": "piece", "clove": "piece", "cloves": "piece",
    "flake": "piece", "flakes": "piece",
    # dash → pinch
    "dash": "pinch",
    # long-form → abbreviated
    "teaspoon": "tsp", "teaspoons": "tsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp",
    "gram": "g", "grams": "g",
    "kilogram": "kg", "kilograms": "kg",
    "milliliter": "ml", "milliliters": "ml", "millilitre": "ml",
    "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    "cups": "cup",
    "pinches": "pinch",
    "pieces": "piece",
    "handful": "handful", "handfuls": "handful",
    # ambiguous catch-alls
    "unit": "piece", "units": "piece",
    "number": "piece", "nos": "piece", "no": "piece",
    "": "piece",
}

VALID_UNITS = {u.value for u in CanonicalUnit}


class LLMIngredient(BaseModel):
    """Permissive schema — accepts any unit string from LLM."""
    name: str
    original_name: str
    quantity: Optional[float] = None
    unit: str = "piece"
    notes: Optional[str] = None
    optional: bool = False


class LLMRecipe(BaseModel):
    """Permissive schema for raw LLM output."""
    title: str
    servings: Optional[int] = None
    ingredients: list[LLMIngredient]


class Ingredient(BaseModel):
    """Strict schema — unit must be canonical."""
    name: str
    original_name: str
    quantity: Optional[float] = None
    unit: CanonicalUnit = CanonicalUnit.PIECE
    notes: Optional[str] = None
    optional: bool = False

    @field_validator("unit", mode="before")
    @classmethod
    def normalize_unit(cls, v: str) -> str:
        v = v.strip().lower()
        # Direct canonical match
        if v in VALID_UNITS:
            return v
        # Normalization table
        normalized = UNIT_NORMALIZATION.get(v)
        if normalized:
            return normalized
        # Unknown unit → piece (safe fallback)
        return "piece"


class ParsedRecipe(BaseModel):
    title: str
    source_url: str
    servings: Optional[int] = None
    ingredients: list[Ingredient]
    source_type: str = "unknown"


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

MAX_CONTENT_CHARS = 15_000

SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; Roomie-Remy/1.0; "
        "+https://github.com/zooperic/roomie)"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


async def _fetch_url(url: str) -> str:
    """Fetch HTML from URL. Raises on failure with a human-readable message."""
    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers=SCRAPE_HEADERS,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except httpx.TimeoutException:
        raise ValueError(f"Took too long to load that page — it might be down. Try a different recipe link?")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"The page returned an error ({e.response.status_code}). Is the link correct?")
    except Exception as e:
        raise ValueError(f"Couldn't reach that page. Check the link and try again.")


def _extract_from_json_ld(html: str) -> tuple[str, Optional[int], str]:
    """
    Try to extract title, servings, and ingredient list from schema.org JSON-LD.
    Returns (title, servings, content) — content is empty string if not found.
    """
    # Simple regex to find JSON-LD blocks — avoids pulling in BeautifulSoup
    script_pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE,
    )

    for match in script_pattern.finditer(html):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        recipe = _find_recipe_node(data)
        if not recipe:
            continue

        title = recipe.get("name", "")
        servings = _parse_servings(recipe.get("recipeYield"))
        ingredients: list[str] = recipe.get("recipeIngredient", [])

        if ingredients:
            content = "INGREDIENTS:\n" + "\n".join(str(i) for i in ingredients)
            return title, servings, content

    return "", None, ""


def _find_recipe_node(data) -> Optional[dict]:
    """Recursively find the first node with @type == Recipe."""
    if isinstance(data, list):
        for item in data:
            found = _find_recipe_node(item)
            if found:
                return found
        return None

    if not isinstance(data, dict):
        return None

    type_val = data.get("@type", "")
    is_recipe = type_val == "Recipe" or (isinstance(type_val, list) and "Recipe" in type_val)
    if is_recipe:
        return data

    # Check @graph
    graph = data.get("@graph", [])
    if isinstance(graph, list):
        for item in graph:
            found = _find_recipe_node(item)
            if found:
                return found

    return None


def _parse_servings(value) -> Optional[int]:
    if isinstance(value, (int, float)) and value > 0:
        return int(value)
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return int(match.group())
    if isinstance(value, list) and value:
        return _parse_servings(value[0])
    return None


def _strip_html_to_text(html: str) -> str:
    """
    Very lightweight HTML→text stripper without BeautifulSoup.
    Removes tags, collapses whitespace.
    """
    # Remove script/style blocks
    html = re.sub(r"<(script|style|nav|footer|header|aside|noscript|iframe)[^>]*>.*?</\1>",
                  "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all remaining tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    html = re.sub(r"\s+", " ", html).strip()
    return html[:MAX_CONTENT_CHARS]


async def scrape_recipe_url(url: str) -> tuple[str, Optional[int], str]:
    """
    Scrape a recipe URL.
    Returns (title, servings, content) where content is the ingredient text
    ready to pass to the LLM.
    """
    import time as _time
    print(f"[Remy scrape] Fetching: {url[:80]}")
    t0 = _time.time()
    html = await _fetch_url(url)
    print(f"[Remy scrape] Fetched {len(html)} chars in {_time.time() - t0:.1f}s")

    # Prefer schema.org JSON-LD (most Indian recipe blogs publish this)
    title, servings, content = _extract_from_json_ld(html)
    if content:
        print(f"[Remy scrape] ✓ JSON-LD found | title={title!r} | servings={servings} | content_chars={len(content)}")
        return title, servings, content

    print(f"[Remy scrape] ✗ no JSON-LD — falling back to raw HTML text")
    # Fallback: strip HTML, send raw text
    text = _strip_html_to_text(html)

    # Try to get title from OG meta tag
    og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if og_title:
        title = og_title.group(1)
    elif not title:
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if h1:
            title = re.sub(r"<[^>]+>", "", h1.group(1)).strip()

    print(f"[Remy scrape] fallback result | title={title!r} | text_chars={len(text)}")
    return title or "Recipe", servings, text


# ---------------------------------------------------------------------------
# LLM Extraction
# ---------------------------------------------------------------------------

async def extract_ingredients_from_content(
    title: str,
    source_url: str,
    content: str,
    source_type: str,
    original_servings: Optional[int] = None,
    target_servings: Optional[int] = None,
) -> ParsedRecipe:
    """
    Core extraction: sends content to LLM with the system prompt.
    Uses slim prompt for text/dish (clean content, fewer tokens needed).
    Uses full prompt for URL scraping (messy HTML, needs more disambiguation).
    """
    # Slim prompt: ~395 tokens. Full prompt: ~1499 tokens.
    # URL mode gets messy blog HTML with ads, nav, comments mixed in — needs full rules.
    # Text/dish mode content is already clean — slim prompt is enough.
    system_prompt = (
        RECIPE_EXTRACTION_SYSTEM_PROMPT_FULL
        if source_type == "url"
        else RECIPE_EXTRACTION_SYSTEM_PROMPT
    )
    servings_line = (
        f"Original servings in recipe: {original_servings}."
        if original_servings
        else "Original servings not specified."
    )
    target_line = (
        f"Target servings requested by user: {target_servings}. Scale all quantities linearly from the original."
        if target_servings
        else ""
    )

    prompt = (
        f"Recipe title: {title}\n"
        f"Source: {source_url}\n"
        f"{servings_line}\n"
        f"{target_line}\n\n"
        f"Recipe content:\n\"\"\"\n{content}\n\"\"\""
    )

    import time as _time
    prompt_label = "slim" if source_type != "url" else "full"
    print(f"[Remy pipeline] ── Starting extraction ──────────────────────────")
    print(f"[Remy pipeline] source={source_type} | servings={target_servings} | prompt={prompt_label} | content_chars={len(content)}")
    print(f"[Remy pipeline] content preview: {content[:150].strip()!r}{'...' if len(content)>150 else ''}")
    t0 = _time.time()

    raw = await get_llm_response(
        prompt=prompt,
        system=system_prompt,
        json_mode=True,
        max_tokens=3000,       # needs headroom for large ingredient lists
        task_type="chat",      # llama3.1:8b on Ollama — fast, capable for structured extraction
    )
    print(f"[Remy pipeline] LLM extraction done in {_time.time() - t0:.1f}s, response len={len(raw)}")

    parsed_data = parse_json_response(raw)

    # Parse into permissive schema first (won't reject on bad units)
    llm_recipe = LLMRecipe(**parsed_data)

    # Normalize units → validate into strict schema
    ingredients = []
    for ing in llm_recipe.ingredients:
        strict_ing = Ingredient(
            name=ing.name,
            original_name=ing.original_name,
            quantity=ing.quantity,
            unit=ing.unit,  # field_validator normalizes this
            notes=ing.notes,
            optional=ing.optional,
        )
        ingredients.append(strict_ing)

    # Post-processing pipeline
    ingredients = _filter_non_shoppable(ingredients)
    ingredients = _dedupe(ingredients)

    result = ParsedRecipe(
        title=llm_recipe.title or title,
        source_url=source_url,
        servings=target_servings or llm_recipe.servings or original_servings,
        ingredients=ingredients,
        source_type=source_type,
    )
    print(f"[Remy pipeline] ── Extraction complete ─────────────────────────")
    print(f"[Remy pipeline] title={result.title!r} | servings={result.servings} | ingredients={len(result.ingredients)}")
    for ing in result.ingredients:
        qty_str = f"{ing.quantity} {ing.unit.value}" if ing.quantity else ing.unit.value
        print(f"[Remy pipeline]   {qty_str:15s} {ing.name}")
    return result


# ---------------------------------------------------------------------------
# Post-processing
# ---------------------------------------------------------------------------

def _filter_non_shoppable(ingredients: list[Ingredient]) -> list[Ingredient]:
    """Drop water and other non-shoppable items."""
    return [
        ing for ing in ingredients
        if ing.name.lower().strip() not in NON_SHOPPABLE
        and not (ing.name.lower() in ("salt", "pepper", "black pepper")
                 and ing.unit == CanonicalUnit.TO_TASTE)
    ]


def _dedupe(ingredients: list[Ingredient]) -> list[Ingredient]:
    """
    Collapse duplicate ingredient names. When the same ingredient appears
    twice (e.g. garlic in marinade + garlic in sauce), sum the quantities
    if they share the same unit, otherwise keep both (different unit forms).
    """
    seen: dict[str, Ingredient] = {}
    result: list[Ingredient] = []

    for ing in ingredients:
        key = ing.name.lower().strip()
        if key in seen:
            existing = seen[key]
            if (existing.unit == ing.unit
                    and existing.quantity is not None
                    and ing.quantity is not None):
                # Merge: sum quantity
                merged = existing.model_copy(
                    update={"quantity": existing.quantity + ing.quantity}
                )
                # Update in result list
                idx = result.index(existing)
                result[idx] = merged
                seen[key] = merged
            # else: different units — keep both (don't merge grams + pieces)
        else:
            seen[key] = ing
            result.append(ing)

    return result


# ---------------------------------------------------------------------------
# Public entry points (called by RemyAgent)
# ---------------------------------------------------------------------------

async def pipeline_from_url(
    url: str,
    target_servings: Optional[int] = None,
) -> ParsedRecipe:
    """Full pipeline: URL → scrape → extract → post-process."""
    title, original_servings, content = await scrape_recipe_url(url)
    if not content:
        raise ValueError("Couldn't find any ingredients on that page. Is it a recipe link?")
    return await extract_ingredients_from_content(
        title=title,
        source_url=url,
        content=content,
        source_type="url",
        original_servings=original_servings,
        target_servings=target_servings,
    )


async def pipeline_from_text(
    text: str,
    target_servings: Optional[int] = None,
) -> ParsedRecipe:
    """Pipeline for pasted recipe text — skip scraping."""
    print(f"[Remy pipeline] mode=text | chars={len(text)} | servings={target_servings}")
    print(f"[Remy pipeline] text preview: {text[:100].strip()!r}{'...' if len(text)>100 else ''}")
    return await extract_ingredients_from_content(
        title="Pasted Recipe",
        source_url="pasted",
        content=text,
        source_type="text",
        target_servings=target_servings,
    )


async def pipeline_from_dish_name(
    dish_name: str,
    target_servings: Optional[int] = None,
) -> ParsedRecipe:
    """
    Pipeline for dish name only.
    Uses a tighter prompt than the full URL pipeline — the LLM generates
    a standard recipe from training knowledge. Faster than reasoning model.
    """
    servings_line = f"Make it for {target_servings} servings." if target_servings else "Use 4 servings as default."
    content = (
        f"List the ingredients needed to make: {dish_name}\n"
        f"{servings_line}\n"
        f"Include quantities for each ingredient. This is an Indian household recipe context."
    )
    return await extract_ingredients_from_content(
        title=dish_name,
        source_url="dish_name",
        content=content,
        source_type="dish_name",
        target_servings=target_servings,
    )
