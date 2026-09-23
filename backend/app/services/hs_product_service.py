import re
from typing import Dict, Tuple, Optional, Any

# ============================================================
# 1. TEXT & CODE CLEANING UTILITIES
# ============================================================

def clean_text(value: Any) -> str:
    """Remove zero-width spaces, normalize non-breaking spaces, trim."""
    if value is None:
        return ""
    return (
        str(value)
        .replace("\u200b", "")
        .replace("\xa0", " ")
        .strip()
    )

def clean_hs_code(value: Any, digits: int) -> str:
    """Convert Excel-style numeric HS codes into fixed-width strings."""
    if value is None:
        return ""
    val_str = str(value).strip()
    if not val_str:
        return ""
    try:
        numeric_value = float(val_str)
        if numeric_value.is_integer():
            val_str = str(int(numeric_value))
    except (TypeError, ValueError):
        pass
    if "." in val_str:
        val_str = val_str.split(".")[0]
    val_str = "".join(ch for ch in val_str if ch.isdigit())
    if not val_str:
        return ""
    return val_str.zfill(digits)[-digits:]

# ============================================================
# 2. HS8 PRODUCT KNOWLEDGE BASE (ASEAN AHTN 2022 / Cambodian Customs)
# ============================================================

HS8_MAPPING: Dict[str, Dict[str, str]] = {
    # Chapter 04: Dairy produce; natural honey
    "04090000": {
        "category_en": "Natural Honey",
        "category_kh": "ទឹកឃ្មុំធម្មជាតិ",
        "name_en": "Natural Honey",
        "name_kh": "ទឹកឃ្មុំធម្មជាតិ",
    },

    # Chapter 08: Edible Fruit and Nuts
    "08011100": {
        "category_en": "Coconuts",
        "category_kh": "ដូង",
        "name_en": "Coconuts: Desiccated",
        "name_kh": "ដូង ៖ ដកជាតិទឹក",
    },
    "08011200": {
        "category_en": "Coconuts",
        "category_kh": "ដូង",
        "name_en": "Coconuts: In the inner shell (endocarp)",
        "name_kh": "ដូង ៖ មានត្រឡោកដូង (endocarp)",
    },
    "08011910": {
        "category_en": "Coconuts",
        "category_kh": "ដូង",
        "name_en": "Coconuts: Young coconut",
        "name_kh": "ដូង ៖ ដូងខ្ចី",
    },
    "08011990": {
        "category_en": "Coconuts",
        "category_kh": "ដូង",
        "name_en": "Coconuts: Other",
        "name_kh": "ដូង ៖ ផ្សេងទៀត",
    },
    "08012100": {
        "category_en": "Brazil Nuts",
        "category_kh": "គ្រាប់ផ្លែប្រេស៊ីល",
        "name_en": "Brazil Nuts: In shell",
        "name_kh": "គ្រាប់ផ្លែប្រេស៊ីល ៖ មានសម្បក",
    },
    "08012200": {
        "category_en": "Brazil Nuts",
        "category_kh": "គ្រាប់ផ្លែប្រេស៊ីល",
        "name_en": "Brazil Nuts: Shelled",
        "name_kh": "គ្រាប់ផ្លែប្រេស៊ីល ៖ បកសម្បករួច",
    },
    "08013100": {
        "category_en": "Cashew Nuts",
        "category_kh": "គ្រាប់ស្វាយចន្ទី",
        "name_en": "Cashew Nuts: In Shell",
        "name_kh": "គ្រាប់ស្វាយចន្ទី ៖ មានសម្បក",
    },
    "08013200": {
        "category_en": "Cashew Nuts",
        "category_kh": "គ្រាប់ស្វាយចន្ទី",
        "name_en": "Cashew Nuts: Shelled",
        "name_kh": "គ្រាប់ស្វាយចន្ទី ៖ បកសម្បករួច",
    },
    "08041000": {
        "category_en": "Dates",
        "category_kh": "ល្ម៉ើ",
        "name_en": "Dates",
        "name_kh": "ល្ម៉ើ",
    },
    "08042000": {
        "category_en": "Figs",
        "category_kh": "ល្វា",
        "name_en": "Figs",
        "name_kh": "ល្វា",
    },
    "08043000": {
        "category_en": "Pineapples",
        "category_kh": "ម្នាស់",
        "name_en": "Pineapples",
        "name_kh": "ម្នាស់",
    },
    "08044000": {
        "category_en": "Avocados",
        "category_kh": "អាវ៉ូកាដូ",
        "name_en": "Avocados",
        "name_kh": "អាវ៉ូកាដូ",
    },
    "08045010": {
        "category_en": "Guavas",
        "category_kh": "ត្របែក",
        "name_en": "Guavas",
        "name_kh": "ត្របែក",
    },
    "08045021": {
        "category_en": "Mango Products",
        "category_kh": "ស្វាយ",
        "name_en": "Mangoes: Fresh",
        "name_kh": "ស្វាយ ៖ ស្រស់",
    },
    "08045022": {
        "category_en": "Mango Products",
        "category_kh": "ស្វាយ",
        "name_en": "Mangoes: Dried",
        "name_kh": "ស្វាយ ៖ ស្ងួត",
    },
    "08045030": {
        "category_en": "Mangosteens",
        "category_kh": "មង្ឃុត",
        "name_en": "Mangosteens",
        "name_kh": "មង្ឃុត",
    },

    # Chapter 09: Coffee, Tea, Maté and Spices
    "09041110": {
        "category_en": "Pepper",
        "category_kh": "ម្រេច",
        "name_en": "White Pepper, Neither Crushed nor Ground",
        "name_kh": "ម្រេចស (មិនទាន់បុក ឬកិន)",
    },
    "09041120": {
        "category_en": "Pepper",
        "category_kh": "ម្រេច",
        "name_en": "Black Pepper, Neither Crushed nor Ground",
        "name_kh": "ម្រេចខ្មៅ (មិនទាន់បុក ឬកិន)",
    },
    "09041190": {
        "category_en": "Pepper",
        "category_kh": "ម្រេច",
        "name_en": "Other Pepper, Neither Crushed nor Ground",
        "name_kh": "ម្រេចផ្សេងទៀត (មិនទាន់បុក ឬកិន)",
    },
    "09041210": {
        "category_en": "Pepper",
        "category_kh": "ម្រេច",
        "name_en": "White Pepper, Crushed or Ground",
        "name_kh": "ម្រេចស (បុក ឬកិនរួច)",
    },
    "09041220": {
        "category_en": "Pepper",
        "category_kh": "ម្រេច",
        "name_en": "Black Pepper, Crushed or Ground",
        "name_kh": "ម្រេចខ្មៅ (បុក ឬកិនរួច)",
    },
    "09041290": {
        "category_en": "Pepper",
        "category_kh": "ម្រេច",
        "name_en": "Other Pepper, Crushed or Ground",
        "name_kh": "ម្រេចផ្សេងទៀត (បុក ឬកិនរួច)",
    },
    "09042110": {
        "category_en": "Chilli Products",
        "category_kh": "ម្ទេស",
        "name_en": "Chillies (Capsicum), Dried, Neither Crushed nor Ground",
        "name_kh": "ម្ទេស (ផ្លែម្ទេសប្រភេទ Capsicum) ក្រៀម មិនទាន់បុក ឬកិន",
    },
    "09042190": {
        "category_en": "Chilli Products",
        "category_kh": "ម្ទេស",
        "name_en": "Other Chilli Products, Dried, Neither Crushed nor Ground",
        "name_kh": "ម្ទេស ឬម្រេចប្រភេទផ្សេងទៀត ក្រៀម មិនទាន់បុក ឬកិន",
    },
    "09042210": {
        "category_en": "Chilli Products",
        "category_kh": "ម្ទេស",
        "name_en": "Chillies (Capsicum), Crushed or Ground",
        "name_kh": "ម្ទេស (ផ្លែម្ទេសប្រភេទ Capsicum) បុក ឬកិនរួច",
    },
    "09042290": {
        "category_en": "Chilli Products",
        "category_kh": "ម្ទេស",
        "name_en": "Other Chilli Products, Crushed or Ground",
        "name_kh": "ម្ទេស ឬម្រេចប្រភេទផ្សេងទៀត (បុក ឬកិនរួច)",
    },
    "09101100": {
        "category_en": "Ginger & Turmeric",
        "category_kh": "ខ្ញី និងរមៀត",
        "name_en": "Ginger: Neither crushed nor ground",
        "name_kh": "ខ្ញី ៖ មិនទាន់បុក ឬកិន",
    },
    "09101200": {
        "category_en": "Ginger & Turmeric",
        "category_kh": "ខ្ញី និងរមៀត",
        "name_en": "Ginger: Crushed or ground",
        "name_kh": "ខ្ញី ៖ បុក ឬកិនរួច",
    },
    "09102000": {
        "category_en": "Spices & Herbs",
        "category_kh": "គ្រឿងទេស",
        "name_en": "Saffron",
        "name_kh": "Saffron",
    },
    "09103000": {
        "category_en": "Ginger & Turmeric",
        "category_kh": "ខ្ញី និងរមៀត",
        "name_en": "Turmeric (curcuma)",
        "name_kh": "រមៀត (curcuma)",
    },
    "09109110": {
        "category_en": "Spices & Herbs",
        "category_kh": "គ្រឿងទេស",
        "name_en": "Spices: Curry",
        "name_kh": "គ្រឿងទេស ៖ ការី",
    },
    "09109190": {
        "category_en": "Spices & Herbs",
        "category_kh": "គ្រឿងទេស",
        "name_en": "Spice Mixtures: Other",
        "name_kh": "ល្បាយគ្រឿងទេស ៖ ផ្សេងទៀត",
    },
    "09109910": {
        "category_en": "Spices & Herbs",
        "category_kh": "គ្រឿងទេស",
        "name_en": "Thyme; bay leaves",
        "name_kh": "ស្លឹក Thyme; ស្លឹក bay",
    },
    "09109990": {
        "category_en": "Spices & Herbs",
        "category_kh": "គ្រឿងទេស",
        "name_en": "Other Spices: Other",
        "name_kh": "គ្រឿងទេសផ្សេងទៀត ៖ ផ្សេងទៀត",
    },

    # Chapter 12: Oil Seeds, Medicinal Plants
    "12112010": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Ginseng roots: Fresh or dried",
        "name_kh": "ប្ញសយ៉ិនស៊ិន ៖ ស្រស់ ឬក្រៀម",
    },
    "12112090": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Ginseng roots: Other",
        "name_kh": "ប្ញសយ៉ិនស៊ិន ៖ ផ្សេងទៀត",
    },
    "12113000": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Coca leaf",
        "name_kh": "ស្លឹកកូកា",
    },
    "12114000": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Poppy straw",
        "name_kh": "ដើមអាភៀន",
    },
    "12115000": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Ephedra",
        "name_kh": "ដើម Ephedra",
    },
    "12116000": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Bark of African cherry (Prunus africana)",
        "name_kh": "សំបកដើមឈើអាហ្វ្រិច (Prunus africana)",
    },
    "12119011": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Cannabis: In cut, crushed or powdered form",
        "name_kh": "កញ្ឆា ៖ ក្នុងទម្រង់ជាកំណាត់ កិនបំបែក ឬកម្ទេចឱ្យទៅជាម្សៅ",
    },
    "12119012": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Cannabis: In other forms",
        "name_kh": "កញ្ឆា ៖ ក្នុងទម្រង់ផ្សេងទៀត",
    },
    "12119013": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Rauwolfia serpentina roots",
        "name_kh": "ប្ញសរ៉ូវុលហ្វៀសឺប៉ង់ទីណា",
    },
    "12119015": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Liquorice roots",
        "name_kh": "ប្ញសដើមឈើអែម",
    },
    "12119017": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Pharmacy plants: Other, fresh or dried",
        "name_kh": "រុក្ខជាតិឱសថ ៖ ផ្សេងទៀត ស្រស់ ឬក្រៀម",
    },
    "12119018": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Pharmacy plants: Other, in cut, crushed or powdered form",
        "name_kh": "រុក្ខជាតិឱសថ ៖ ផ្សេងទៀត ក្នុងទម្រង់ជាកំណាត់ កិនបំបែក ឬកម្ទេចឱ្យទៅជាម្សៅ",
    },
    "12119019": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Pharmacy plants: Other",
        "name_kh": "រុក្ខជាតិឱសថ ៖ ផ្សេងទៀត",
    },
    "12119091": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Pyrethrum: In cut, crushed or powdered form",
        "name_kh": "រុក្ខជាតិ Pyrethrum ៖ ក្នុងទម្រង់ជាកំណាត់ កិនបំបែក ឬកម្ទេចឱ្យទៅជាម្សៅ",
    },
    "12119092": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Pyrethrum: In other forms",
        "name_kh": "រុក្ខជាតិ Pyrethrum ៖ ក្នុងទម្រង់ផ្សេងទៀត",
    },
    "12119094": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Sandalwood chips",
        "name_kh": "ចំណិតឈើក្រអូប Sandalwood",
    },
    "12119095": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Agarwood (Gaharu) chips",
        "name_kh": "ចំណិតឈើ Agarwood (Gaharu)",
    },
    "12119097": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Bark of persea (Persea kurzii Kosterm)",
        "name_kh": "សំបកដើម Persea (Persea kurzii Kosterm)",
    },
    "12119098": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Other plants: In cut, crushed or powdered form",
        "name_kh": "រុក្ខជាតិផ្សេងទៀត ៖ ក្នុងទម្រង់ជាកំណាត់ កិនបំបែក ឬកម្ទេចឱ្យទៅជាម្សៅ",
    },
    "12119099": {
        "category_en": "Medicinal & Industrial Plants",
        "category_kh": "រុក្ខជាតិឱសថ",
        "name_en": "Other plants: Other",
        "name_kh": "រុក្ខជាតិផ្សេងទៀត ៖ ផ្សេងទៀត",
    },

    # Chapter 17: Sugars and Sugar Confectionery
    "17021100": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Lactose (>= 99%)",
        "name_kh": "ឡាក់តូស ៩៩% ឬលើស",
    },
    "17021900": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Lactose: Other",
        "name_kh": "ឡាក់តូស ៖ ផ្សេងទៀត",
    },
    "17022000": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Maple sugar and syrup",
        "name_kh": "ស្ករ និងស៊ីរ៉ូម៉ាផល",
    },
    "17023010": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Glucose",
        "name_kh": "គ្លុយកូស",
    },
    "17023020": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Glucose syrup",
        "name_kh": "ស៊ីរ៉ូគ្លុយកូស",
    },
    "17024000": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Glucose and syrup (20% to 50% fructose)",
        "name_kh": "គ្លុយកូស និងស៊ីរ៉ូគ្លុយកូស (២០% ដល់ ៥០% នៃហ្វ្រុចតូស)",
    },
    "17025000": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Chemically pure fructose",
        "name_kh": "ហ្វ្រុចតូសសុទ្ធដោយគីមី",
    },
    "17026010": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Fructose",
        "name_kh": "ហ្វ្រុចតូស",
    },
    "17026020": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Fructose syrup",
        "name_kh": "ស៊ីរ៉ូហ្វ្រុចតូស",
    },
    "17029011": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Chemically pure maltose",
        "name_kh": "ម៉ាល់តូសសុទ្ធដោយគីមី",
    },
    "17029019": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Maltose: Other",
        "name_kh": "ម៉ាល់តូស ៖ ផ្សេងទៀត",
    },
    "17029020": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Artificial honey",
        "name_kh": "ទឹកឃ្មុំសិប្បនិម្មិត",
    },
    "17029030": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Flavoured or coloured sugars",
        "name_kh": "ស្ករមានលាយរសជាតិ ឬសារធាតុពណ៌",
    },
    "17029040": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Caramel",
        "name_kh": "ការ៉ាមែល",
    },
    "17029051": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Coconut sap sugar",
        "name_kh": "ស្ករបានពីផ្កានៃពពួកត្នោត",
    },
    "17029059": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Palm sugar: Other",
        "name_kh": "ស្ករត្នោត ៖ ផ្សេងទៀត",
    },
    "17029091": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Sugar syrups",
        "name_kh": "ស៊ីរ៉ូស្ករ",
    },
    "17029099": {
        "category_en": "Sugar & Syrups",
        "category_kh": "ស្ករ និងទឹកស្ករ",
        "name_en": "Other sugar & syrups",
        "name_kh": "ស្ករ និងទឹកស្ករផ្សេងទៀត ៖ ផ្សេងទៀត",
    },
}

