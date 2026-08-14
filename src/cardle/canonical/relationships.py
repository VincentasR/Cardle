import re
from urllib.parse import unquote, urlsplit


def resolve_relationships(
    canonical_vehicles: list[dict],
) -> list[dict]:
    """
    Resolve predecessor/successor references across all
    canonicalized vehicle pages.

    Resolution uses:

    1. Explicit canonical Variant names/codes in relationship text.
    2. Wikipedia URL matching.
    3. Body style for ambiguous multi-variant relationships.
    4. Production chronology as a conservative filter.
    5. Source-specific mappings such as:
           E81/E87: F20/F21
           E82/E88: F22/F23
    6. Qualified relationship clauses such as:
           "(for body style)"
           "(for nameplate)"
    7. Shared Wikipedia pages where one chassis code is used
       as the article title for multiple related Variants.

    One raw relationship may resolve to multiple canonical
    relationships.

    If a target remains ambiguous, it stays unresolved rather
    than being guessed.
    """

    registry = build_variant_registry(
        canonical_vehicles
    )

    for page in canonical_vehicles:
        for variant in page.get(
            "variants",
            [],
        ):
            source_record = registry[
                "by_id"
            ].get(
                variant["id"]
            )

            if source_record is None:
                continue

            variant["predecessors"] = (
                _resolve_relationship_list(
                    source_record=source_record,
                    relationships=variant.get(
                        "predecessors",
                        [],
                    ),
                    registry=registry,
                    relation_kind="predecessor",
                )
            )

            variant["successors"] = (
                _resolve_relationship_list(
                    source_record=source_record,
                    relationships=variant.get(
                        "successors",
                        [],
                    ),
                    registry=registry,
                    relation_kind="successor",
                )
            )

    return canonical_vehicles


def build_variant_registry(
    canonical_vehicles: list[dict],
) -> dict:
    """
    Build registries used for cross-page relationship
    resolution.
    """

    by_id = {}
    by_name = {}
    by_url_exact = {}
    by_url_base = {}

    all_records = []

    for page in canonical_vehicles:
        model_id = page["model"]["id"]
        manufacturer_id = (
            page["manufacturer"]["id"]
        )

        for variant in page.get(
            "variants",
            [],
        ):
            body_style_ids = {
                body_style["id"]
                for body_style
                in variant.get(
                    "body_styles",
                    [],
                )
                if body_style.get("id")
            }

            record = {
                "id": variant["id"],
                "name": variant["name"],
                "model_id": model_id,
                "manufacturer_id": manufacturer_id,
                "source_url": variant.get(
                    "source_url"
                ),
                "body_style_ids": body_style_ids,
                "production_start": variant.get(
                    "production_start"
                ),
                "production_end": variant.get(
                    "production_end"
                ),
            }

            all_records.append(
                record
            )

            by_id[
                record["id"]
            ] = record

            name_key = (
                record["name"].casefold()
            )

            by_name.setdefault(
                name_key,
                [],
            ).append(
                record
            )

            source_url = record.get(
                "source_url"
            )

            if source_url:
                exact_key = _normalize_url(
                    source_url,
                    keep_fragment=True,
                )

                base_key = _normalize_url(
                    source_url,
                    keep_fragment=False,
                )

                if exact_key:
                    by_url_exact.setdefault(
                        exact_key,
                        [],
                    ).append(
                        record
                    )

                if base_key:
                    by_url_base.setdefault(
                        base_key,
                        [],
                    ).append(
                        record
                    )

    # Longest names first so that a longer/more-specific
    # Variant name is considered before a shorter one.
    variant_names = sorted(
        {
            record["name"]
            for record in all_records
            if record.get("name")
        },
        key=len,
        reverse=True,
    )

    return {
        "by_id": by_id,
        "by_name": by_name,
        "by_url_exact": by_url_exact,
        "by_url_base": by_url_base,
        "variant_names": variant_names,
    }


def _resolve_relationship_list(
    source_record: dict,
    relationships: list[dict],
    registry: dict,
    relation_kind: str,
) -> list[dict]:
    """
    Resolve all relationships of one type for one Variant.
    """

    resolved_relationships = []

    for relationship in relationships:

        # Values such as:
        #
        #   predecessor = "none"
        #
        # mean that no relationship exists at all.
        if _is_empty_relationship(
            relationship
        ):
            continue

        resolved = _resolve_one_relationship(
            source_record=source_record,
            relationship=relationship,
            registry=registry,
            relation_kind=relation_kind,
        )

        for item in resolved:
            if not _relationship_exists(
                resolved_relationships,
                item,
            ):
                resolved_relationships.append(
                    item
                )

    return resolved_relationships


