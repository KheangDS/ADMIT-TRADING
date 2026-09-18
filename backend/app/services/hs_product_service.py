from typing import Dict, Tuple, Optional

# Official 4-Digit HS Chapter Titles — Bilingual (English + Khmer)
HS4_OFFICIAL_MAP: Dict[str, Dict[str, str]] = {
    "0801": {
        "title_en": "Cashew Nuts & Coconuts",
        "title_km": "គ្រាប់ស្វាយចន្ទី និងដូង",
        "full_desc_en": "Coconuts, Brazil nuts and cashew nuts, fresh or dried, whether or not shelled or peeled.",
        "full_desc_km": "ដូង គ្រាប់ប្រេស៊ីល និងគ្រាប់ស្វាយចន្ទី ស្រស់ ឬ ស្ងួត មានសំបក ឬ គ្មានសំបក ឬ បោះសំបកចេញ។"
    },
    "0804": {
        "title_en": "Fresh & Dried Mangoes",
        "title_km": "ស្វាយ និងផ្លែឈើស្ងួត",
        "full_desc_en": "Dates, figs, pineapples, avocados, guavas, mangoes and mangosteens, fresh or dried.",
        "full_desc_km": "ល្មើត ល្វា ម្នាស់ អាវូកាដូ ត្របែក ស្វាយ និងមង្គុត ស្រស់ ឬ ស្ងួត។"
    },
    "0904": {
        "title_en": "Pepper & Chili (Capsicum)",
        "title_km": "ម្រេច និងម្ទេស (Capsicum)",
        "full_desc_en": "Pepper of the genus Piper; dried or crushed or ground fruits of the genus Capsicum or of the genus Pimenta.",
        "full_desc_km": "ម្រេចពូជ Piper; ផ្លែស្ងួត ទន្ទក់ ឬ កិន នៃពូជ Capsicum ឬ Pimenta។"
    },
    "0910": {
        "title_en": "Ginger, Turmeric & Spices",
        "title_km": "ខ្ញី រមៀត និងគ្រឿងទេស",
        "full_desc_en": "Ginger, saffron, turmeric (curcuma), thyme, bay leaves, curry and other spices.",
        "full_desc_km": "ខ្ញី សាហ្វរ៉ង់ រមៀត ថាយម៍ ស្លឹកបៃ ការី និងគ្រឿងទេសផ្សេងៗ។"
    },
    "1211": {
        "title_en": "Medicinal & Perfumery Plants",
        "title_km": "រុក្ខជាតិឱសថ និងរុក្ខជាតិក្លិន",
        "full_desc_en": "Plants and parts of plants (including seeds and fruits), of a kind used primarily in perfumery, in pharmacy or for insecticidal, fungicidal or similar purposes, fresh, chilled, frozen or dried, whether or not cut, crushed or powdered.",
        "full_desc_km": "រុក្ខជាតិ និងផ្នែករបស់រុក្ខជាតិ (រួមទាំងគ្រាប់ និងផ្លែ) ប្រើជាចម្បងក្នុងការផលិតទឹកអប់ ឱសថ ឬសម្រាប់សម្លាប់សត្វល្អិត ផ្សិត ឬប្រើប្រាស់ស្រដៀងគ្នា ស្រស់ ត្រជាក់ ទឹកកក ឬ ស្ងួត មានការកាត់ កិន ឬ ទន្ទក់ ឬ គ្មាន។"
    }
}