# ============================================================
# 3. HS4 HEADING KNOWLEDGE BASE
# ============================================================

HS4_MAP: Dict[str, Dict[str, str]] = {
    "0409": {
        "title_en": "Natural Honey",
        "title_km": "ទឹកឃ្មុំធម្មជាតិ",
        "desc_en": "Natural honey.",
        "desc_kh": "ទឹកឃ្មុំធម្មជាតិ",
    },
    "0801": {
        "title_en": "Cashew Nuts & Coconuts",
        "title_km": "គ្រាប់ស្វាយចន្ទី និងដូង",
        "desc_en": "Coconuts, Brazil nuts and cashew nuts, fresh or dried, whether or not shelled or peeled.",
        "desc_kh": "ផ្លែដូង គ្រាប់ផ្លែប្រេស៊ីល និងគ្រាប់ស្វាយចន្ទី ស្រស់ ឬស្ងួត ទោះបក ឬមិនទាន់បកលលាដ៍ ឬសម្បកចេញ",
    },
    "0804": {
        "title_en": "Fresh & Dried Mangoes",
        "title_km": "ស្វាយ និងផ្លែឈើស្ងួត",
        "desc_en": "Dates, figs, pineapples, avocados, guavas, mangoes and mangosteens, fresh or dried.",
        "desc_kh": "ផ្លែល្ម៉ើ ល្វា ម្នាស់ អាវ៉ូកាដូ ត្របែក ស្វាយ មង្ឃុត ស្រស់ ឬស្ងួត",
    },
    "0904": {
        "title_en": "Pepper & Chili (Capsicum)",
        "title_km": "ម្រេច និងម្ទេស (Capsicum)",
        "desc_en": "Pepper of the genus Piper; dried or crushed or ground fruits of the genus Capsicum or of the genus Pimenta.",
        "desc_kh": "ម្រេចប្រភេទPiper; ផ្លែម្ទេសប្រភេទCapsicum ឬ ម្ទេស ម្រេចប្រភេទPimenta; ក្រៀម កម្ទេច ឬម្សៅម៉ដ្ឋ",
    },
    "0910": {
        "title_en": "Ginger, Turmeric & Spices",
        "title_km": "ខ្ញី រមៀត និងគ្រឿងទេស",
        "desc_en": "Ginger, saffron, turmeric (curcuma), thyme, bay leaves, curry and other spices.",
        "desc_kh": "ខ្ញី saffron រមៀត(curcuma) ស្លឹក Thyme ស្លឹក bay ការី និងគ្រឿងទេសផ្សេងទៀត",
    },
    "1211": {
        "title_en": "Medicinal & Perfumery Plants",
        "title_km": "រុក្ខជាតិឱសថ និងរុក្ខជាតិក្លិន",
        "desc_en": "Plants and parts of plants (including seeds and fruits), of a kind used primarily in perfumery, pharmacy or for insecticidal, fungicidal or similar purposes, fresh, chilled, frozen or dried, whether or not cut, crushed or powdered.",
        "desc_kh": "រុក្ខជាតិ និងភាគបំណែកនៃរុក្ខជាតិ (រាប់បញ្ចូលទាំងគ្រាប់ និងផ្លែឈើ) ដែលប្រើប្រាស់ជាចម្បងក្នុងការផលិតគ្រឿងក្រអូប វិស័យឱសថសាស្ត្រ ឬសម្រាប់សម្លាប់សត្វល្អិត សម្លាប់ផ្សិត ឬគោលបំណងប្រហាក់ប្រហែល ស្រស់ ក្លាស្សេ បង្កក ឬក្រៀម",
    },
    "1702": {
        "title_en": "Sugar & Syrups",
        "title_km": "ស្ករ និងទឹកស្ករ",
        "desc_en": "Other sugars, including chemically pure lactose, maltose, glucose and fructose, in solid form; sugar syrups; artificial honey; caramel.",
        "desc_kh": "ស្ករផ្សេងទៀតរួមទាំងឡាក់តូស ម៉ាល់តូស គ្លុយកូស និងហ្វ្រុចតូសសុទ្ធស្ថិតនៅក្នុងស្ថានភាពរឹង; ស៊ីរ៉ូស្ករ; ទឹកឃ្មុំសិប្បនិម្មិត; ការ៉ាមែល",
    },
}

