import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import compression from 'compression'
import rateLimit from 'express-rate-limit'
import multer from 'multer'
import pino from 'pino'
import { OCRProcessor } from './processors/OCRProcessor'
import { ImagePreprocessor } from './processors/ImagePreprocessor'
import { ValidationService } from './services/ValidationService'
import { HealthService } from './services/HealthService'
import { errorHandler, requestLogger } from './middleware'

// Initialize logger
const logger = pino({
  name: 'ocr-service',
  level: process.env.LOG_LEVEL || 'info',
  ...(process.env.NODE_ENV === 'development' && {
    transport: {
      target: 'pino-pretty',
      options: { colorize: true }
    }
  })
})

// Initialize services
const imagePreprocessor = new ImagePreprocessor()
const ocrProcessor = new OCRProcessor(logger)
const validationService = new ValidationService()
const healthService = new HealthService(ocrProcessor)

const app = express()
const PORT = process.env.PORT || 8100

// Security middleware
app.use(helmet())
app.use(compression())
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['*'],
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))

// Rate limiting
const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30, // 30 requests per minute
  message: 'Too many OCR requests, please try again later',
  standardHeaders: true,
  legacyHeaders: false
})
app.use(limiter)

// Request logging
app.use(requestLogger(logger))

// File upload configuration
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB
    files: 1
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/tiff']
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true)
    } else {
      cb(new Error('Invalid file type. Only JPEG, PNG, and TIFF are allowed.'))
    }
  }
})

// Types
interface OCRRequest {
  region: 'nombre' | 'curp'
  boundingBox: {
    x: number
    y: number
    width: number
    height: number
  }
  preprocessing?: {
    denoise?: boolean
    sharpen?: boolean
    contrast?: number
    brightness?: number
  }
}

interface OCRResponse {
  text: string
  confidence: number
  processing: {
    originalText: string
    correctedText: string
    preprocessing: string[]
    processingTimeMs: number
  }
  boundingBox: OCRRequest['boundingBox']
  region: OCRRequest['region']
}

// Routes
app.post('/ocr', upload.single('image'), async (req, res, next) => {
  try {
    const startTime = Date.now()
    
    // Validate request
    const validation = validationService.validateOCRRequest(req.body)
    if (!validation.isValid) {
      return res.status(400).json({
        error: 'Validation failed',
        details: validation.errors
      })
    }

    if (!req.file) {
      return res.status(400).json({
        error: 'No image file provided'
      })
    }

    const request: OCRRequest = JSON.parse(req.body.request || '{}')
    
    logger.info({
      region: request.region,
      fileSize: req.file.size,
      mimetype: req.file.mimetype
    }, 'Processing OCR request')

    // Preprocess image
    const preprocessedImage = await imagePreprocessor.processRegion(
      req.file.buffer,
      request.boundingBox,
      request.preprocessing
    )

    // Perform OCR based on region type
    let ocrResult: { text: string; confidence: number }
    
    if (request.region === 'nombre') {
      ocrResult = await ocrProcessor.recognizeHandwriting(preprocessedImage)
    } else if (request.region === 'curp') {
      ocrResult = await ocrProcessor.recognizeCURP(preprocessedImage)
    } else {
      throw new Error(`Unsupported region type: ${request.region}`)
    }

    // Post-process results
    const correctedText = request.region === 'curp' 
      ? validationService.correctCURPOCRErrors(ocrResult.text)
      : validationService.normalizeNameText(ocrResult.text)

    const response: OCRResponse = {
      text: correctedText,
      confidence: ocrResult.confidence,
      processing: {
        originalText: ocrResult.text,
        correctedText,
        preprocessing: preprocessedImage.appliedFilters,
        processingTimeMs: Date.now() - startTime
      },
      boundingBox: request.boundingBox,
      region: request.region
    }

    logger.info({
      region: request.region,
      confidence: ocrResult.confidence,
      processingTime: response.processing.processingTimeMs,
      originalLength: ocrResult.text.length,
      correctedLength: correctedText.length
    }, 'OCR processing completed')

    res.json(response)

  } catch (error) {
    next(error)
  }
})