# Official 8-Digit Tariff Code Mappings — Bilingual (English + Khmer)
HS8_PRODUCT_NAME_MAP: Dict[str, Dict[str, str]] = {

    # ===== Head 0801 (Coconuts, Brazil nuts & Cashew nuts) =====
    "08011100": {"en": "Coconuts - Desiccated", "km": "ដូង - ស្ងួតកិន"},
    "08011200": {"en": "Coconuts - In the inner shell (endocarp)", "km": "ដូង - ក្នុងសំបកខាងក្នុង"},
    "08011910": {"en": "Coconuts - Young coconut", "km": "ដូង - ដូងខ្ចី"},
    "08011990": {"en": "Coconuts - Other", "km": "ដូង - ផ្សេងទៀត"},
    "08012100": {"en": "Brazil nuts - In shell", "km": "គ្រាប់ប្រេស៊ីល - ក្នុងសំបក"},
    "08012200": {"en": "Brazil nuts - Shelled", "km": "គ្រាប់ប្រេស៊ីល - បកសំបកចេញ"},
    "08013100": {"en": "Cashew nuts - In shell", "km": "គ្រាប់ស្វាយចន្ទី - ក្នុងសំបក"},
    "08013200": {"en": "Cashew nuts - Shelled", "km": "គ្រាប់ស្វាយចន្ទី - បកសំបកចេញ"},

    # ===== Head 0804 (Dates, figs, pineapples, avocados, guavas, mangoes) =====
    "08041000": {"en": "Dates - Fresh or dried", "km": "ល្មើត - ស្រស់ ឬ ស្ងួត"},
    "08042000": {"en": "Figs - Fresh or dried", "km": "ល្វា - ស្រស់ ឬ ស្ងួត"},
    "08043000": {"en": "Pineapples - Fresh or dried", "km": "ម្នាស់ - ស្រស់ ឬ ស្ងួត"},
    "08044000": {"en": "Avocados - Fresh or dried", "km": "អាវូកាដូ - ស្រស់ ឬ ស្ងួត"},
    "08045010": {"en": "Guavas - Fresh or dried", "km": "ត្របែក - ស្រស់ ឬ ស្ងួត"},
    "08045021": {"en": "Mangoes - Fresh", "km": "ស្វាយ - ស្រស់"},
    "08045022": {"en": "Mangoes - Dried", "km": "ស្វាយ - ស្ងួត"},
    "08045030": {"en": "Mangosteens - Fresh or dried", "km": "មង្គុត - ស្រស់ ឬ ស្ងួត"},

    # ===== Head 0904 (Pepper & Capsicum / Chili) =====
    "09041110": {"en": "Pepper (Piper) - White, unground", "km": "ម្រេច (Piper) - ស, មិនកិន"},
    "09041120": {"en": "Pepper (Piper) - Black, unground", "km": "ម្រេច (Piper) - ខ្មៅ, មិនកិន"},
    "09041190": {"en": "Pepper (Piper) - Other, unground", "km": "ម្រេច (Piper) - ផ្សេងទៀត, មិនកិន"},
    "09041210": {"en": "Pepper (Piper) - White, crushed or ground", "km": "ម្រេច (Piper) - ស, កិន ឬកិនម៉ដ៍"},
    "09041220": {"en": "Pepper (Piper) - Black, crushed or ground", "km": "ម្រេច (Piper) - ខ្មៅ, កិន ឬកិនម៉ដ៍"},
    "09041290": {"en": "Pepper (Piper) - Other, crushed or ground", "km": "ម្រេច (Piper) - ផ្សេងទៀត, កិន ឬកិនម៉ដ៍"},
    "09042110": {"en": "Chili (Capsicum) - Dried, unground", "km": "ម្ទេស (Capsicum) - ស្ងួត, មិនកិន"},
    "09042190": {"en": "Chili/Pimenta - Other, dried, unground", "km": "ម្ទេស/ភីម៉ិនតា - ផ្សេងទៀត, ស្ងួត, មិនកិន"},
    "09042210": {"en": "Chili (Capsicum) - Crushed or ground", "km": "ម្ទេស (Capsicum) - កិន ឬកិនម៉ដ៍"},
    "09042290": {"en": "Chili (Capsicum) - Other crushed or ground", "km": "ម្ទេស (Capsicum) - ផ្សេងទៀត, កិន ឬកិនម៉ដ៍"},

    # ===== Head 0910 (Ginger, saffron, turmeric, thyme, curry) =====
    "09101100": {"en": "Ginger - Neither crushed nor ground", "km": "ខ្ញី - មិនកិន"},
    "09101200": {"en": "Ginger - Crushed or ground", "km": "ខ្ញី - កិន ឬកិនម៉ដ៍"},
    "09102000": {"en": "Saffron", "km": "សាហ្វរ៉ង់"},
    "09103000": {"en": "Turmeric (curcuma)", "km": "រមៀត"},
    "09109110": {"en": "Curry spice mixtures", "km": "គ្រឿងផ្សំការី"},
    "09109190": {"en": "Other spice mixtures", "km": "គ្រឿងផ្សំគ្រឿងទេស - ផ្សេងទៀត"},
    "09109910": {"en": "Thyme; bay leaves", "km": "ថាយម៍; ស្លឹកបៃ"},
    "09109990": {"en": "Other spices - Other", "km": "គ្រឿងទេសផ្សេងទៀត - ផ្សេងទៀត"},

    # ===== Head 1211 (Medicinal & Aromatic Plants) =====
    "12112010": {"en": "Ginseng roots - Fresh or dried", "km": "ឫសយិនសិន - ស្រស់ ឬ ស្ងួត"},
    "12112090": {"en": "Ginseng roots - Other", "km": "ឫសយិនសិន - ផ្សេងទៀត"},
    "12113000": {"en": "Coca leaf", "km": "ស្លឹកកូកា"},
    "12114000": {"en": "Poppy straw", "km": "គាំសរអាភៀន"},
    "12115000": {"en": "Ephedra", "km": "អេហ្វេដ្រា"},
    "12116000": {"en": "Bark of African cherry (Prunus africana)", "km": "សំបកឈើឆេរីអាហ្វ្រិក (Prunus africana)"},
    "12119011": {"en": "Cannabis - Cut, crushed or powdered", "km": "កញ្ឆា - កាត់, កិន ឬកិនម៉ដ៍"},
    "12119012": {"en": "Cannabis - Other forms", "km": "កញ្ឆា - ទម្រង់ផ្សេងទៀត"},
    "12119013": {"en": "Rauwolfia serpentina roots", "km": "ឫសរ៉ូវូលហ្វៀ (Rauwolfia serpentina)"},
    "12119015": {"en": "Liquorice roots", "km": "ឫសជីអង្កាម"},
    "12119017": {"en": "Other pharmacy plants - Fresh or dried, cut/crushed/powdered", "km": "រុក្ខជាតិឱសថផ្សេងទៀត - ស្រស់ ឬស្ងួត, កាត់/កិន/កិនម៉ដ៍"},
    "12119018": {"en": "Other pharmacy plants - Cut, crushed or powdered", "km": "រុក្ខជាតិឱសថផ្សេងទៀត - កាត់, កិន ឬកិនម៉ដ៍"},
    "12119019": {"en": "Other pharmacy plants - Other", "km": "រុក្ខជាតិឱសថផ្សេងទៀត - ផ្សេងទៀត"},
    "12119091": {"en": "Pyrethrum - Cut, crushed or powdered", "km": "ភីរីទ្រូម - កាត់, កិន ឬកិនម៉ដ៍"},
    "12119092": {"en": "Pyrethrum - Other forms", "km": "ភីរីទ្រូម - ទម្រង់ផ្សេងទៀត"},
    "12119094": {"en": "Sandalwood chips", "km": "បន្ទះឈើចន្ទន៍"},
    "12119095": {"en": "Agarwood (Gaharu) chips", "km": "បន្ទះឈើគ្រំ (ហ្គារូ)"},
    "12119097": {"en": "Bark of persea (Persea kurzii Kosterm)", "km": "សំបកឈើពែរស៊ា (Persea kurzii Kosterm)"},
    "12119098": {"en": "Other (non-pharmacy) - Cut, crushed or powdered", "km": "ផ្សេងទៀត (មិនមែនឱសថ) - កាត់, កិន ឬកិនម៉ដ៍"},
    "12119099": {"en": "Other (non-pharmacy) - Other", "km": "ផ្សេងទៀត (មិនមែនឱសថ) - ផ្សេងទៀត"},

    # Backward-compat alias (old code used 12119090, now mapped to nearest)
    "12119090": {"en": "Other plants - Other", "km": "រុក្ខជាតិ (ប្រភេទផ្សេង) - ផ្សេងទៀត"},
    "12119010": {"en": "Medicinal plants - Used in pharmacy", "km": "រុក្ខជាតិឱសថ - ប្រើក្នុងឱសថ"},
}