# ============================================================
# 4. COUNTRY KNOWLEDGE BASE (41 Countries with ISO-3 Codes)
# ============================================================

COUNTRY_MAP: Dict[str, Dict[str, str]] = {
    # Southeast Asia
    "វៀតណាម": {"EN": "Vietnam", "ISO": "VNM", "Canonical_KH": "វៀតណាម"},
    "ថៃ": {"EN": "Thailand", "ISO": "THA", "Canonical_KH": "ថៃ"},
    "សិង្ហបុរី": {"EN": "Singapore", "ISO": "SGP", "Canonical_KH": "សិង្ហបុរី"},
    "ម៉ាឡេស៊ី": {"EN": "Malaysia", "ISO": "MYS", "Canonical_KH": "ម៉ាឡេស៊ី"},
    "ហ៊្វីលីពីន": {"EN": "Philippines", "ISO": "PHL", "Canonical_KH": "ហ្វីលីពីន"},
    "ហ្វ៊ីលីពីន": {"EN": "Philippines", "ISO": "PHL", "Canonical_KH": "ហ្វីលីពីន"},
    "ហ្វីលីពីន": {"EN": "Philippines", "ISO": "PHL", "Canonical_KH": "ហ្វីលីពីន"},
    "ឥណ្ឌូនេស៊ី": {"EN": "Indonesia", "ISO": "IDN", "Canonical_KH": "ឥណ្ឌូណេស៊ី"},
    "ឥណ្ឌូណេស៊ី": {"EN": "Indonesia", "ISO": "IDN", "Canonical_KH": "ឥណ្ឌូណេស៊ី"},
    "ព្រុយណេ": {"EN": "Brunei", "ISO": "BRN", "Canonical_KH": "ព្រុយណេ"},
    "ឡាវ": {"EN": "Laos", "ISO": "LAO", "Canonical_KH": "ឡាវ"},

    # East Asia
    "ចិន": {"EN": "China", "ISO": "CHN", "Canonical_KH": "ចិន"},
    "ជប៉ុន": {"EN": "Japan", "ISO": "JPN", "Canonical_KH": "ជប៉ុន"},
    "កូរ៉េខាងត្បូង": {"EN": "South Korea", "ISO": "KOR", "Canonical_KH": "កូរ៉េខាងត្បូង"},
    "តៃវ៉ាន់": {"EN": "Taiwan", "ISO": "TWN", "Canonical_KH": "តៃវ៉ាន់"},
    "ហុងកុង": {"EN": "Hong Kong", "ISO": "HKG", "Canonical_KH": "ហុងកុង"},

    # South Asia
    "ឥណ្ឌា": {"EN": "India", "ISO": "IND", "Canonical_KH": "ឥណ្ឌា"},
    "បង់ក្លាដែស": {"EN": "Bangladesh", "ISO": "BGD", "Canonical_KH": "បង់ក្លាដែស"},
    "ប៉ាគីស្ថាន": {"EN": "Pakistan", "ISO": "PAK", "Canonical_KH": "ប៉ាគីស្ថាន"},
    "ស្រីលង្កា": {"EN": "Sri Lanka", "ISO": "LKA", "Canonical_KH": "ស្រីលង្កា"},

    # Central & West Asia / Middle East
    "កាហ្សាក់ស្ថាន": {"EN": "Kazakhstan", "ISO": "KAZ", "Canonical_KH": "កាហ្សាក់ស្ថាន"},
    "អ៊ីស្រាអែល": {"EN": "Israel", "ISO": "ISR", "Canonical_KH": "អ៊ីស្រាអែល"},
    "អារ៉ាប៊ីសាអូឌីត": {"EN": "Saudi Arabia", "ISO": "SAU", "Canonical_KH": "អារ៉ាប៊ីសាអូឌីត"},
    "អេមីរ៉ាតអារ៉ាប់រួម": {"EN": "United Arab Emirates", "ISO": "ARE", "Canonical_KH": "អេមីរ៉ាតអារ៉ាប់រួម"},
    "កាតា": {"EN": "Qatar", "ISO": "QAT", "Canonical_KH": "កាតា"},
    "កូវ៉ែត": {"EN": "Kuwait", "ISO": "KWT", "Canonical_KH": "កូវ៉ែត"},
    "បារ៉ែន": {"EN": "Bahrain", "ISO": "BHR", "Canonical_KH": "បារ៉ែន"},
    "អូម៉ង់": {"EN": "Oman", "ISO": "OMN", "Canonical_KH": "អូម៉ង់"},
    "ហ្ស៊កដានី": {"EN": "Jordan", "ISO": "JOR", "Canonical_KH": "ហ្ស៊កដានី"},

    # Europe
    "បារាំង": {"EN": "France", "ISO": "FRA", "Canonical_KH": "បារាំង"},
    "ហូឡង់": {"EN": "Netherlands", "ISO": "NLD", "Canonical_KH": "ហូឡង់"},
    "អាល្លឺម៉ង់": {"EN": "Germany", "ISO": "DEU", "Canonical_KH": "អាល្លឺម៉ង់"},
    "បែលហ្ស៊ិក": {"EN": "Belgium", "ISO": "BEL", "Canonical_KH": "បែលហ្ស៊ិក"},
    "អង់គ្លេស (ចក្រភព)": {"EN": "United Kingdom", "ISO": "GBR", "Canonical_KH": "អង់គ្លេស (ចក្រភព)"},
    "អ៊ីតាលី": {"EN": "Italy", "ISO": "ITA", "Canonical_KH": "អ៊ីតាលី"},
    "អេស្ប៉ាញ": {"EN": "Spain", "ISO": "ESP", "Canonical_KH": "អេស្ប៉ាញ"},
    "ព័រទុយហ្គាល់": {"EN": "Portugal", "ISO": "PRT", "Canonical_KH": "ព័រទុយហ្គាល់"},
    "ស្វ៊ីស": {"EN": "Switzerland", "ISO": "CHE", "Canonical_KH": "ស្វ៊ីស"},
    "អូទ្រីស": {"EN": "Austria", "ISO": "AUT", "Canonical_KH": "អូទ្រីស"},
    "ដាណឺម៉ាក": {"EN": "Denmark", "ISO": "DNK", "Canonical_KH": "ដាណឺម៉ាក"},
    "ន័រវែស": {"EN": "Norway", "ISO": "NOR", "Canonical_KH": "ន័រវែស"},
    "ស៊ុយអែត": {"EN": "Sweden", "ISO": "SWE", "Canonical_KH": "ស៊ុយអែត"},
    "ហ្វាំងឡង់": {"EN": "Finland", "ISO": "FIN", "Canonical_KH": "ហ្វាំងឡង់"},
    "ប៉ូឡូញ": {"EN": "Poland", "ISO": "POL", "Canonical_KH": "ប៉ូឡូញ"},
    "ឆែក (សាធារណរដ្ឋ)": {"EN": "Czech Republic", "ISO": "CZE", "Canonical_KH": "ឆែក (សាធារណរដ្ឋ)"},
    "ហុងគ្រី": {"EN": "Hungary", "ISO": "HUN", "Canonical_KH": "ហុងគ្រី"},
    "ក្រូអាស៊ី": {"EN": "Croatia", "ISO": "HRV", "Canonical_KH": "ក្រូអាស៊ី"},
    "ក្រិក": {"EN": "Greece", "ISO": "GRC", "Canonical_KH": "ក្រិក"},
    "ស៊ែប៊ី": {"EN": "Serbia", "ISO": "SRB", "Canonical_KH": "ស៊ែប៊ី"},
    "លីទុយអានី": {"EN": "Lithuania", "ISO": "LTU", "Canonical_KH": "លីទុយអានី"},
    "រុស្ស៊ី": {"EN": "Russia", "ISO": "RUS", "Canonical_KH": "រុស្ស៊ី"},
    "តួកគី": {"EN": "Turkey", "ISO": "TUR", "Canonical_KH": "តួកគី"},
    "អៀរឡង់": {"EN": "Ireland", "ISO": "IRL", "Canonical_KH": "អៀរឡង់"},

    # Americas
    "អាមេរិក (សហរដ្ឋ)": {"EN": "United States", "ISO": "USA", "Canonical_KH": "អាមេរិក (សហរដ្ឋ)"},
    "អាម៉េរិក (សហរដ្ឋ)": {"EN": "United States", "ISO": "USA", "Canonical_KH": "អាមេរិក (សហរដ្ឋ)"},
    "កាណាដា": {"EN": "Canada", "ISO": "CAN", "Canonical_KH": "កាណាដា"},
    "ម៉ិកស៊ិក": {"EN": "Mexico", "ISO": "MEX", "Canonical_KH": "ម៉ិកស៊ិក"},
    "អេក្វាទ័រ": {"EN": "Ecuador", "ISO": "ECU", "Canonical_KH": "អេក្វាទ័រ"},

    # Africa
    "ហ្កាណា": {"EN": "Ghana", "ISO": "GHA", "Canonical_KH": "ហ្កាណា"},
    "ម៉ាលី": {"EN": "Mali", "ISO": "MLI", "Canonical_KH": "ម៉ាលី"},
    "សេណេហ្កាល់": {"EN": "Senegal", "ISO": "SEN", "Canonical_KH": "សេណេហ្កាល់"},
    "តង់សានី": {"EN": "Tanzania", "ISO": "TZA", "Canonical_KH": "តង់សានី"},
    "ម៉ូសំប៊ិក": {"EN": "Mozambique", "ISO": "MOZ", "Canonical_KH": "ម៉ូសំប៊ិក"},
    "ស៊ីមបាវ៉េ": {"EN": "Zimbabwe", "ISO": "ZWE", "Canonical_KH": "ស៊ីមបាវ៉េ"},
    "ស្វាស៊ីឡង់": {"EN": "Eswatini", "ISO": "SWZ", "Canonical_KH": "ស្វាស៊ីឡង់"},

    # Oceania
    "អូស្ត្រាលី": {"EN": "Australia", "ISO": "AUS", "Canonical_KH": "អូស្ត្រាលី"},
    "នូវែលសេឡង់": {"EN": "New Zealand", "ISO": "NZL", "Canonical_KH": "នូវែលសេឡង់"},
    "កោះ New Caledonia (បារាំង)": {"EN": "New Caledonia", "ISO": "NCL", "Canonical_KH": "កោះ New Caledonia (បារាំង)"},
}

