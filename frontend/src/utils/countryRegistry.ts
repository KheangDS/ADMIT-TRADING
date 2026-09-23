import worldGeoJson from '../assets/world.json';

export interface CountryMeta {
  en: string;
  km: string;
  iso: string;
  coords: [number, number];
  flag: string;
}

export const CAMBODIA_COORDS: [number, number] = [104.9282, 11.5564];

// Master Dictionary: Khmer & English country names, ISO codes, coordinates, and emoji flags
const RAW_COUNTRY_REGISTRY: CountryMeta[] = [
  // Southeast Asia
  { en: 'Cambodia', km: 'កម្ពុជា', iso: 'KHM', coords: [104.9282, 11.5564], flag: '🇰🇭' },
  { en: 'Vietnam', km: 'វៀតណាម', iso: 'VNM', coords: [106.6297, 10.8231], flag: '🇻🇳' },
  { en: 'Thailand', km: 'ថៃ', iso: 'THA', coords: [100.5018, 13.7563], flag: '🇹🇭' },
  { en: 'Singapore', km: 'សិង្ហបុរី', iso: 'SGP', coords: [103.8198, 1.3521], flag: '🇸🇬' },
  { en: 'Malaysia', km: 'ម៉ាឡេស៊ី', iso: 'MYS', coords: [101.6869, 3.1390], flag: '🇲🇾' },
  { en: 'Philippines', km: 'ហ្វីលីពីន', iso: 'PHL', coords: [120.9842, 14.5995], flag: '🇵🇭' },
  { en: 'Indonesia', km: 'ឥណ្ឌូណេស៊ី', iso: 'IDN', coords: [106.8456, -6.2088], flag: '🇮🇩' },
  { en: 'Brunei', km: 'ព្រុយណេ', iso: 'BRN', coords: [114.9422, 4.9031], flag: '🇧🇳' },
  { en: 'Laos', km: 'ឡាវ', iso: 'LAO', coords: [102.6331, 17.9757], flag: '🇱🇦' },
  { en: 'Myanmar', km: 'មីយ៉ាន់ម៉ា', iso: 'MMR', coords: [96.1951, 16.8661], flag: '🇲🇲' },

  // East Asia
  { en: 'China', km: 'ចិន', iso: 'CHN', coords: [116.4074, 39.9042], flag: '🇨🇳' },
  { en: 'Japan', km: 'ជប៉ុន', iso: 'JPN', coords: [139.6917, 35.6895], flag: '🇯🇵' },
  { en: 'South Korea', km: 'កូរ៉េខាងត្បូង', iso: 'KOR', coords: [126.9780, 37.5665], flag: '🇰🇷' },
  { en: 'North Korea', km: 'កូរ៉េខាងជើង', iso: 'PRK', coords: [125.7625, 39.0392], flag: '🇰🇵' },
  { en: 'Taiwan', km: 'តៃវ៉ាន់', iso: 'TWN', coords: [121.5654, 25.0330], flag: '🇹🇼' },
  { en: 'Hong Kong', km: 'ហុងកុង', iso: 'HKG', coords: [114.1694, 22.3193], flag: '🇭🇰' },
  { en: 'Macau', km: 'ម៉ាកាវ', iso: 'MAC', coords: [113.5439, 22.1987], flag: '🇲🇴' },
  { en: 'Mongolia', km: 'ម៉ុងហ្គោលី', iso: 'MNG', coords: [106.9186, 47.9212], flag: '🇲🇳' },

  // South Asia
  { en: 'India', km: 'ឥណ្ឌា', iso: 'IND', coords: [77.2090, 28.6139], flag: '🇮🇳' },
  { en: 'Bangladesh', km: 'បង់ក្លាដែស', iso: 'BGD', coords: [90.4125, 23.8103], flag: '🇧🇩' },
  { en: 'Pakistan', km: 'ប៉ាគីស្ថាន', iso: 'PAK', coords: [73.0479, 33.6844], flag: '🇵🇰' },
  { en: 'Sri Lanka', km: 'ស្រីលង្កា', iso: 'LKA', coords: [79.8612, 6.9271], flag: '🇱🇰' },
  { en: 'Nepal', km: 'នេប៉ាល់', iso: 'NPL', coords: [85.3240, 27.7172], flag: '🇳🇵' },

  // Americas
  { en: 'Canada', km: 'កាណាដា', iso: 'CAN', coords: [-106.3468, 56.1304], flag: '🇨🇦' },
  { en: 'United States', km: 'សហរដ្ឋអាមេរិក', iso: 'USA', coords: [-95.7129, 37.0902], flag: '🇺🇸' },
  { en: 'Mexico', km: 'ម៉ិកស៊ិក', iso: 'MEX', coords: [-99.1332, 19.4326], flag: '🇲🇽' },
  { en: 'Brazil', km: 'ប្រេស៊ីល', iso: 'BRA', coords: [-47.8825, -15.7942], flag: '🇧🇷' },
  { en: 'Argentina', km: 'អាហ្សង់ទីន', iso: 'ARG', coords: [-58.3816, -34.6037], flag: '🇦🇷' },
  { en: 'Chile', km: 'ឈីលី', iso: 'CHL', coords: [-70.6693, -33.4489], flag: '🇨🇱' },
  { en: 'Colombia', km: 'កូឡុំប៊ី', iso: 'COL', coords: [-74.0721, 4.7110], flag: '🇨🇴' },
  { en: 'Peru', km: 'ប៉េរូ', iso: 'PER', coords: [-77.0428, -12.0464], flag: '🇵🇪' },
  { en: 'Ecuador', km: 'អេក្វាទ័រ', iso: 'ECU', coords: [-78.4678, -0.1807], flag: '🇪🇨' },
  { en: 'Panama', km: 'ប៉ាណាម៉ា', iso: 'PAN', coords: [-79.5199, 8.9824], flag: '🇵🇦' },
  { en: 'Costa Rica', km: 'កូស្តារីកា', iso: 'CRI', coords: [-84.0907, 9.9281], flag: '🇨🇷' },
  { en: 'Guatemala', km: 'ក្វាតេម៉ាឡា', iso: 'GTM', coords: [-90.5069, 14.6349], flag: '🇬🇹' },
  { en: 'Cuba', km: 'គុយបា', iso: 'CUB', coords: [-82.3666, 23.1136], flag: '🇨🇺' },

  // Europe
  { en: 'France', km: 'បារាំង', iso: 'FRA', coords: [2.3522, 48.8566], flag: '🇫🇷' },
  { en: 'Germany', km: 'អាល្លឺម៉ង់', iso: 'DEU', coords: [13.4050, 52.5200], flag: '🇩🇪' },
  { en: 'Netherlands', km: 'ហូឡង់', iso: 'NLD', coords: [4.9041, 52.3676], flag: '🇳🇱' },
  { en: 'Belgium', km: 'បែលហ្ស៊ិក', iso: 'BEL', coords: [4.3517, 50.8503], flag: '🇧🇪' },
  { en: 'United Kingdom', km: 'អង់គ្លេស', iso: 'GBR', coords: [-0.1278, 51.5074], flag: '🇬🇧' },
  { en: 'Italy', km: 'អ៊ីតាលី', iso: 'ITA', coords: [12.4964, 41.9028], flag: '🇮🇹' },
  { en: 'Spain', km: 'អេស្ប៉ាញ', iso: 'ESP', coords: [-3.7038, 40.4168], flag: '🇪🇸' },
  { en: 'Portugal', km: 'ព័រទុយហ្គាល់', iso: 'PRT', coords: [-9.1393, 38.7223], flag: '🇵🇹' },
  { en: 'Switzerland', km: 'ស្វ៊ីស', iso: 'CHE', coords: [7.4474, 46.9480], flag: '🇨🇭' },
  { en: 'Austria', km: 'អូទ្រីស', iso: 'AUT', coords: [16.3738, 48.2082], flag: '🇦🇹' },
  { en: 'Denmark', km: 'ដាណឺម៉ាក', iso: 'DNK', coords: [12.5683, 55.6761], flag: '🇩🇰' },
  { en: 'Norway', km: 'ន័រវែស', iso: 'NOR', coords: [10.7522, 59.9139], flag: '🇳🇴' },
  { en: 'Sweden', km: 'ស៊ុយអែត', iso: 'SWE', coords: [18.0686, 59.3293], flag: '🇸🇪' },
  { en: 'Finland', km: 'ហ្វាំងឡង់', iso: 'FIN', coords: [24.9384, 60.1699], flag: '🇫🇮' },
  { en: 'Poland', km: 'ប៉ូឡូញ', iso: 'POL', coords: [21.0122, 52.2297], flag: '🇵🇱' },
  { en: 'Czech Republic', km: 'ឆែក', iso: 'CZE', coords: [14.4378, 50.0755], flag: '🇨🇿' },
  { en: 'Hungary', km: 'ហុងគ្រី', iso: 'HUN', coords: [19.0402, 47.4979], flag: '🇭🇺' },
  { en: 'Croatia', km: 'ក្រូអាស៊ី', iso: 'HRV', coords: [15.9819, 45.8150], flag: '🇭🇷' },
  { en: 'Greece', km: 'ក្រិក', iso: 'GRC', coords: [23.7275, 37.9838], flag: '🇬🇷' },
  { en: 'Serbia', km: 'ស៊ែប៊ី', iso: 'SRB', coords: [20.4489, 44.7866], flag: '🇷🇸' },
  { en: 'Lithuania', km: 'លីទុយអានី', iso: 'LTU', coords: [25.2797, 54.6872], flag: '🇱🇹' },
  { en: 'Latvia', km: 'ឡាតវី', iso: 'LVA', coords: [24.1052, 56.9496], flag: '🇱🇻' },
  { en: 'Estonia', km: 'អេស្តូនី', iso: 'EST', coords: [24.7535, 59.4370], flag: '🇪🇪' },
  { en: 'Russia', km: 'រុស្ស៊ី', iso: 'RUS', coords: [37.6173, 55.7558], flag: '🇷🇺' },
  { en: 'Turkey', km: 'តួកគី', iso: 'TUR', coords: [32.8597, 39.9334], flag: '🇹🇷' },
  { en: 'Ireland', km: 'អៀរឡង់', iso: 'IRL', coords: [-6.2603, 53.3498], flag: '🇮🇪' },
  { en: 'Ukraine', km: 'អ៊ុយក្រែន', iso: 'UKR', coords: [30.5234, 50.4501], flag: '🇺🇦' },
  { en: 'Romania', km: 'រូម៉ានី', iso: 'ROU', coords: [26.1025, 44.4268], flag: '🇷🇴' },
  { en: 'Bulgaria', km: 'ប៊ុលហ្គារី', iso: 'BGR', coords: [23.3219, 42.6977], flag: '🇧🇬' },

  // Central / West Asia & Middle East
  { en: 'Kazakhstan', km: 'កាហ្សាក់ស្ថាន', iso: 'KAZ', coords: [71.4491, 51.1694], flag: '🇰🇿' },
  { en: 'Uzbekistan', km: 'អ៊ូសបេគីស្ថាន', iso: 'UZB', coords: [69.2401, 41.2995], flag: '🇺🇿' },
  { en: 'Israel', km: 'អ៊ីស្រាអែល', iso: 'ISR', coords: [35.2137, 31.7683], flag: '🇮🇱' },
  { en: 'Saudi Arabia', km: 'អារ៉ាប៊ីសាអូឌីត', iso: 'SAU', coords: [46.6753, 24.7136], flag: '🇸🇦' },
  { en: 'United Arab Emirates', km: 'អេមីរ៉ាតអារ៉ាប់រួម', iso: 'ARE', coords: [54.3773, 24.4539], flag: '🇦🇪' },
  { en: 'Qatar', km: 'កាតា', iso: 'QAT', coords: [51.5310, 25.2854], flag: '🇶🇦' },
  { en: 'Kuwait', km: 'កូវ៉ែត', iso: 'KWT', coords: [47.9774, 29.3759], flag: '🇰🇼' },
  { en: 'Bahrain', km: 'បារ៉ែន', iso: 'BHR', coords: [50.5860, 26.2285], flag: '🇧🇭' },
  { en: 'Oman', km: 'អូម៉ង់', iso: 'OMN', coords: [58.4059, 23.5859], flag: '🇴🇲' },
  { en: 'Jordan', km: 'ហ្ស៊កដានី', iso: 'JOR', coords: [35.9284, 31.9454], flag: '🇯🇴' },
  { en: 'Iran', km: 'អ៊ីរង់', iso: 'IRN', coords: [51.3890, 35.6892], flag: '🇮🇷' },
  { en: 'Iraq', km: 'អ៊ីរ៉ាក់', iso: 'IRQ', coords: [44.3661, 33.3152], flag: '🇮🇶' },

  // Africa
  { en: 'Ghana', km: 'ហ្កាណា', iso: 'GHA', coords: [-0.1870, 5.6037], flag: '🇬🇭' },
  { en: 'Mali', km: 'ម៉ាលី', iso: 'MLI', coords: [-8.0029, 12.6392], flag: '🇲🇱' },
  { en: 'Senegal', km: 'សេណេហ្កាល់', iso: 'SEN', coords: [-17.4441, 14.6928], flag: '🇸🇳' },
  { en: 'Tanzania', km: 'តង់សានី', iso: 'TZA', coords: [35.7516, -6.1630], flag: '🇹🇿' },
  { en: 'Mozambique', km: 'ម៉ូសំប៊ិក', iso: 'MOZ', coords: [32.5732, -25.9692], flag: '🇲🇿' },
  { en: 'Zimbabwe', km: 'ស៊ីមបាវ៉េ', iso: 'ZWE', coords: [31.0530, -17.8252], flag: '🇿🇼' },
  { en: 'Eswatini', km: 'ស្វាស៊ីឡង់', iso: 'SWZ', coords: [31.1367, -26.4194], flag: '🇸🇿' },
  { en: 'South Africa', km: 'អាហ្វ្រិកខាងត្បូង', iso: 'ZAF', coords: [28.0473, -26.2041], flag: '🇿🇦' },
  { en: 'Egypt', km: 'អេហ្ស៊ីប', iso: 'EGY', coords: [31.2357, 30.0444], flag: '🇪🇬' },
  { en: 'Nigeria', km: 'នីហ្សេរីយ៉ា', iso: 'NGA', coords: [7.4951, 9.0579], flag: '🇳🇬' },
  { en: 'Kenya', km: 'កេនយ៉ា', iso: 'KEN', coords: [36.8219, -1.2921], flag: '🇰🇪' },
  { en: 'Ethiopia', km: 'អេត្យូពី', iso: 'ETH', coords: [38.7578, 8.9806], flag: '🇪🇹' },
  { en: 'Morocco', km: 'ម៉ារ៉ុក', iso: 'MAR', coords: [-6.8498, 34.0209], flag: '🇲🇦' },
  { en: 'Algeria', km: 'អាល់ហ្សេរី', iso: 'DZA', coords: [3.0588, 36.7538], flag: '🇩🇿' },
  { en: 'Côte d\'Ivoire', km: 'កូតឌីវ័រ', iso: 'CIV', coords: [-4.0083, 5.3600], flag: '🇨🇮' },

  // Oceania
  { en: 'Australia', km: 'អូស្ត្រាលី', iso: 'AUS', coords: [133.7751, -25.2744], flag: '🇦🇺' },
  { en: 'New Zealand', km: 'នូវែលសេឡង់', iso: 'NZL', coords: [174.7633, -36.8485], flag: '🇳🇿' },
  { en: 'Fiji', km: 'ហ្វីជី', iso: 'FJI', coords: [178.4419, -18.1416], flag: '🇫🇯' },
  { en: 'Papua New Guinea', km: 'ប៉ាពួញូហ្គីណេ', iso: 'PNG', coords: [147.1803, -9.4438], flag: '🇵🇬' },
  { en: 'New Caledonia', km: 'កោះ New Caledonia (បារាំង)', iso: 'NCL', coords: [166.4572, -22.2711], flag: '🇳🇨' },
];

