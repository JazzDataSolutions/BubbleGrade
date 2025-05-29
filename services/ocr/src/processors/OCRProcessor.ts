import Tesseract from 'tesseract.js'
import type { Logger } from 'pino'

export interface ProcessedImage {
  buffer: Buffer
  appliedFilters: string[]
}

export interface OCRResult {
  text: string
  confidence: number
}

export class OCRProcessor {
  private logger: Logger
  private handwritingWorker: Tesseract.Worker | null = null
  private printWorker: Tesseract.Worker | null = null
  private isInitialized = false

  constructor(logger: Logger) {
    this.logger = logger
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return

    this.logger.info('Initializing OCR workers...')

    try {
      // Initialize handwriting recognition worker
      this.handwritingWorker = await Tesseract.createWorker({
        logger: m => {
          if (m.status === 'recognizing text') {
            this.logger.debug({ progress: m.progress }, 'Handwriting OCR progress')
          }
        }
      })

      await this.handwritingWorker.loadLanguage('spa') // Spanish
      await this.handwritingWorker.initialize('spa')
      await this.handwritingWorker.setParameters({
        tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑáéíóúñ ',
        tessedit_pageseg_mode: Tesseract.PSM.SINGLE_LINE,
        preserve_interword_spaces: '1',
        tessedit_do_invert: '0'
      })

      // Initialize print text worker for CURP
      this.printWorker = await Tesseract.createWorker({
        logger: m => {
          if (m.status === 'recognizing text') {
            this.logger.debug({ progress: m.progress }, 'Print OCR progress')
          }
        }
      })

      await this.printWorker.loadLanguage('eng')
      await this.printWorker.initialize('eng')
      await this.printWorker.setParameters({
        tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        tessedit_pageseg_mode: Tesseract.PSM.SINGLE_LINE,
        preserve_interword_spaces: '0',
        tessedit_do_invert: '0',
        classify_bln_numeric_mode: '1'
      })

      this.isInitialized = true
      this.logger.info('OCR workers initialized successfully')

    } catch (error) {
      this.logger.error({ error: error.message }, 'Failed to initialize OCR workers')
      throw new Error(`OCR initialization failed: ${error.message}`)
    }
  }

  async recognizeHandwriting(image: ProcessedImage): Promise<OCRResult> {
    await this.initialize()

    if (!this.handwritingWorker) {
      throw new Error('Handwriting worker not initialized')
    }

    try {
      this.logger.debug('Starting handwriting recognition')
      
      const { data } = await this.handwritingWorker.recognize(image.buffer)
      
      // Clean up the recognized text
      let cleanText = data.text
        .trim()
        .replace(/\n/g, ' ')
        .replace(/\s+/g, ' ')
        .toUpperCase()

      // Remove common OCR artifacts for handwriting
      cleanText = this.cleanHandwritingArtifacts(cleanText)

      const confidence = data.confidence / 100 // Convert to 0-1 range

      this.logger.debug({
        originalText: data.text,
        cleanedText: cleanText,
        confidence,
        appliedFilters: image.appliedFilters
      }, 'Handwriting recognition completed')

      return {
        text: cleanText,
        confidence
      }

    } catch (error) {
      this.logger.error({ error: error.message }, 'Handwriting recognition failed')
      throw new Error(`Handwriting OCR failed: ${error.message}`)
    }
  }

  async recognizeCURP(image: ProcessedImage): Promise<OCRResult> {
    await this.initialize()

    if (!this.printWorker) {
      throw new Error('Print worker not initialized')
    }

    try {
      this.logger.debug('Starting CURP recognition')
      
      const { data } = await this.printWorker.recognize(image.buffer)
      
      // Clean up CURP text
      let cleanText = data.text
        .trim()
        .replace(/\n/g, '')
        .replace(/\s+/g, '')
        .toUpperCase()

      // Apply CURP-specific cleaning
      cleanText = this.cleanCURPArtifacts(cleanText)

      const confidence = data.confidence / 100 // Convert to 0-1 range

      this.logger.debug({
        originalText: data.text,
        cleanedText: cleanText,
        confidence,
        appliedFilters: image.appliedFilters
      }, 'CURP recognition completed')

      return {
        text: cleanText,
        confidence
      }

    } catch (error) {
      this.logger.error({ error: error.message }, 'CURP recognition failed')
      throw new Error(`CURP OCR failed: ${error.message}`)
    }
  }