// Batch OCR endpoint
app.post('/ocr/batch', upload.single('image'), async (req, res, next) => {
  try {
    const startTime = Date.now()
    
    if (!req.file) {
      return res.status(400).json({ error: 'No image file provided' })
    }

    const requests: OCRRequest[] = JSON.parse(req.body.requests || '[]')
    
    if (requests.length === 0 || requests.length > 5) {
      return res.status(400).json({ 
        error: 'Invalid request count. Must be between 1 and 5 regions.' 
      })
    }

    logger.info({
      requestCount: requests.length,
      fileSize: req.file.size
    }, 'Processing batch OCR request')

    // Process all regions in parallel
    const results = await Promise.all(
      requests.map(async (request) => {
        try {
          // Validate individual request
          const validation = validationService.validateOCRRequest(request)
          if (!validation.isValid) {
            throw new Error(`Invalid request for region ${request.region}: ${validation.errors.join(', ')}`)
          }

          // Preprocess region
          const preprocessedImage = await imagePreprocessor.processRegion(
            req.file!.buffer,
            request.boundingBox,
            request.preprocessing
          )

          // Perform OCR
          let ocrResult: { text: string; confidence: number }
          
          if (request.region === 'nombre') {
            ocrResult = await ocrProcessor.recognizeHandwriting(preprocessedImage)
          } else if (request.region === 'curp') {
            ocrResult = await ocrProcessor.recognizeCURP(preprocessedImage)
          } else {
            throw new Error(`Unsupported region type: ${request.region}`)
          }

          // Post-process
          const correctedText = request.region === 'curp' 
            ? validationService.correctCURPOCRErrors(ocrResult.text)
            : validationService.normalizeNameText(ocrResult.text)

          return {
            text: correctedText,
            confidence: ocrResult.confidence,
            processing: {
              originalText: ocrResult.text,
              correctedText,
              preprocessing: preprocessedImage.appliedFilters,
              processingTimeMs: Date.now() - startTime
            },
            boundingBox: request.boundingBox,
            region: request.region,
            success: true
          }

        } catch (error) {
          logger.error({ error: error.message, region: request.region }, 'Failed to process region')
          return {
            region: request.region,
            boundingBox: request.boundingBox,
            success: false,
            error: error.message
          }
        }
      })
    )

    const successfulResults = results.filter(r => r.success)
    const failedResults = results.filter(r => !r.success)

    logger.info({
      totalRequests: requests.length,
      successful: successfulResults.length,
      failed: failedResults.length,
      totalTime: Date.now() - startTime
    }, 'Batch OCR processing completed')

    res.json({
      results: successfulResults,
      errors: failedResults,
      summary: {
        total: requests.length,
        successful: successfulResults.length,
        failed: failedResults.length,
        processingTimeMs: Date.now() - startTime
      }
    })

  } catch (error) {
    next(error)
  }
})

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const health = await healthService.getHealthStatus()
    const statusCode = health.status === 'healthy' ? 200 : 503
    res.status(statusCode).json(health)
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    })
  }
})

// Performance metrics endpoint
app.get('/metrics', async (req, res) => {
  try {
    const metrics = await healthService.getMetrics()
    res.json(metrics)
  } catch (error) {
    res.status(500).json({
      error: 'Failed to retrieve metrics',
      details: error.message
    })
  }
})

// Error handling
app.use(errorHandler(logger))

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    availableEndpoints: [
      'POST /ocr - Single region OCR processing',
      'POST /ocr/batch - Batch region OCR processing',
      'GET /health - Service health check',
      'GET /metrics - Performance metrics'
    ]
  })
})

// Start server
app.listen(PORT, () => {
  logger.info({
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    version: process.env.npm_package_version || '1.0.0'
  }, '🔤 OCR Service started successfully')
})

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('Received SIGTERM, shutting down gracefully')
  process.exit(0)
})

process.on('SIGINT', () => {
  logger.info('Received SIGINT, shutting down gracefully')
  process.exit(0)
})

export default app