// Build Fast Alias Map
const ALIAS_MAP = new Map<string, CountryMeta>();

function registerAliases(entry: CountryMeta) {
  const enLower = entry.en.toLowerCase();
  ALIAS_MAP.set(enLower, entry);
  ALIAS_MAP.set(entry.km, entry);
  ALIAS_MAP.set(entry.iso.toLowerCase(), entry);

  // Common synonyms and variations
  if (entry.en === 'United States') {
    ALIAS_MAP.set('usa', entry);
    ALIAS_MAP.set('us', entry);
    ALIAS_MAP.set('united states of america', entry);
    ALIAS_MAP.set('អាមេរិក (សហរដ្ឋ)', entry);
    ALIAS_MAP.set('អាម៉េរិក (សហរដ្ឋ)', entry);
    ALIAS_MAP.set('សហរដ្ឋអាមេរិក', entry);
    ALIAS_MAP.set('អាមេរិក', entry);
  } else if (entry.en === 'United Kingdom') {
    ALIAS_MAP.set('uk', entry);
    ALIAS_MAP.set('great britain', entry);
    ALIAS_MAP.set('britain', entry);
    ALIAS_MAP.set('england', entry);
    ALIAS_MAP.set('អង់គ្លេស (ចក្រភព)', entry);
    ALIAS_MAP.set('ចក្រភពអង់គ្លេស', entry);
  } else if (entry.en === 'South Korea') {
    ALIAS_MAP.set('korea', entry);
    ALIAS_MAP.set('republic of korea', entry);
    ALIAS_MAP.set('rok', entry);
    ALIAS_MAP.set('កូរ៉េ', entry);
  } else if (entry.en === 'North Korea') {
    ALIAS_MAP.set('dprk', entry);
  } else if (entry.en === 'Vietnam') {
    ALIAS_MAP.set('viet nam', entry);
  } else if (entry.en === 'United Arab Emirates') {
    ALIAS_MAP.set('uae', entry);
    ALIAS_MAP.set('dubai', entry);
  } else if (entry.en === 'Czech Republic') {
    ALIAS_MAP.set('czechia', entry);
    ALIAS_MAP.set('ឆែក (សាធារណរដ្ឋ)', entry);
  } else if (entry.en === 'Eswatini') {
    ALIAS_MAP.set('swaziland', entry);
  } else if (entry.en === 'Philippines') {
    ALIAS_MAP.set('ហ៊្វីលីពីន', entry);
    ALIAS_MAP.set('ហ្វ៊ីលីពីន', entry);
  } else if (entry.en === 'Indonesia') {
    ALIAS_MAP.set('ឥណ្ឌូនេស៊ី', entry);
  }
}

