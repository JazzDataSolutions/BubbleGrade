package main

import (
	"encoding/json"
	"fmt"
	"image"
	"io"
	"log"
	"net/http"
	"os"
	"runtime"
	"sync"
	"time"

	"gocv.io/x/gocv"
)

// Enhanced result structure with region detection
type ProcessingResult struct {
	Score      int                `json:"score"`
	Answers    []string           `json:"answers"`
	Total      int                `json:"total"`
	Regions    RegionBoundingBoxes `json:"regions"`
	Quality    ImageQualityMetrics `json:"quality"`
	ProcessingTime int64            `json:"processingTimeMs"`
}

type RegionBoundingBoxes struct {
	Nombre BoundingBox `json:"nombre"`
	CURP   BoundingBox `json:"curp"`
	OMR    BoundingBox `json:"omr"`
}

type BoundingBox struct {
	X      int `json:"x"`
	Y      int `json:"y"`
	Width  int `json:"width"`
	Height int `json:"height"`
}

type ImageQualityMetrics struct {
	Resolution struct {
		Width  int `json:"width"`
		Height int `json:"height"`
	} `json:"resolution"`
	Clarity float64 `json:"clarity"`
	Skew    float64 `json:"skew"`
}

type DocumentProcessor struct {
	debug bool
	mutex sync.RWMutex
}

func NewDocumentProcessor(debug bool) *DocumentProcessor {
	return &DocumentProcessor{
		debug: debug,
	}
}

func (dp *DocumentProcessor) ProcessDocument(imgData []byte) (*ProcessingResult, error) {
	startTime := time.Now()
	
	// Decode image
	img, err := gocv.IMDecode(imgData, gocv.IMReadColor)
	if err != nil {
		return nil, fmt.Errorf("failed to decode image: %v", err)
	}
	defer img.Close()

	result := &ProcessingResult{
		ProcessingTime: time.Since(startTime).Milliseconds(),
	}

	// Get image quality metrics
	result.Quality = dp.analyzeImageQuality(&img)

	// Detect and segment regions
	regions, err := dp.detectRegions(&img)
	if err != nil {
		return nil, fmt.Errorf("failed to detect regions: %v", err)
	}
	result.Regions = regions

	// Process OMR section for bubble detection
	omrResults, err := dp.processOMRSection(&img, regions.OMR)
	if err != nil {
		log.Printf("Warning: OMR processing failed: %v", err)
		// Continue with empty results rather than failing completely
		result.Answers = []string{}
		result.Score = 0
		result.Total = 0
	} else {
		result.Answers = omrResults.Answers
		result.Score = omrResults.Score
		result.Total = omrResults.Total
	}

	result.ProcessingTime = time.Since(startTime).Milliseconds()
	return result, nil
}

func (dp *DocumentProcessor) analyzeImageQuality(img *gocv.Mat) ImageQualityMetrics {
	quality := ImageQualityMetrics{}
	
	// Resolution
	quality.Resolution.Width = img.Cols()
	quality.Resolution.Height = img.Rows()
	
	// Calculate clarity using Laplacian variance
	gray := gocv.NewMat()
	defer gray.Close()
	gocv.CvtColor(*img, &gray, gocv.ColorBGRToGray)
	
	laplacian := gocv.NewMat()
	defer laplacian.Close()
	gocv.Laplacian(gray, &laplacian, gocv.MatTypeCV64F, 1, 1, 0, gocv.BorderDefault)
	
	mean, stddev := gocv.MeanStdDev(laplacian, gocv.NewMat())
	quality.Clarity = stddev.Val1 * stddev.Val1 // Variance
	mean.Close()
	stddev.Close()
	
	// Calculate skew (simplified)
	quality.Skew = dp.calculateSkew(&gray)
	
	return quality
}

