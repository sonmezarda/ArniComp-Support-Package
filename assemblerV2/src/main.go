package main

import (
	"assemblerV2/cfg"
	"assemblerV2/pkg/oneline"
	"fmt"
	"os"
)

func readFile() []byte {
	file, err := os.Open(cfg.FILEPATH)
	if err != nil {
		fmt.Println("Error opening file:", err)
		return nil
	}
	content := make([]byte, 100)
	_, err = file.Read(content)
	if err != nil {
		fmt.Println("Error reading file:", err)
		return nil
	}
	file.Close()
	return content
}

func breakLines(data []byte) [][]byte {
	var lines [][]byte
	var buffer []byte
	for _, b := range data {
		if b == '\n' {
			if len(buffer) > 0 {
				lines = append(lines, buffer)
			}
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

func removeComments(lines [][]byte) [][]byte {
	var result [][]byte
	for _, line := range lines {
		cleanLine := oneline.RemoveComment(line)
		if len(cleanLine) > 0 {
			result = append(result, cleanLine)
		}
	}
	return result
}

func getLabels(lines [][]byte) map[string]int {
	labels := make(map[string]int)
	labelCount := 0
	for i, line := range lines {
		label := oneline.GetLabelName(line)
		if label == "" {
			continue
		}
		labels[label] = i - labelCount
		labelCount++
	}
	return labels
}

func removeLabels(lines [][]byte) [][]byte {
	var result [][]byte
	for _, line := range lines {
		if oneline.IsLabel(line) {
			continue
		}
		result = append(result, line)
	}
	return result
}

func printLines(lines [][]byte) {
	for i, line := range lines {
		fmt.Printf("%d: %s\n", i, string(line))
	}
}

func TrimSpaces(lines [][]byte) [][]byte {
	var result [][]byte
	for _, line := range lines {
		trimmed := oneline.TrimSpaces(line)
		if len(trimmed) > 0 {
			result = append(result, trimmed)
		}
	}
	return result
}

func getConstants(lines [][]byte) map[string]string {
	constants := make(map[string]string)
	for _, line := range lines {
		if oneline.IsConstantDefine(line) {
			name, value := oneline.GetConstantDefineParts(line)
			constants[name] = value
		}
	}
	return constants
}

func removeConstants(lines [][]byte) [][]byte {
	var result [][]byte
	for _, line := range lines {
		if oneline.IsConstantDefine(line) {
			continue
		}
		result = append(result, line)
	}
	return result
}

func lowerAll(lines [][]byte) [][]byte {
	var result [][]byte
	for _, line := range lines {
		var lowerLine []byte
		for _, b := range line {
			if b >= 'A' && b <= 'Z' {
				lowerLine = append(lowerLine, b+'a'-'A')
			} else {
				lowerLine = append(lowerLine, b)
			}
		}
		result = append(result, lowerLine)
	}
	return result
}

func main() {
	content := readFile()
	if content == nil {
		return
	}

	lines := breakLines(content)
	lines = removeComments(lines)
	lines = TrimSpaces(lines)
	lines = lowerAll(lines)
	constants := getConstants(lines)
	lines = removeConstants(lines)
	labels := getLabels(lines)
	lines = removeLabels(lines)

	printLines(lines)
	fmt.Println("Labels:")
	for label, line := range labels {
		fmt.Printf("%s: %d\n", label, line)
	}
	fmt.Println("Constants:")
	for name, value := range constants {
		fmt.Printf("%s: %s\n", name, value)
	}
}