# Raw vs Processed pairs within the same HS4 chapter
# Key = hs4_code, value = list of (raw_hs8, processed_hs8) pairs
RAW_VS_PROCESSED_PAIRS: Dict[str, list] = {
    "0801": [
        ("08013100", "08013200"),  # Cashew in-shell (raw) vs shelled (processed)
    ],
    "0804": [
        ("08045021", "08045022"),  # Fresh mango (raw) vs dried mango (processed)
    ],
}


def get_hs4_official_name(hs4_code: str, raw_desc: str = "") -> Tuple[str, str, str, str]:
    """
    Returns (title_en, title_km, full_desc_en, full_desc_km) for an HS4 chapter.
    Falls back to raw_desc if code not in map.
    """
    clean_code = str(hs4_code).replace('.0', '').zfill(4)
    if clean_code in HS4_OFFICIAL_MAP:
        info = HS4_OFFICIAL_MAP[clean_code]
        return (
            info["title_en"],
            info["title_km"],
            info["full_desc_en"],
            info["full_desc_km"],
        )

    desc = raw_desc.strip() if raw_desc else f"Agricultural Chapter HS {clean_code}"
    short = desc[:40]
    return short, short, desc, desc


def get_product_name(hs8_code: str, raw_description: str = "", lang: Optional[str] = None) -> str:
    """
    Returns the product name for an 8-digit HS code.
    - lang='en'  → English only (default for backward compatibility)
    - lang='km'  → Khmer only
    - lang=None  → English only (backward compat)
    Falls back to a clean excerpt of raw_description if code is not mapped.
    """
    clean_code = str(hs8_code).replace('.0', '').zfill(8)
    target_lang = lang if lang in ("en", "km") else "en"

    if clean_code in HS8_PRODUCT_NAME_MAP:
        return HS8_PRODUCT_NAME_MAP[clean_code][target_lang]

    if raw_description:
        desc = str(raw_description).strip()
        if len(desc) > 50:
            return desc[:50] + "..."
        return desc

    return f"Product Code {clean_code}"