func (dp *DocumentProcessor) calculateSkew(gray *gocv.Mat) float64 {
	// Detect lines using HoughLines
	edges := gocv.NewMat()
	defer edges.Close()
	gocv.Canny(*gray, &edges, 50, 150, 3, false)
	
	lines := gocv.NewMat()
	defer lines.Close()
	gocv.HoughLines(edges, &lines, 1, 3.14159/180, 100)
	
	if lines.Rows() == 0 {
		return 0.0 // No lines detected
	}
	
	// Calculate average angle of horizontal lines
	var angleSum float64
	var count int
	
	for i := 0; i < lines.Rows(); i++ {
		rho := lines.GetFloatAt(i, 0)
		theta := lines.GetFloatAt(i, 1)
		
		// Filter for roughly horizontal lines
		angleDeg := theta * 180 / 3.14159
		if angleDeg > 170 || angleDeg < 10 {
			angleSum += angleDeg
			count++
		}
		
		_ = rho // Suppress unused variable warning
	}
	
	if count == 0 {
		return 0.0
	}
	
	avgAngle := angleSum / float64(count)
	
	// Normalize to [-90, 90] range
	if avgAngle > 90 {
		avgAngle -= 180
	}
	
	return avgAngle
}

func (dp *DocumentProcessor) detectRegions(img *gocv.Mat) (RegionBoundingBoxes, error) {
	imgHeight := img.Rows()
	imgWidth := img.Cols()
	
	// Default regions based on typical Mexican exam sheet layout
	regions := RegionBoundingBoxes{
		Nombre: BoundingBox{
			X:      int(float64(imgWidth) * 0.15),  // 15% from left
			Y:      int(float64(imgHeight) * 0.08), // 8% from top
			Width:  int(float64(imgWidth) * 0.70),  // 70% width
			Height: int(float64(imgHeight) * 0.06), // 6% height
		},
		CURP: BoundingBox{
			X:      int(float64(imgWidth) * 0.15),  // 15% from left
			Y:      int(float64(imgHeight) * 0.18), // 18% from top
			Width:  int(float64(imgWidth) * 0.70),  // 70% width
			Height: int(float64(imgHeight) * 0.08), // 8% height
		},
		OMR: BoundingBox{
			X:      int(float64(imgWidth) * 0.10),  // 10% from left
			Y:      int(float64(imgHeight) * 0.30), // 30% from top
			Width:  int(float64(imgWidth) * 0.80),  // 80% width
			Height: int(float64(imgHeight) * 0.60), // 60% height
		},
	}

	// TODO: Implement advanced region detection using:
	// 1. Template matching for standard forms
	// 2. Text detection to find "NOMBRE:" and "CURP:" labels
	// 3. Contour detection for OMR grid boundaries
	// 4. Machine learning for adaptive region detection

	return regions, nil
}

type OMRResults struct {
	Answers []string
	Score   int
	Total   int
}

func (dp *DocumentProcessor) processOMRSection(img *gocv.Mat, omrRegion BoundingBox) (*OMRResults, error) {
	// Extract OMR region
	roi := img.Region(image.Rect(
		omrRegion.X,
		omrRegion.Y,
		omrRegion.X+omrRegion.Width,
		omrRegion.Y+omrRegion.Height,
	))
	defer roi.Close()

	// Convert to grayscale
	gray := gocv.NewMat()
	defer gray.Close()
	gocv.CvtColor(roi, &gray, gocv.ColorBGRToGray)

	// Apply adaptive threshold
	binary := gocv.NewMat()
	defer binary.Close()
	gocv.AdaptiveThreshold(gray, &binary, 255, gocv.AdaptiveThresholdMean, gocv.ThresholdBinary, 11, 2)

	// Detect circles using HoughCircles
	circles := gocv.NewMat()
	defer circles.Close()
	
	gocv.HoughCircles(
		gray,
		&circles,
		gocv.HoughGradient,
		1,    // dp
		30,   // minDist
		100,  // param1
		30,   // param2
		10,   // minRadius
		40,   // maxRadius
	)

	// Process detected circles
	answers := make([]string, 10) // Assume 10 questions for demo
	correctAnswers := []string{"A", "B", "C", "D", "A", "B", "C", "D", "A", "B"}
	
	if circles.Cols() > 0 {
		// Group circles by rows and determine answers
		answers = dp.processBubbleGrid(circles, roi.Cols(), roi.Rows())
	}

	// Calculate score
	score := 0
	total := len(correctAnswers)
	for i, answer := range answers {
		if i < len(correctAnswers) && answer == correctAnswers[i] {
			score++
		}
	}
	
	if total > 0 {
		score = (score * 100) / total
	}

	return &OMRResults{
		Answers: answers,
		Score:   score,
		Total:   total,
	}, nil
}

