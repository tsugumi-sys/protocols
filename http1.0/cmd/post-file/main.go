package main

import (
	"log"
	"net/http"
	"os"
)

func main() {
	file, err := os.Open("./Form.md")
	if err != nil {
		panic(err)
	}
	// x-www-form-urlencoded
	resp, err := http.Post("http://localhost:18888", "test/plain", file)
	if err != nil {
		panic(err)
	}
	log.Println("status:", resp.Status)
}
