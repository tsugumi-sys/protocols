package main

import (
	"log"
	"net/http"
)

func main() {
	resp, err := http.Head("http://localhost:18888")
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()

	log.Println("status:", resp.Status)
	log.Println("headers:", resp.Header)
}