def _resolve_one_relationship(
    source_record: dict,
    relationship: dict,
    registry: dict,
    relation_kind: str,
) -> list[dict]:
    """
    Resolve one raw predecessor/successor statement.
    """

    relationship_name = (
        relationship.get("name")
        or ""
    )

    relationship_url = (
        relationship.get("url")
    )

    # ---------------------------------------------------------
    # Source-specific mappings
    #
    # Example:
    #
    # E81/E87: 1 Series (F20/F21)
    # E82/E88: 2 Series (F22/F23)
    #
    # For E82 we should only inspect:
    #
    #     2 Series (F22/F23)
    # ---------------------------------------------------------

    relationship_scope = (
        _select_source_specific_scope(
            text=relationship_name,
            source_variant_name=source_record[
                "name"
            ],
        )
    )

    # ---------------------------------------------------------
    # Semantic qualifiers
    #
    # Example:
    #
    # BMW 6 Series (F06/F12/F13)
    #     (for body style)
    #
    # BMW 8 Series (E31)
    #     (for 8-series nameplate)
    #
    # These are separate semantic relationships.
    # ---------------------------------------------------------

    if _has_semantic_qualifiers(
        relationship_scope
    ):
        qualified_candidates = (
            _resolve_qualified_candidates(
                source_record=source_record,
                text=relationship_scope,
                registry=registry,
                relation_kind=relation_kind,
            )
        )

        if qualified_candidates:
            return [
                _make_resolved_relationship(
                    relationship,
                    candidate["id"],
                )
                for candidate
                in qualified_candidates
            ]

        # A qualified relationship should not fall through to
        # less-specific generic logic if its semantic clauses
        # could not be resolved confidently.
        return [
            _make_unresolved_relationship(
                relationship
            )
        ]

    # ---------------------------------------------------------
    # 1. Explicit Variant names/codes in relationship text
    # ---------------------------------------------------------

    text_candidates = (
        _find_named_candidates(
            relationship_scope,
            registry,
        )
    )

    text_candidates = (
        _remove_source_variant(
            text_candidates,
            source_record,
        )
    )

    # Chronology is used as a disambiguation signal.
    text_candidates = (
        _filter_by_relationship_direction(
            source_record=source_record,
            candidates=text_candidates,
            relation_kind=relation_kind,
        )
    )

    # ---------------------------------------------------------
    # 2. Wikipedia URL candidates
    # ---------------------------------------------------------

    url_candidates = (
        _find_url_candidates(
            relationship_url,
            registry,
        )
    )

    url_candidates = (
        _remove_source_variant(
            url_candidates,
            source_record,
        )
    )

    url_candidates = (
        _filter_by_relationship_direction(
            source_record=source_record,
            candidates=url_candidates,
            relation_kind=relation_kind,
        )
    )

    # ---------------------------------------------------------
    # Explicit text is stronger evidence than URL.
    # ---------------------------------------------------------

    if text_candidates:
        candidates = (
            _dedupe_candidates(
                text_candidates
            )
        )

        # -----------------------------------------------------
        # One explicitly named Variant may actually be the
        # title/code for a Wikipedia page containing several
        # body-code Variants.
        #
        # Example:
        #
        #     E61 wagon
        #         -> BMW 5 Series (F10)
        #
        # F10 itself is sedan, but the F10 article also
        # represents F11 wagon.
        # -----------------------------------------------------

        if len(candidates) == 1:
            shared_page_result = (
                _resolve_single_shared_page_candidate(
                    source_record=source_record,
                    candidates=candidates,
                    registry=registry,
                    relation_kind=relation_kind,
                )
            )

            if shared_page_result is None:
                return [
                    _make_unresolved_relationship(
                        relationship
                    )
                ]

            candidates = (
                shared_page_result
            )

        # -----------------------------------------------------
        # Multiple explicitly named candidates can often be
        # narrowed by body style.
        #
        # Example:
        #
        # E90 sedan
        #     -> F30/F31/F32/F33
        #
        # becomes:
        #
        # E90 -> F30
        # -----------------------------------------------------

        elif len(candidates) > 1:
            candidates = (
                _narrow_by_body_style(
                    source_record,
                    candidates,
                )
            )

        return [
            _make_resolved_relationship(
                relationship,
                candidate["id"],
            )
            for candidate
            in candidates
        ]

    # ---------------------------------------------------------
    # No known canonical Variant name was found.
    #
    # Before using URL-only matching, check whether the source
    # explicitly mentions a target-like chassis/model code.
    #
    # Example:
    #
    # raw says:
    #     BMW 4 Series (G22)
    #
    # dataset currently has only G26 on that Wikipedia page.
    #
    # We must NOT silently convert:
    #
    #     G22 -> G26
    # ---------------------------------------------------------

    explicit_tokens = (
        _extract_explicit_target_tokens(
            relationship_scope
        )
    )

    if explicit_tokens:
        return [
            _make_unresolved_relationship(
                relationship
            )
        ]

    # ---------------------------------------------------------
    # 3. URL-only resolution
    # ---------------------------------------------------------

    if len(url_candidates) == 1:
        return [
            _make_resolved_relationship(
                relationship,
                url_candidates[0]["id"],
            )
        ]

    if len(url_candidates) > 1:
        narrowed = (
            _narrow_by_body_style(
                source_record,
                url_candidates,
            )
        )

        if len(narrowed) == 1:
            return [
                _make_resolved_relationship(
                    relationship,
                    narrowed[0]["id"],
                )
            ]

        # Several Variants still fit the same Wikipedia page.
        # Do not guess.
        return [
            _make_unresolved_relationship(
                relationship
            )
        ]

    # ---------------------------------------------------------
    # Nothing could be resolved.
    # ---------------------------------------------------------

    return [
        _make_unresolved_relationship(
            relationship
        )
    ]