# Raw vs Processed pairs within the same HS4 chapter
RAW_VS_PROCESSED_PAIRS: Dict[str, list] = {
    "0801": [
        ("08013100", "08013200"),  # Cashew in-shell (raw) vs shelled (processed)
    ],
    "0804": [
        ("08045021", "08045022"),  # Fresh mango (raw) vs dried mango (processed)
    ],
    "0904": [
        ("09041110", "09041210"),  # White pepper unground vs ground
        ("09041120", "09041220"),  # Black pepper unground vs ground
    ]
}

# ============================================================
# 5. PUBLIC HELPER FUNCTIONS
# ============================================================

def get_hs4_official_name(hs4_code: str, raw_desc: str = "") -> Tuple[str, str, str, str]:
    """Returns (title_en, title_km, full_desc_en, full_desc_km) for an HS4 chapter."""
    clean_code = clean_hs_code(hs4_code, 4)
    if clean_code in HS4_MAP:
        info = HS4_MAP[clean_code]
        return (
            info.get("title_en", f"Chapter {clean_code}"),
            info.get("title_km", f"ជំពូក {clean_code}"),
            info.get("desc_en", raw_desc),
            info.get("desc_kh", raw_desc),
        )

    desc = clean_text(raw_desc) if raw_desc else f"Agricultural Chapter HS {clean_code}"
    short = desc[:40]
    return short, short, desc, desc

