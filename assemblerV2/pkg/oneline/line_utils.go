package oneline

import "assemblerV2/cfg"

func RemoveComment(line []byte) []byte {
	for i, b := range line {
		if b == cfg.COMMENT_SYMBOL {
			return line[:i]
		}
	}
	return line
}

func IsLabel(line []byte) bool {
	return line[len(line)-1] == ':'
}

func GetLabelName(line []byte) string {
	if IsLabel(line) {
		return string(line[:len(line)-1])
	}
	return ""
}

func SplitInstruction(line []byte) (string, []byte) {
	var opcode string
	var operand []byte
	for i, b := range line {
		if b == ' ' || b == '\t' {
			opcode = string(line[:i])
			operand = line[i+1:]
			return opcode, operand
		}
	}
	opcode = string(line)
	return opcode, nil
}

func TrimSpaces(line []byte) []byte {
	start := 0
	end := len(line) - 1
	for start <= end && (line[start] == ' ' || line[start] == '\t') {
		start++
	}
	for end >= start && (line[end] == ' ' || line[end] == '\t') {
		end--
	}
	if start > end {
		return nil
	}
	return line[start : end+1]
}

func IsConstantDefine(line []byte) bool {
	opcode, _ := SplitInstruction(line)
	return opcode == "equ"
}

func GetConstantDefineParts(line []byte) (string, string) {

	opcode, operand := SplitInstruction(line)
	if opcode != "equ" || operand == nil {
		return "", ""
	}
	var name string
	var value []byte
	for i, b := range operand {
		if b == ' ' || b == '\t' {
			name = string(TrimSpaces(operand[:i]))
			value = operand[i+1:]
			return name, string(TrimSpaces(value))
		}
	}
	name = string(operand)
	return name, ""
}