  private cleanHandwritingArtifacts(text: string): string {
    let cleaned = text

    // Common handwriting OCR corrections
    const handwritingCorrections: Record<string, string> = {
      '0': 'O',     // Zero to O
      '1': 'I',     // One to I  
      '5': 'S',     // Five to S
      '8': 'B',     // Eight to B
      '@': 'A',     // @ to A
      '|': 'I',     // Pipe to I
      '!': 'I',     // Exclamation to I
      '¡': 'I',     // Inverted exclamation to I
      '/': '',      // Remove slashes
      '\\': '',     // Remove backslashes
      '_': '',      // Remove underscores
      '-': ' ',     // Dash to space
      '.': '',      // Remove periods
      ',': '',      // Remove commas
    }

    // Apply corrections
    for (const [wrong, correct] of Object.entries(handwritingCorrections)) {
      cleaned = cleaned.replace(new RegExp(wrong, 'g'), correct)
    }

    // Remove extra spaces and trim
    cleaned = cleaned.replace(/\s+/g, ' ').trim()

    // Ensure proper name formatting (first letter of each word capitalized)
    cleaned = cleaned
      .split(' ')
      .map(word => {
        if (word.length === 0) return word
        return word.charAt(0) + word.slice(1).toLowerCase()
      })
      .join(' ')
      .toUpperCase() // Convert back to uppercase for consistency

    return cleaned
  }

  private cleanCURPArtifacts(text: string): string {
    let cleaned = text

    // CURP-specific corrections (must maintain exact 18 characters)
    const curpCorrections: Record<string, string> = {
      'O': '0',     // O to zero in date positions
      'I': '1',     // I to one in date positions  
      'S': '5',     // S to five in date positions
      'B': '8',     // B to eight in date positions
      'G': '6',     // G to six
      'Z': '2',     // Z to two
      'l': '1',     // Lowercase l to 1
      'o': '0',     // Lowercase o to 0
    }

    // Only apply number corrections to positions 4-9 (birth date)
    let result = ''
    for (let i = 0; i < cleaned.length && i < 18; i++) {
      let char = cleaned[i]
      
      // Apply corrections to date section (positions 4-9)
      if (i >= 4 && i <= 9) {
        // Should be numbers
        if (curpCorrections[char]) {
          char = curpCorrections[char]
        }
        // Ensure it's a valid digit
        if (!/[0-9]/.test(char)) {
          char = '0' // Default to 0 if can't determine
        }
      } else {
        // Should be letters in other positions
        if (/[0-9]/.test(char)) {
          // Try to convert numbers back to letters
          const letterCorrections: Record<string, string> = {
            '0': 'O',
            '1': 'I',
            '5': 'S',
            '8': 'B',
            '6': 'G',
            '2': 'Z'
          }
          char = letterCorrections[char] || char
        }
      }
      
      result += char
    }

    // Ensure exactly 18 characters by padding or truncating
    if (result.length < 18) {
      result = result.padEnd(18, 'X') // Pad with X
    } else if (result.length > 18) {
      result = result.substring(0, 18) // Truncate
    }

    return result
  }

  async cleanup(): Promise<void> {
    this.logger.info('Cleaning up OCR workers')

    try {
      if (this.handwritingWorker) {
        await this.handwritingWorker.terminate()
        this.handwritingWorker = null
      }

      if (this.printWorker) {
        await this.printWorker.terminate()
        this.printWorker = null
      }

      this.isInitialized = false
      this.logger.info('OCR workers cleaned up successfully')

    } catch (error) {
      this.logger.error({ error: error.message }, 'Error during OCR cleanup')
    }
  }

  getStatus(): { initialized: boolean; workers: { handwriting: boolean; print: boolean } } {
    return {
      initialized: this.isInitialized,
      workers: {
        handwriting: this.handwritingWorker !== null,
        print: this.printWorker !== null
      }
    }
  }
}