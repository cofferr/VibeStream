"""Cubre FuzzySearchStrategy._filter_objects: la lógica de fuzzy matching
(rapidfuzz) y el orden por similitud que usan song/album/artist search.
No necesita una BD real — opera sobre objetos en memoria, que es todo lo
que _filter_objects toca."""

from types import SimpleNamespace

from strategies.fuzzy_strategy import FuzzySearchStrategy


def make(id_, title):
    return SimpleNamespace(id=id_, title=title)


async def test_exact_match_is_included():
    strategy = FuzzySearchStrategy(threshold=70)
    objs = [make(1, "Bohemian Rhapsody")]

    result = await strategy._filter_objects(objs, "Bohemian Rhapsody", "title")

    assert result == objs


async def test_typo_still_matches_above_threshold():
    strategy = FuzzySearchStrategy(threshold=70)
    objs = [make(1, "Bohemian Rhapsody")]

    result = await strategy._filter_objects(objs, "bohemian rapsody", "title")

    assert result == objs


async def test_unrelated_query_is_excluded():
    strategy = FuzzySearchStrategy(threshold=70)
    objs = [make(1, "Bohemian Rhapsody")]

    result = await strategy._filter_objects(objs, "completamente distinto xyz", "title")

    assert result == []


async def test_results_ordered_by_similarity_descending():
    # ambos del mismo largo que la query para que partial_ratio se
    # comporte como un ratio normal (con largos distintos, rapidfuzz
    # desliza una ventana y puede encontrar una coincidencia perfecta de
    # substring aunque el resto del texto difiera del todo)
    strategy = FuzzySearchStrategy(threshold=10)
    exact = make(1, "Bohemian Rhapsody")
    scrambled = make(2, "Bohemiam Rhapsooy")

    result = await strategy._filter_objects([scrambled, exact], "Bohemian Rhapsody", "title")

    assert result == [exact, scrambled]


async def test_object_missing_field_is_skipped_not_crashed():
    """Un objeto sin el campo (getattr devuelve None) no debe romper el
    resto de la búsqueda — se salta en silencio (loggeado), no crashea."""
    strategy = FuzzySearchStrategy(threshold=70)
    broken = SimpleNamespace(id=1)  # sin atributo "title"
    ok = make(2, "Bohemian Rhapsody")

    result = await strategy._filter_objects([broken, ok], "Bohemian Rhapsody", "title")

    assert result == [ok]


async def test_threshold_is_respected():
    strategy = FuzzySearchStrategy(threshold=95)
    objs = [make(1, "Bohemian Rhapsody")]

    # una consulta parecida pero no lo suficiente para el threshold alto
    result = await strategy._filter_objects(objs, "bohemian rap", "title")

    assert result == []
