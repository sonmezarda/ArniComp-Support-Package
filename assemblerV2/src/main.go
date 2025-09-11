package main

import (
	"fmt"
	"os"
)

const FILEPATH = "./cfg/test.asm"

func readFile() []byte {
	file, err := os.Open(FILEPATH)
	if err != nil {
		fmt.Println("Error opening file:", err)
		return nil
	}
	content := make([]byte, 100)
	_, err = file.Read(content)

	fmt.Println("File content:\n", string(content))
	file.Close()
	return content
}

func breakLines(data []byte) [][]byte {
	var lines [][]byte
	var buffer []byte
	for _, b := range data {
		if b == '\n' {
			lines = append(lines, buffer)
			buffer = nil
		} else {
			buffer = append(buffer, b)
		}
	}
	if len(buffer) > 0 {
		lines = append(lines, buffer)
	}
	return lines
}

func removeWhitespace(data []byte) []byte {
	var result []byte
	for _, b := range data {
		if b != ' ' && b != '\t' && b != '\n' && b != '\r' {
			result = append(result, b)
		}
	}
	return result
}

func main() {
	content := readFile()
	if content == nil {
		return
	}
	lines := breakLines(content)
	fmt.Println("Lines:")

	for i, line := range lines {
		fmt.Printf("%d: %s\n", i+1, string(line))
	}
}