def get_product_names_bilingual(hs8_code: str, raw_description: str = "") -> Dict[str, str]:
    """
    Returns {"en": "...", "km": "..."} for an 8-digit HS code.
    Falls back to raw_description or code placeholder if not mapped.
    """
    clean_code = str(hs8_code).replace('.0', '').zfill(8)

    if clean_code in HS8_PRODUCT_NAME_MAP:
        return dict(HS8_PRODUCT_NAME_MAP[clean_code])

    fallback_en = raw_description.strip()[:50] if raw_description else f"Product Code {clean_code}"
    return {"en": fallback_en, "km": fallback_en}


def get_raw_processed_pair(hs4_code: str, hs8_code: str) -> Optional[Dict]:
    """
    If this hs8_code belongs to a raw-vs-processed pair within its hs4_code,
    returns {"raw_hs8": "...", "processed_hs8": "...", "is_raw": bool, "is_processed": bool}.
    Returns None if no pairing applies.
    """
    clean_hs4 = str(hs4_code).replace('.0', '').zfill(4)
    clean_hs8 = str(hs8_code).replace('.0', '').zfill(8)

    pairs = RAW_VS_PROCESSED_PAIRS.get(clean_hs4, [])
    for raw_hs8, processed_hs8 in pairs:
        if clean_hs8 in (raw_hs8, processed_hs8):
            return {
                "raw_hs8": raw_hs8,
                "processed_hs8": processed_hs8,
                "is_raw": clean_hs8 == raw_hs8,
                "is_processed": clean_hs8 == processed_hs8,
            }
    return None