RAW_COUNTRY_REGISTRY.forEach(registerAliases);

// Calculate Centroid fallback from GeoJSON features if unknown
function getFeatureCentroid(feature: any): [number, number] {
  const geom = feature.geometry;
  if (!geom || !geom.coordinates) return [100.0, 20.0];
  let totalLng = 0, totalLat = 0, count = 0;
  
  function processCoords(coords: any) {
    if (typeof coords[0] === 'number' && typeof coords[1] === 'number') {
      totalLng += coords[0];
      totalLat += coords[1];
      count++;
    } else if (Array.isArray(coords)) {
      for (const c of coords) {
        processCoords(c);
      }
    }
  }
  
  processCoords(geom.coordinates);
  return count > 0 
    ? [Math.round((totalLng / count) * 10000) / 10000, Math.round((totalLat / count) * 10000) / 10000]
    : [100.0, 20.0];
}

/**
 * Resolves any raw country string (Khmer or English or abbreviation) to standardized CountryMeta
 */
export function getCountryMeta(rawName: string): CountryMeta {
  if (!rawName) return { en: 'Unknown', km: 'មិនស្គាល់', iso: 'OTH', coords: [100.0, 20.0], flag: '🌐' };

  const clean = rawName.replace(/[\u200b\xa0]/g, '').trim();
  const lower = clean.toLowerCase();

  // 1. Exact Match via Alias Map
  if (ALIAS_MAP.has(lower)) {
    return ALIAS_MAP.get(lower)!;
  }
  if (ALIAS_MAP.has(clean)) {
    return ALIAS_MAP.get(clean)!;
  }

  // 2. Partial / Substring Match in Dictionary
  for (const entry of RAW_COUNTRY_REGISTRY) {
    const eLower = entry.en.toLowerCase();
    if (lower.includes(eLower) || eLower.includes(lower)) {
      return entry;
    }
    if (clean.includes(entry.km) || entry.km.includes(clean)) {
      return entry;
    }
  }

  // 3. Fallback: Search in worldGeoJson features directly
  const worldFeatures = (worldGeoJson as any).features || [];
  const matchedFeature = worldFeatures.find((f: any) => {
    const fname = f.properties?.name || '';
    return fname && (fname.toLowerCase() === lower || lower.includes(fname.toLowerCase()) || fname.toLowerCase().includes(lower));
  });

  if (matchedFeature) {
    const calculatedCoords = getFeatureCentroid(matchedFeature);
    const fname = matchedFeature.properties?.name || clean;
    return {
      en: fname,
      km: clean,
      iso: 'OTH',
      coords: calculatedCoords,
      flag: '🌐',
    };
  }

  // Default fallback
  return { en: clean, km: clean, iso: 'OTH', coords: [100.0, 20.0], flag: '🌐' };
}

