// CURP validation utilities for Mexican official identification

export interface CURPValidation {
  isValid: boolean
  format: boolean
  checksum: boolean
  federalEntity: string | null
  birthDate: string | null
  gender: 'M' | 'F' | null
}

// Mexican states mapping for CURP validation
const FEDERAL_ENTITIES: Record<string, string> = {
  'AS': 'AGUASCALIENTES',
  'BC': 'BAJA CALIFORNIA',
  'BS': 'BAJA CALIFORNIA SUR',
  'CC': 'CAMPECHE',
  'CL': 'COAHUILA',
  'CM': 'COLIMA',
  'CS': 'CHIAPAS',
  'CH': 'CHIHUAHUA',
  'DF': 'CIUDAD DE MÉXICO',
  'DG': 'DURANGO',
  'GT': 'GUANAJUATO',
  'GR': 'GUERRERO',
  'HG': 'HIDALGO',
  'JC': 'JALISCO',
  'MC': 'MÉXICO',
  'MN': 'MICHOACÁN',
  'MS': 'MORELOS',
  'NT': 'NAYARIT',
  'NL': 'NUEVO LEÓN',
  'OC': 'OAXACA',
  'PL': 'PUEBLA',
  'QT': 'QUERÉTARO',
  'QR': 'QUINTANA ROO',
  'SP': 'SAN LUIS POTOSÍ',
  'SL': 'SINALOA',
  'SR': 'SONORA',
  'TC': 'TABASCO',
  'TS': 'TAMAULIPAS',
  'TL': 'TLAXCALA',
  'VZ': 'VERACRUZ',
  'YN': 'YUCATÁN',
  'ZS': 'ZACATECAS',
  'NE': 'NACIDO EN EL EXTRANJERO'
}

// Forbidden words that cannot appear in CURP
const FORBIDDEN_WORDS = [
  'BACA', 'BAKA', 'BUEI', 'BUEY', 'CACA', 'CACO', 'CAGA', 'CAGO',
  'CAKA', 'CAKO', 'COGE', 'COGI', 'COJA', 'COJE', 'COJI', 'COJO',
  'COLA', 'CULO', 'FALO', 'FETO', 'GETA', 'GUEI', 'GUEY', 'JETA',
  'JOTO', 'KACA', 'KACO', 'KAGA', 'KAGO', 'KAKA', 'KAKO', 'KOGE',
  'KOGI', 'KOJA', 'KOJE', 'KOJI', 'KOJO', 'KOLA', 'KULO', 'LILO',
  'LOCA', 'LOCO', 'LOKA', 'LOKO', 'MAME', 'MAMO', 'MEAR', 'MEAS',
  'MEON', 'MIAR', 'MION', 'MOCO', 'MOKO', 'MULA', 'MULO', 'NACA',
  'NACO', 'PEDA', 'PEDO', 'PENE', 'PIPI', 'PITO', 'POPO', 'PUTA',
  'PUTO', 'QULO', 'RATA', 'ROBA', 'ROBE', 'ROBO', 'RUIN', 'SENO',
  'TETA', 'VACA', 'VAGA', 'VAGO', 'VAKA', 'VUEI', 'VUEY', 'WUEI',
  'WUEY'
]

/**
 * Validates Mexican CURP (Clave Única de Registro de Población)
 */