def _resolve_qualified_candidates(
    source_record: dict,
    text: str,
    registry: dict,
    relation_kind: str,
) -> list[dict]:
    """
    Resolve relationship text containing semantic qualifiers.

    Example:

        BMW 6 Series (F06/F12/F13)
            (for body style)

        BMW 8 Series (E31)
            (for 8-series nameplate)

    Body-style filtering applies only to the body-style clause.

    Nameplate relationships are retained independently.
    """

    clauses = (
        _split_semantic_clauses(
            text
        )
    )

    all_candidates = []

    for clause in clauses:
        candidates = (
            _find_named_candidates(
                clause,
                registry,
            )
        )

        candidates = (
            _remove_source_variant(
                candidates,
                source_record,
            )
        )

        candidates = (
            _filter_by_relationship_direction(
                source_record=source_record,
                candidates=candidates,
                relation_kind=relation_kind,
            )
        )

        if not candidates:
            continue

        clause_lower = (
            clause.lower()
        )

        # -----------------------------------------------------
        # Body-style-qualified relationship
        # -----------------------------------------------------

        if (
            "body style" in clause_lower
            or "body-style"
            in clause_lower
        ):

            if len(candidates) == 1:
                shared_page_result = (
                    _resolve_single_shared_page_candidate(
                        source_record=source_record,
                        candidates=candidates,
                        registry=registry,
                        relation_kind=relation_kind,
                        strict_body_style=True,
                    )
                )

                if shared_page_result is None:
                    # This clause remains ambiguous, but other
                    # qualified clauses such as "nameplate"
                    # may still resolve.
                    continue

                candidates = (
                    shared_page_result
                )

            else:
                candidates = (
                    _narrow_by_body_style(
                        source_record,
                        candidates,
                    )
                )

        # -----------------------------------------------------
        # Nameplate clauses deliberately do NOT use body-style
        # filtering.
        # -----------------------------------------------------

        all_candidates.extend(
            candidates
        )

    return _dedupe_candidates(
        all_candidates
    )


