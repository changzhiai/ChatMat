/**
 * Parse natural language input to extract material, supercell, structure type, etc.
 * Port of the Python parse_material_request function from app.py
 */

export function parseMaterialRequest(text) {
  const textLower = text.toLowerCase();

  // Initialize defaults
  const result = {
    material_name: "Si",
    supercell_dims: [1, 1, 1],
    structure_type: null,
    lattice_parameter: null,
    compound: null,
    source_type: null,
    source_params: {},
    use_llm: false,
    llm_provider: null,
    llm_params: {}
  };

  // Extract supercell dimensions (e.g., "2x2x2", "3x3x3", "2 2 2")
  const supercellPatterns = [
    /(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)/,  // 2x2x2, 3×3×3
    /supercell\s*[:\s]+(\d+)\s*[x×,]\s*(\d+)\s*[x×,]\s*(\d+)/,  // supercell: 2x2x2
    /(\d+)\s+(\d+)\s+(\d+)/  // 2 2 2
  ];

  for (const pattern of supercellPatterns) {
    const match = textLower.match(pattern);
    if (match) {
      result.supercell_dims = [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
      break;
    }
  }

  // Extract structure types
  const structureKeywords = {
    fcc: ["fcc", "face-centered cubic", "face centered cubic"],
    bcc: ["bcc", "body-centered cubic", "body centered cubic"],
    hcp: ["hcp", "hexagonal close-packed", "hexagonal close packed"],
    diamond: ["diamond", "diamond cubic"],
    sc: ["sc", "simple cubic"],
    zincblende: ["zincblende", "zinc blende", "sphalerite"],
    rocksalt: ["rocksalt", "rock salt", "nacl structure"],
    wurtzite: ["wurtzite"],
    perovskite: ["perovskite"],
    rutile: ["rutile"]
  };

  for (const [structType, keywords] of Object.entries(structureKeywords)) {
    if (keywords.some(kw => textLower.includes(kw))) {
      result.structure_type = structType;
      break;
    }
  }

  // Extract lattice parameter (e.g., "a=5.43", "lattice 4.08")
  const latticePatterns = [
    /[al]\s*=\s*([\d.]+)/,
    /lattice\s*(?:parameter|constant)?\s*[:=]?\s*([\d.]+)/,
    /a\s*=\s*([\d.]+)/
  ];
  for (const pattern of latticePatterns) {
    const match = textLower.match(pattern);
    if (match) {
      result.lattice_parameter = parseFloat(match[1]);
      break;
    }
  }

  // Common words to filter out
  const commonWords = new Set(["the", "for", "get", "calculate", "energy", "force", 
    "structure", "supercell", "bulk", "of", "a", "an", "in", "on", "at"]);

  // Extract compounds FIRST before elements to avoid false matches
  const compoundMap = {
    "nacl": { name: "NaCl", compound: ["Na", "Cl"] },
    "sodium chloride": { name: "NaCl", compound: ["Na", "Cl"] },
    "mgo": { name: "MgO", compound: ["Mg", "O"] },
    "magnesium oxide": { name: "MgO", compound: ["Mg", "O"] },
    "gan": { name: "GaN", compound: ["Ga", "N"] },
    "gallium nitride": { name: "GaN", compound: ["Ga", "N"] },
    "gap": { name: "GaP", compound: ["Ga", "P"] },
    "gallium phosphide": { name: "GaP", compound: ["Ga", "P"] },
    "zns": { name: "ZnS", compound: ["Zn", "S"] },
    "zinc sulfide": { name: "ZnS", compound: ["Zn", "S"] },
    "tio2": { name: "TiO2", compound: ["Ti", "O"] },
    "titanium dioxide": { name: "TiO2", compound: ["Ti", "O"] },
    "sio2": { name: "SiO2", compound: ["Si", "O"], structure_type: "quartz" },
    "silicon dioxide": { name: "SiO2", compound: ["Si", "O"], structure_type: "quartz" },
    "quartz": { name: "SiO2", compound: ["Si", "O"], structure_type: "quartz" },
    "catio3": { name: "CaTiO3", compound: ["Ca", "Ti", "O"] },
    "calcium titanate": { name: "CaTiO3", compound: ["Ca", "Ti", "O"] }
  };

  for (const [key, value] of Object.entries(compoundMap)) {
    if (textLower.includes(key)) {
      result.material_name = value.name;
      result.compound = value.compound;
      if (value.structure_type) {
        result.structure_type = value.structure_type;
      }
      return result;
    }
  }

  // Check for compound formulas (e.g., "NaCl", "GaN", "SiO2")
  if (!result.compound) {
    const compoundPattern = /\b([A-Z][a-z]?[A-Z]?[a-z]?\d*)\b/g;
    const compoundMatches = text.match(compoundPattern) || [];
    
    for (const match of compoundMatches) {
      if (!commonWords.has(match.toLowerCase())) {
        if (/\d/.test(match)) {  // Has numbers, likely compound
          result.material_name = match;
          const elements = match.match(/[A-Z][a-z]?/g) || [];
          if (elements.length >= 2) {
            result.compound = elements;
            break;
          }
        } else if (match.length === 2 && /[A-Z]/.test(match[0]) && /[A-Z]/.test(match[1])) {
          result.material_name = match;
          result.compound = [match[0], match[1]];
          break;
        }
      }
    }
  }

  // Only check for elements if we haven't found a compound
  if (!result.compound) {
    const elementMap = {
      "silicon": "Si", "si": "Si",
      "aluminum": "Al", "aluminium": "Al", "al": "Al",
      "gold": "Au", "au": "Au",
      "copper": "Cu", "cu": "Cu",
      "iron": "Fe", "fe": "Fe",
      "titanium": "Ti", "ti": "Ti",
      "magnesium": "Mg", "mg": "Mg",
      "nickel": "Ni", "ni": "Ni",
      "zinc": "Zn", "zn": "Zn",
      "carbon": "C", "c": "C",
      "germanium": "Ge", "ge": "Ge",
      "chromium": "Cr", "cr": "Cr",
      "molybdenum": "Mo", "mo": "Mo",
      "tungsten": "W", "w": "W",
      "vanadium": "V", "v": "V",
      "cobalt": "Co", "co": "Co",
      "palladium": "Pd", "pd": "Pd",
      "platinum": "Pt", "pt": "Pt",
      "silver": "Ag", "ag": "Ag",
      "beryllium": "Be", "be": "Be",
      "zirconium": "Zr", "zr": "Zr"
    };

    for (const [name, symbol] of Object.entries(elementMap)) {
      if (textLower.includes(name)) {
        result.material_name = symbol;
        break;
      }
    }

    // Check for chemical symbols directly if still default
    if (result.material_name === "Si") {
      const elementSymbols = text.match(/\b([A-Z][a-z]?)\b/g) || [];
      const potentialElements = elementSymbols.filter(m => !commonWords.has(m.toLowerCase()) && m.length <= 2);
      if (potentialElements.length > 0) {
        result.material_name = potentialElements[0];
      }
    }
  }

  // Detect external source types
  const mpMatch = text.match(/\bmp-\d+\b/i);
  if (mpMatch) {
    result.material_name = mpMatch[0];
    result.source_type = "mp";
    return result;
  }

  const codMatch = text.match(/\bcod-?\d+\b/i);
  if (codMatch) {
    result.material_name = codMatch[0].replace(/^cod-?/, "");
    result.source_type = "cod";
    return result;
  }

  const urlMatch = text.match(/https?:\/\/\S+/);
  if (urlMatch) {
    result.material_name = urlMatch[0];
    result.source_type = "url";
    return result;
  }

  if (/[\/\\]/.test(text) || /\.(cif|xyz|vasp|poscar)$/.test(text)) {
    result.material_name = text.trim();
    result.source_type = "file";
  }

  return result;
}
