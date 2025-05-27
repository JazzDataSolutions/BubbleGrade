package main

import (
	"encoding/json"
	"fmt"
	"image"
	_ "image/jpeg"
	_ "image/png"
	"log"
	"math"
	"net/http"
	"os"
	"sort"

	"gocv.io/x/gocv"
)

type Result struct {
	Score   int      `json:"score"`
	Answers []string `json:"answers"`
	Total   int      `json:"total"`
}

type Circle struct {
	X      int
	Y      int
	Radius int
	Filled bool
}

func detectBubbles(img gocv.Mat) []Circle {
	gray := gocv.NewMat()
	defer gray.Close()
	
	gocv.CvtColor(img, &gray, gocv.ColorBGRToGray)
	
	blurred := gocv.NewMat()
	defer blurred.Close()
	gocv.GaussianBlur(gray, &blurred, image.Pt(5, 5), 0, 0, gocv.BorderDefault)
	
	circles := gocv.NewMat()
	defer circles.Close()
	
	gocv.HoughCircles(blurred, &circles, gocv.HoughGradient, 1, 20, 100, 30, 10, 50)
	
	var bubbles []Circle
	for i := 0; i < circles.Cols(); i++ {
		v := circles.GetVecfAt(0, i)
		if len(v) >= 3 {
			x := int(v[0])
			y := int(v[1])
			radius := int(v[2])
			
			filled := isBubbleFilled(gray, x, y, radius)
			bubbles = append(bubbles, Circle{
				X:      x,
				Y:      y,
				Radius: radius,
				Filled: filled,
			})
		}
	}
	
	return bubbles
}

func isBubbleFilled(gray gocv.Mat, x, y, radius int) bool {
	roi := gray.Region(image.Rect(
		max(0, x-radius),
		max(0, y-radius),
		min(gray.Cols(), x+radius),
		min(gray.Rows(), y+radius),
	))
	defer roi.Close()
	
	mean := gocv.Mean(roi)
	threshold := 100.0
	
	return mean.Val1 < threshold
}

func organizeAnswers(bubbles []Circle) []string {
	if len(bubbles) == 0 {
		return []string{}
	}
	
	sort.Slice(bubbles, func(i, j int) bool {
		if math.Abs(float64(bubbles[i].Y-bubbles[j].Y)) < 30 {
			return bubbles[i].X < bubbles[j].X
		}
		return bubbles[i].Y < bubbles[j].Y
	})
	
	var answers []string
	var currentRow []Circle
	lastY := bubbles[0].Y
	
	for _, bubble := range bubbles {
		if math.Abs(float64(bubble.Y-lastY)) > 30 {
			if len(currentRow) > 0 {
				answer := processRow(currentRow)
				if answer != "" {
					answers = append(answers, answer)
				}
			}
			currentRow = []Circle{bubble}
			lastY = bubble.Y
		} else {
			currentRow = append(currentRow, bubble)
		}
	}
	
	if len(currentRow) > 0 {
		answer := processRow(currentRow)
		if answer != "" {
			answers = append(answers, answer)
		}
	}
	
	return answers
}

func processRow(row []Circle) string {
	sort.Slice(row, func(i, j int) bool {
		return row[i].X < row[j].X
	})
	
	options := []string{"A", "B", "C", "D", "E"}
	for i, bubble := range row {
		if bubble.Filled && i < len(options) {
			return options[i]
		}
	}
	return ""
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func grade(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	file, _, err := r.FormFile("file")
	if err != nil {
		http.Error(w, fmt.Sprintf("Error reading file: %v", err), 400)
		return
	}
	defer file.Close()
	
	img, _, err := image.Decode(file)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error decoding image: %v", err), 400)
		return
	}
	
	mat, err := gocv.ImageToMatRGB(img)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error converting to OpenCV Mat: %v", err), 500)
		return
	}
	defer mat.Close()
	
	bubbles := detectBubbles(mat)
	answers := organizeAnswers(bubbles)
	
	correctAnswers := []string{"A", "B", "C", "D", "A", "B", "C", "D", "A", "B"}
	score := calculateScore(answers, correctAnswers)
	
	result := Result{
		Score:   score,
		Answers: answers,
		Total:   len(correctAnswers),
	}
	
	json.NewEncoder(w).Encode(result)
}

func calculateScore(answers, correct []string) int {
	if len(answers) == 0 || len(correct) == 0 {
		return 0
	}
	
	score := 0
	maxLen := min(len(answers), len(correct))
	
	for i := 0; i < maxLen; i++ {
		if answers[i] == correct[i] {
			score++
		}
	}
	
	return int(float64(score) / float64(len(correct)) * 100)
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy", "service": "omr"})
}

func main() {
	http.HandleFunc("/grade", grade)
	http.HandleFunc("/health", healthCheck)
	
	port := os.Getenv("PORT")
	if port == "" {
		port = "8090"
	}
	
	log.Printf("🔍 OMR service listening on :%s", port)
	log.Printf("📊 Ready to process bubble sheets!")
	log.Fatal(http.ListenAndServe(":"+port, nil))
}