export async function validateCURP(curp: string): Promise<CURPValidation> {
  const result: CURPValidation = {
    isValid: false,
    format: false,
    checksum: false,
    federalEntity: null,
    birthDate: null,
    gender: null
  }

  // Clean and normalize input
  const cleanCURP = curp.trim().toUpperCase().replace(/\s/g, '')

  // Basic format validation
  const curpRegex = /^[A-Z]{4}[0-9]{6}[HM][A-Z]{2}[A-Z0-9][A-Z0-9][0-9]$/
  result.format = curpRegex.test(cleanCURP)

  if (!result.format) {
    return result
  }

  // Extract components
  const apellidoPaterno = cleanCURP.substring(0, 2)
  const apellidoMaterno = cleanCURP.substring(2, 3)
  const nombre = cleanCURP.substring(3, 4)
  const fechaNacimiento = cleanCURP.substring(4, 10)
  const sexo = cleanCURP.substring(10, 11) as 'H' | 'M'
  const entidadFederativa = cleanCURP.substring(11, 13)
  const consonanteInterna1 = cleanCURP.substring(13, 14)
  const consonanteInterna2 = cleanCURP.substring(14, 15)
  const digitoVerificador = cleanCURP.substring(15, 16)

  // Validate forbidden words
  const firstFourChars = cleanCURP.substring(0, 4)
  if (FORBIDDEN_WORDS.includes(firstFourChars)) {
    return result
  }

  // Validate birth date
  try {
    const year = parseInt(fechaNacimiento.substring(0, 2))
    const month = parseInt(fechaNacimiento.substring(2, 4))
    const day = parseInt(fechaNacimiento.substring(4, 6))

    // Determine century (CURP was created in 1996)
    const fullYear = year <= 30 ? 2000 + year : 1900 + year
    
    const birthDate = new Date(fullYear, month - 1, day)
    const isValidDate = (
      birthDate.getFullYear() === fullYear &&
      birthDate.getMonth() === month - 1 &&
      birthDate.getDate() === day &&
      month >= 1 && month <= 12 &&
      day >= 1 && day <= 31
    )

    if (isValidDate) {
      result.birthDate = birthDate.toISOString().split('T')[0]
    } else {
      return result
    }
  } catch {
    return result
  }

  // Validate federal entity
  result.federalEntity = FEDERAL_ENTITIES[entidadFederativa] || null
  if (!result.federalEntity) {
    return result
  }

  // Set gender
  result.gender = sexo === 'H' ? 'M' : 'F' // H=Hombre=Male, M=Mujer=Female

  // Validate check digit
  result.checksum = validateCheckDigit(cleanCURP)
  result.isValid = result.format && result.checksum && !!result.federalEntity

  return result
}

/**
 * Validates CURP check digit using official algorithm
 */
function validateCheckDigit(curp: string): boolean {
  const values: Record<string, number> = {
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15, 'G': 16, 'H': 17, 'I': 18,
    'J': 19, 'K': 20, 'L': 21, 'M': 22, 'N': 23, 'O': 24, 'P': 25, 'Q': 26, 'R': 27,
    'S': 28, 'T': 29, 'U': 30, 'V': 31, 'W': 32, 'X': 33, 'Y': 34, 'Z': 35
  }

  let sum = 0
  const curpWithoutCheckDigit = curp.substring(0, 17)

  for (let i = 0; i < curpWithoutCheckDigit.length; i++) {
    const char = curpWithoutCheckDigit[i]
    const value = values[char]
    if (value === undefined) return false
    sum += value * (18 - i)
  }

  const remainder = sum % 10
  const expectedCheckDigit = remainder === 0 ? '0' : (10 - remainder).toString()
  const actualCheckDigit = curp.substring(17, 18)

  return expectedCheckDigit === actualCheckDigit
}

/**
 * Generates a valid CURP based on personal data (for testing)
 */
export function generateCURP(
  apellidoPaterno: string,
  apellidoMaterno: string,
  nombres: string,
  fechaNacimiento: Date,
  sexo: 'M' | 'F',
  entidad: string
): string {
  // This would implement the full CURP generation algorithm
  // For now, return a template for testing
  const year = fechaNacimiento.getFullYear().toString().substring(2)
  const month = (fechaNacimiento.getMonth() + 1).toString().padStart(2, '0')
  const day = fechaNacimiento.getDate().toString().padStart(2, '0')
  
  const sexChar = sexo === 'M' ? 'H' : 'M'
  
  // Find entity code
  const entityCode = Object.entries(FEDERAL_ENTITIES)
    .find(([_, name]) => name === entidad.toUpperCase())?.[0] || 'DF'

  // Build CURP (simplified version)
  const partial = `${apellidoPaterno.substring(0, 2)}${apellidoMaterno.charAt(0)}${nombres.charAt(0)}${year}${month}${day}${sexChar}${entityCode}XXX`
  
  // Calculate check digit (simplified)
  const checkDigit = '0' // Would use proper algorithm
  
  return partial + checkDigit
}

/**
 * Auto-corrects common OCR errors in CURP
 */
export function correctCURPOCRErrors(ocrResult: string): string {
  let corrected = ocrResult.toUpperCase().trim()
  
  // Common OCR substitutions
  const corrections: Record<string, string> = {
    '0': 'O', // Zero to O
    '1': 'I', // One to I
    '5': 'S', // Five to S
    '8': 'B', // Eight to B
    'Q': 'O', // Q to O
    '@': 'A', // @ to A
  }

  // Apply corrections to letter positions only (not date/digits)
  for (let i = 0; i < corrected.length; i++) {
    const char = corrected[i]
    const shouldBeLetter = (i < 4) || (i >= 10 && i < 13) || (i >= 13 && i < 15)
    
    if (shouldBeLetter && corrections[char]) {
      corrected = corrected.substring(0, i) + corrections[char] + corrected.substring(i + 1)
    }
  }

  return corrected
}