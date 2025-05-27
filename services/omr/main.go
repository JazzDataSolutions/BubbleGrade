package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"math/rand"
	"time"
)

type Result struct {
	Score   int      `json:"score"`
	Answers []string `json:"answers"`
	Total   int      `json:"total"`
}

func grade(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, fmt.Sprintf("Error reading file: %v", err), 400)
		return
	}
	defer file.Close()
	
	log.Printf("📸 Processing file: %s", header.Filename)
	
	// Simulate processing time
	time.Sleep(2 * time.Second)
	
	// Generate mock answers for demo
	correctAnswers := []string{"A", "B", "C", "D", "A", "B", "C", "D", "A", "B"}
	answers := generateMockAnswers(len(correctAnswers))
	score := calculateScore(answers, correctAnswers)
	
	result := Result{
		Score:   score,
		Answers: answers,
		Total:   len(correctAnswers),
	}
	
	log.Printf("✅ Processed successfully - Score: %d%%", score)
	json.NewEncoder(w).Encode(result)
}

func generateMockAnswers(count int) []string {
	options := []string{"A", "B", "C", "D"}
	answers := make([]string, count)
	
	rand.Seed(time.Now().UnixNano())
	
	for i := 0; i < count; i++ {
		// 80% chance of correct answer for demo
		if rand.Float32() < 0.8 {
			answers[i] = []string{"A", "B", "C", "D", "A", "B", "C", "D", "A", "B"}[i]
		} else {
			answers[i] = options[rand.Intn(len(options))]
		}
	}
	
	return answers
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

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
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
	log.Printf("📊 Mock service ready to process bubble sheets!")
	log.Printf("💡 This is a simplified version for demonstration")
	log.Fatal(http.ListenAndServe(":"+port, nil))
}