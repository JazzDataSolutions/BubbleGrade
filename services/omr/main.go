
package main

import (
    "encoding/json"
    "image"
    _ "image/jpeg"
    "log"
    "net/http"
    "os"
)

type Result struct {
    Score int `json:"score"`
}

func grade(w http.ResponseWriter, r *http.Request) {
    file, _, err := r.FormFile("file")
    if err != nil { http.Error(w, err.Error(), 400); return }
    defer file.Close()
    _, _, err = image.Decode(file)
    if err != nil { http.Error(w, err.Error(), 400); return }
    res := Result{Score: 100}
    json.NewEncoder(w).Encode(res)
}

func main() {
    http.HandleFunc("/grade", grade)
    port := os.Getenv("PORT")
    if port == "" { port = "8090" }
    log.Printf("OMR listening on :%s", port)
    log.Fatal(http.ListenAndServe(":"+port, nil))
}