def _split_semantic_clauses(
    text: str,
) -> list[str]:
    """
    Split semantically qualified relationship statements.

    Handles both:

        "... (for body style), BMW ... (for nameplate)"

    and Wikipedia-flattened forms:

        "... (for body style) BMW ... (for nameplate)"
    """

    # Wikipedia extraction can flatten away separators between
    # relationship entries.
    #
    # Turn:
    #
    #     "(for body style) BMW ..."
    #
    # into:
    #
    #     "(for body style), BMW ..."
    #
    text = re.sub(
        r"\)\s*(?=BMW\b)",
        "), ",
        text,
        flags=re.IGNORECASE,
    )

    parts = re.split(
        r"\s*[,;]\s*(?=BMW\b)",
        text,
        flags=re.IGNORECASE,
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def _has_semantic_qualifiers(
    text: str,
) -> bool:
    """
    Detect relationship statements where different targets have
    different meanings.
    """

    text_lower = (
        text.lower()
    )

    return (
        "nameplate" in text_lower
        or "for body style"
        in text_lower
        or "for body-style"
        in text_lower
    )


def _filter_by_relationship_direction(
    source_record: dict,
    candidates: list[dict],
    relation_kind: str,
) -> list[dict]:
    """
    Remove candidates that are clearly chronologically
    incompatible with the relationship direction.

    This is deliberately conservative and is used mainly when
    several candidates exist.

    Example:

        F10 successor candidates:
            G30  -> begins later
            F07  -> same generation/start year

        therefore:
            keep G30
            remove F07
    """

    candidates = (
        _dedupe_candidates(
            candidates
        )
    )

    # Chronology should not override a single explicit source
    # relationship.
    if len(candidates) <= 1:
        return candidates

    source_start = source_record.get(
        "production_start"
    )

    if source_start is None:
        return candidates

    filtered = []

    for candidate in candidates:
        candidate_start = (
            candidate.get(
                "production_start"
            )
        )

        # Unknown dates are not evidence against a candidate.
        if candidate_start is None:
            filtered.append(
                candidate
            )
            continue

        if relation_kind == "successor":
            if (
                candidate_start
                <= source_start
            ):
                continue

        elif relation_kind == "predecessor":
            if (
                candidate_start
                >= source_start
            ):
                continue

        filtered.append(
            candidate
        )

    # Chronology alone must not erase all explicitly supplied
    # possibilities.
    if not filtered:
        return candidates

    return filtered


def _select_source_specific_scope(
    text: str,
    source_variant_name: str,
) -> str:
    """
    Extract the section of a composite relationship mapping
    that applies to the current source Variant.

    Example:

        E81/E87: 1 Series (F20/F21)
        E82/E88: 2 Series (F22/F23)

    For E82 this returns approximately:

        2 Series (F22/F23)
    """

    if not text:
        return text

    mapping_pattern = re.compile(
        r"(?P<label>"
        r"[A-Za-z0-9]+"
        r"(?:\s*/\s*[A-Za-z0-9]+)+"
        r")\s*:"
    )

    matches = list(
        mapping_pattern.finditer(
            text
        )
    )

    if not matches:
        return text

    source_key = (
        source_variant_name.casefold()
    )

    for index, match in enumerate(
        matches
    ):
        label = match.group(
            "label"
        )

        source_codes = {
            part.strip().casefold()
            for part in re.split(
                r"\s*/\s*",
                label,
            )
        }

        if (
            source_key
            not in source_codes
        ):
            continue

        start = match.end()

        if (
            index + 1
            < len(matches)
        ):
            end = matches[
                index + 1
            ].start()
        else:
            end = len(text)

        return text[
            start:end
        ].strip()

    return text


def _find_named_candidates(
    text: str,
    registry: dict,
) -> list[dict]:
    """
    Find known canonical Variant names appearing explicitly in
    relationship text.

    This avoids hard-coding BMW chassis-code patterns into the
    resolver itself.
    """

    if not text:
        return []

    matches = []

    for variant_name in registry[
        "variant_names"
    ]:
        pattern = (
            _variant_name_pattern(
                variant_name
            )
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        records = (
            registry[
                "by_name"
            ].get(
                variant_name.casefold(),
                [],
            )
        )

        for record in records:
            matches.append(
                (
                    match.start(),
                    record,
                )
            )

    # Preserve source-text target order.
    matches.sort(
        key=lambda item: item[0]
    )

    return _dedupe_candidates(
        [
            record
            for _, record
            in matches
        ]
    )


def _variant_name_pattern(
    variant_name: str,
) -> str:
    """
    Build a boundary-aware regex for a canonical Variant name.
    """

    escaped = re.escape(
        variant_name
    )

    # Allow flexible whitespace.
    escaped = escaped.replace(
        r"\ ",
        r"\s+",
    )

    prefix = ""
    suffix = ""

    if variant_name[0].isalnum():
        prefix = (
            r"(?<![A-Za-z0-9])"
        )

    if variant_name[-1].isalnum():
        suffix = (
            r"(?![A-Za-z0-9])"
        )

    return (
        prefix
        + escaped
        + suffix
    )


def _find_url_candidates(
    url: str | None,
    registry: dict,
) -> list[dict]:
    """
    Find canonical Variants represented by a Wikipedia URL.
    """

    if not url:
        return []

    # Prefer the exact URL including fragment.
    exact_key = _normalize_url(
        url,
        keep_fragment=True,
    )

    exact_candidates = (
        registry[
            "by_url_exact"
        ].get(
            exact_key,
            [],
        )
    )

    if exact_candidates:
        return (
            _dedupe_candidates(
                exact_candidates
            )
        )

    # Fall back to the article without its section fragment.
    base_key = _normalize_url(
        url,
        keep_fragment=False,
    )

    return _dedupe_candidates(
        registry[
            "by_url_base"
        ].get(
            base_key,
            [],
        )
    )


def _normalize_url(
    url: str,
    keep_fragment: bool,
) -> str:
    """
    Normalize Wikipedia URLs enough for stable comparison.

    This deliberately does not attempt to resolve Wikipedia
    redirects. Redirect/alias differences are handled using
    Variant names in relationship text.
    """

    if not url:
        return ""

    parsed = urlsplit(
        url.strip()
    )

    host = (
        parsed.netloc.casefold()
    )

    if host.startswith(
        "www."
    ):
        host = host[4:]

    path = unquote(
        parsed.path
    )

    path = path.replace(
        " ",
        "_",
    )

    path = re.sub(
        r"_+",
        "_",
        path,
    )

    result = (
        host
        + path.casefold()
    )

    if (
        keep_fragment
        and parsed.fragment
    ):
        result += (
            "#"
            + unquote(
                parsed.fragment
            ).casefold()
        )

    return result


def _resolve_single_shared_page_candidate(
    source_record: dict,
    candidates: list[dict],
    registry: dict,
    relation_kind: str,
    strict_body_style: bool = False,
) -> list[dict] | None:
    """
    Handle a relationship that explicitly names one Variant
    code which is also being used as the title/code for a
    multi-Variant Wikipedia page.

    Example:

        E61 wagon
            -> "BMW 5 Series (F10)"

    F10's page contains:

        F07
        F10 sedan
        F11 wagon

    The explicitly named F10 conflicts with E61's wagon body
    style, so inspect sibling Variants represented by that same
    Wikipedia page.

    If exactly one known sibling matches the source body style,
    use that sibling.

    Otherwise:

        - for an ordinary explicit relationship, preserve the
          explicitly named candidate;

        - for a relationship explicitly qualified as
          "for body style", return None so the relationship
          remains unresolved rather than contradicting the
          qualifier.

    Body style is therefore normally a disambiguation signal,
    not a reason to discard explicit source evidence.
    """

    candidates = (
        _dedupe_candidates(
            candidates
        )
    )

    if len(candidates) != 1:
        return candidates

    candidate = candidates[0]

    # --------------------------------------------------------
    # The explicitly named target already agrees with the
    # source body style.
    #
    # No reinterpretation is necessary.
    # --------------------------------------------------------

    if not _body_styles_conflict(
        source_record,
        candidate,
    ):
        return candidates

    candidate_url = candidate.get(
        "source_url"
    )

    # --------------------------------------------------------
    # We know the explicit target conflicts by body style, but
    # there is no shared-page evidence available to identify a
    # better sibling.
    #
    # Ordinary relationship:
    #     preserve explicit target.
    #
    # Explicit "(for body style)" relationship:
    #     remain unresolved.
    # --------------------------------------------------------

    if not candidate_url:
        if strict_body_style:
            return None

        return candidates

    # --------------------------------------------------------
    # Find every canonical Variant represented by the same
    # Wikipedia article.
    # --------------------------------------------------------

    page_candidates = (
        _find_url_candidates(
            candidate_url,
            registry,
        )
    )

    # Sibling expansion must stay inside the same canonical
    # Model.
    page_candidates = [
        item
        for item
        in page_candidates
        if item["model_id"]
        == candidate["model_id"]
    ]

    page_candidates = (
        _filter_by_relationship_direction(
            source_record=source_record,
            candidates=page_candidates,
            relation_kind=relation_kind,
        )
    )

    # --------------------------------------------------------
    # There are no actual sibling alternatives.
    # --------------------------------------------------------

    if len(page_candidates) <= 1:
        if strict_body_style:
            return None

        return candidates

    # --------------------------------------------------------
    # Look for siblings whose KNOWN body styles overlap the
    # source body styles.
    # --------------------------------------------------------

    body_matches = (
        _known_body_style_matches(
            source_record,
            page_candidates,
        )
    )

    # Exactly one body-style-compatible sibling is strong
    # enough evidence to reinterpret the article-title code.
    if len(body_matches) == 1:
        return body_matches

    # --------------------------------------------------------
    # Zero or multiple body-style matches.
    #
    # For ordinary explicit relationships, the explicitly
    # named target remains stronger evidence than body-style
    # disagreement.
    #
    # For "(for body style)" clauses, however, ambiguity or
    # disagreement means we cannot resolve the clause.
    # --------------------------------------------------------

    if strict_body_style:
        return None

    return candidates


def _resolve_qualified_candidates(
    source_record: dict,
    text: str,
    registry: dict,
    relation_kind: str,
) -> list[dict]:
    """
    Resolve relationship text containing semantic qualifiers.

    Example:

        BMW 6 Series (F06/F12/F13)
            (for body style)

        BMW 8 Series (E31)
            (for 8-series nameplate)

    Body-style filtering applies only to the body-style clause.

    Nameplate relationships are retained independently.
    """

    clauses = _split_semantic_clauses(
        text
    )

    all_candidates = []

    for clause in clauses:
        candidates = (
            _find_named_candidates(
                clause,
                registry,
            )
        )

        candidates = (
            _remove_source_variant(
                candidates,
                source_record,
            )
        )

        candidates = (
            _filter_by_relationship_direction(
                source_record=source_record,
                candidates=candidates,
                relation_kind=relation_kind,
            )
        )

        if not candidates:
            continue

        clause_lower = (
            clause.lower()
        )

        # -----------------------------------------------------
        # Body-style-qualified relationship
        # -----------------------------------------------------

        if (
            "body style" in clause_lower
            or "body-style"
            in clause_lower
        ):

            if len(candidates) == 1:
                shared_page_result = (
                    _resolve_single_shared_page_candidate(
                        source_record=source_record,
                        candidates=candidates,
                        registry=registry,
                        relation_kind=relation_kind,
                        strict_body_style=True,
                    )
                )

                if shared_page_result is None:
                    # This clause remains ambiguous, but other
                    # qualified clauses such as "nameplate"
                    # may still resolve.
                    continue

                candidates = (
                    shared_page_result
                )

            else:
                candidates = (
                    _narrow_by_body_style(
                        source_record,
                        candidates,
                    )
                )

        # -----------------------------------------------------
        # Nameplate clauses deliberately do NOT use body-style
        # filtering.
        # -----------------------------------------------------

        all_candidates.extend(
            candidates
        )

    return _dedupe_candidates(
        all_candidates
    )


def _known_body_style_matches(
    source_record: dict,
    candidates: list[dict],
) -> list[dict]:
    """
    Return candidates with KNOWN body styles overlapping the
    source body styles.

    Candidates with missing body-style data are ignored rather
    than treated as matches or mismatches.
    """

    source_styles = (
        source_record.get(
            "body_style_ids",
            set(),
        )
    )

    if not source_styles:
        return []

    return [
        candidate
        for candidate in candidates
        if (
            candidate.get(
                "body_style_ids"
            )
            and (
                source_styles
                & candidate[
                    "body_style_ids"
                ]
            )
        )
    ]


def _narrow_by_body_style(
    source_record: dict,
    candidates: list[dict],
) -> list[dict]:
    """
    Narrow ambiguous candidates using body style.

    Candidates may belong to different Models.

    Example:

        E90 sedan
            candidates:
                F30 sedan
                F31 wagon
                F32 coupe
                F33 convertible

            result:
                F30

    If candidate body-style data is incomplete, do not use the
    missing data as evidence.
    """

    candidates = (
        _dedupe_candidates(
            candidates
        )
    )

    if len(candidates) <= 1:
        return candidates

    source_styles = (
        source_record.get(
            "body_style_ids",
            set(),
        )
    )

    if not source_styles:
        return candidates

    # Missing body-style data means we don't know enough to
    # safely eliminate that candidate.
    if any(
        not candidate.get(
            "body_style_ids"
        )
        for candidate in candidates
    ):
        return candidates

    matching = [
        candidate
        for candidate in candidates
        if (
            source_styles
            & candidate[
                "body_style_ids"
            ]
        )
    ]

    if matching:
        return matching

    return candidates


def _body_styles_conflict(
    source_record: dict,
    candidate: dict,
) -> bool:
    """
    Return True only when both sides have known body-style data
    and the sets do not overlap.
    """

    source_styles = (
        source_record.get(
            "body_style_ids",
            set(),
        )
    )

    candidate_styles = (
        candidate.get(
            "body_style_ids",
            set(),
        )
    )

    if (
        not source_styles
        or not candidate_styles
    ):
        return False

    return not bool(
        source_styles
        & candidate_styles
    )


def _extract_explicit_target_tokens(
    text: str,
) -> set[str]:
    """
    Detect target-like identifiers even when no corresponding
    canonical Variant exists.

    Examples:

        E28
        F22
        G22
        U11
        NA0
        I01
        319/1
        507

    This protects against using an unrelated/shared Wikipedia
    URL candidate when the relationship text explicitly names
    a different target.
    """

    if not text:
        return set()

    tokens = set()

    # Letter/digit platform-like identifiers.
    for match in re.finditer(
        r"\b[A-Za-z]{1,3}\d{1,3}"
        r"[A-Za-z0-9]*\b",
        text,
    ):
        tokens.add(
            match.group(0).casefold()
        )

    # Older numeric vehicle/model identifiers.
    for match in re.finditer(
        r"\b\d{3,4}"
        r"(?:/\d+)?\b",
        text,
    ):
        token = match.group(0)

        # Avoid treating ordinary years as vehicle identifiers.
        numeric_prefix = (
            token.split(
                "/",
                1,
            )[0]
        )

        if numeric_prefix.isdigit():
            number = int(
                numeric_prefix
            )

            if 1900 <= number <= 2099:
                continue

        tokens.add(
            token.casefold()
        )

    return tokens


def _remove_source_variant(
    candidates: list[dict],
    source_record: dict,
) -> list[dict]:
    """
    Prevent accidental self-relationships.
    """

    return [
        candidate
        for candidate in candidates
        if candidate["id"]
        != source_record["id"]
    ]


def _dedupe_candidates(
    candidates: list[dict],
) -> list[dict]:
    """
    Deduplicate candidate Variants while preserving order.
    """

    result = []
    seen = set()

    for candidate in candidates:
        candidate_id = (
            candidate["id"]
        )

        if candidate_id in seen:
            continue

        seen.add(
            candidate_id
        )

        result.append(
            candidate
        )

    return result


def _make_resolved_relationship(
    relationship: dict,
    target_id: str,
) -> dict:
    """
    Create one canonical resolved relationship.
    """

    return {
        "name": relationship.get(
            "name"
        ),
        "url": relationship.get(
            "url"
        ),
        "target_id": target_id,
    }


def _make_unresolved_relationship(
    relationship: dict,
) -> dict:
    """
    Preserve a source relationship even when its canonical
    target cannot be identified confidently.
    """

    return {
        "name": relationship.get(
            "name"
        ),
        "url": relationship.get(
            "url"
        ),
        "target_id": None,
    }


def _relationship_exists(
    relationships: list[dict],
    candidate: dict,
) -> bool:
    """
    Check whether an identical canonical relationship has
    already been emitted.
    """

    key = (
        candidate.get("name"),
        candidate.get("url"),
        candidate.get(
            "target_id"
        ),
    )

    for existing in relationships:
        existing_key = (
            existing.get("name"),
            existing.get("url"),
            existing.get(
                "target_id"
            ),
        )

        if existing_key == key:
            return True

    return False


def _is_empty_relationship(
    relationship: dict,
) -> bool:
    """
    Detect source values meaning that no relationship exists.

    Example:

        predecessor = "none"

    should become:

        "predecessors": []

    rather than an unresolved relationship with target_id null.
    """

    name = (
        relationship.get("name")
        or ""
    ).strip().lower()

    url = relationship.get("url")

    empty_values = {
        "",
        "none",
        "n/a",
        "na",
        "not applicable",
        "no predecessor",
        "no successor",
    }

    return (
        name in empty_values
        and not url
    )