export function getCountryFlag(name: string): string {
  return getCountryMeta(name).flag;
}

export function getDisplayCountryName(name: string): string {
  const meta = getCountryMeta(name);
  if (meta.en !== name && meta.km !== name) {
    return `${meta.en} (${name})`;
  }
  return meta.en || name;
}

/**
 * Robustly checks if two country identifiers (English, Khmer, ISO, Alias, or GeoJSON name) represent the same country.
 */
export function isSameCountry(name1: string, name2: string): boolean {
  if (!name1 || !name2) return false;
  const clean1 = name1.replace(/[\u200b\xa0]/g, '').trim();
  const clean2 = name2.replace(/[\u200b\xa0]/g, '').trim();
  if (clean1.toLowerCase() === clean2.toLowerCase()) return true;

  const meta1 = getCountryMeta(clean1);
  const meta2 = getCountryMeta(clean2);

  if (meta1.iso !== 'OTH' && meta2.iso !== 'OTH' && meta1.iso === meta2.iso) {
    return true;
  }
  if (meta1.en && meta2.en && meta1.en.toLowerCase() === meta2.en.toLowerCase()) {
    return true;
  }
  if (meta1.km && meta2.km && meta1.km === meta2.km) {
    return true;
  }

  const l1 = clean1.toLowerCase();
  const l2 = clean2.toLowerCase();
  const e1 = meta1.en.toLowerCase();
  const e2 = meta2.en.toLowerCase();

  return l1 === e2 ||
         l2 === e1 ||
         clean1 === meta2.km ||
         clean2 === meta1.km ||
         (e1.length > 3 && l2.includes(e1)) ||
         (e2.length > 3 && l1.includes(e2));
}