func (dp *DocumentProcessor) processBubbleGrid(circles gocv.Mat, width, height int) []string {
	// This is a simplified implementation
	// In production, you would:
	// 1. Group circles by rows and columns
	// 2. Determine which bubbles are filled based on intensity
	// 3. Map positions to question numbers and answer choices
	
	answers := make([]string, 10)
	choices := []string{"A", "B", "C", "D"}
	
	// Mock processing for demo
	for i := 0; i < 10; i++ {
		if i < circles.Rows() {
			// Simplified: just cycle through choices
			answers[i] = choices[i%4]
		} else {
			answers[i] = "A" // Default
		}
	}
	
	return answers
}

// HTTP handlers
func (dp *DocumentProcessor) gradeHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse multipart form
	err := r.ParseMultipartForm(32 << 20) // 32MB max
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to parse form: %v", err), http.StatusBadRequest)
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get file: %v", err), http.StatusBadRequest)
		return
	}
	defer file.Close()

	log.Printf("🔍 Processing file: %s (size: %d bytes)", header.Filename, header.Size)

	// Read file data
	fileData, err := io.ReadAll(file)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to read file: %v", err), http.StatusInternalServerError)
		return
	}

	// Process document
	result, err := dp.ProcessDocument(fileData)
	if err != nil {
		log.Printf("❌ Processing failed: %v", err)
		http.Error(w, fmt.Sprintf("Processing failed: %v", err), http.StatusInternalServerError)
		return
	}

	log.Printf("✅ Processing completed in %dms - Score: %d%%", result.ProcessingTime, result.Score)

	// Send response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	// Get system info
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	
	health := map[string]interface{}{
		"status":    "healthy",
		"service":   "omr-enhanced",
		"version":   "2.0.0",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"opencv":    gocv.Version(),
		"system": map[string]interface{}{
			"goroutines": runtime.NumGoroutine(),
			"memory_mb":  m.Alloc / 1024 / 1024,
			"gc_cycles":  m.NumGC,
		},
	}
	
	json.NewEncoder(w).Encode(health)
}

func main() {
	// Configure OpenCV
	if gocv.Version() == "" {
		log.Fatal("❌ OpenCV not found. Please install gocv properly.")
	}

	log.Printf("🔍 OMR Enhanced Service starting...")
	log.Printf("📊 OpenCV version: %s", gocv.Version())
	log.Printf("💻 Go version: %s", runtime.Version())

	// Initialize processor
	debug := os.Getenv("DEBUG") == "true"
	processor := NewDocumentProcessor(debug)

	// Setup routes
	http.HandleFunc("/grade", processor.gradeHandler)
	http.HandleFunc("/health", healthHandler)

	// Add CORS middleware for all routes
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}
		
		http.NotFound(w, r)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8090"
	}

	log.Printf("🚀 OMR Enhanced service listening on :%s", port)
	log.Printf("🎯 Endpoints available:")
	log.Printf("   POST /grade - Process document with region detection")
	log.Printf("   GET  /health - Service health check")
	
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal("❌ Server failed to start:", err)
	}
}