def get_hs8_product_info(hs8_code: str, raw_description: str = "") -> Dict[str, str]:
    """Returns full bilingual HS8 dictionary: name_en, name_kh, category_en, category_kh."""
    clean_code = clean_hs_code(hs8_code, 8)
    if clean_code in HS8_MAPPING:
        return dict(HS8_MAPPING[clean_code])
    
    clean_desc = clean_text(raw_description)
    fallback = clean_desc[:50] if clean_desc else f"HS8 {clean_code}"
    return {
        "name_en": fallback,
        "name_kh": fallback,
        "category_en": "Other Agricultural",
        "category_kh": "កសិផលផ្សេងៗ"
    }

def get_product_name(hs8_code: str, raw_description: str = "", lang: Optional[str] = None) -> str:
    """Returns localized product name (defaulting to English)."""
    info = get_hs8_product_info(hs8_code, raw_description)
    target = "name_kh" if lang == "km" else "name_en"
    return info.get(target, info["name_en"])

def get_product_names_bilingual(hs8_code: str, raw_description: str = "") -> Dict[str, str]:
    """Returns {'en': '...', 'km': '...'} for an 8-digit HS code."""
    info = get_hs8_product_info(hs8_code, raw_description)
    return {"en": info["name_en"], "km": info["name_kh"]}

def get_country_info(raw_country: str) -> Dict[str, str]:
    """Returns {'EN': str, 'ISO': str, 'Canonical_KH': str} for a country."""
    clean_c = clean_text(raw_country)
    if clean_c in COUNTRY_MAP:
        return dict(COUNTRY_MAP[clean_c])
    
    # Check if input is already English name
    for kh, info in COUNTRY_MAP.items():
        if info["EN"].lower() == clean_c.lower():
            return dict(info)
            
    return {
        "EN": clean_c or "Other",
        "ISO": "OTH",
        "Canonical_KH": clean_c or "ផ្សេងៗ"
    }

def get_raw_processed_pair(hs4_code: str, hs8_code: str) -> Optional[Dict]:
    """Checks if hs8_code belongs to a recognized raw-vs-processed pair."""
    clean_hs4 = clean_hs_code(hs4_code, 4)
    clean_hs8 = clean_hs_code(hs8_code, 8)

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
