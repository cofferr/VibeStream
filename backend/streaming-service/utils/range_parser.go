package utils

import (
	"strconv"
	"strings"
)

func ParseRange(rangeHeader string, fileSize int64) (int64, int64) {
	var start, end int64 = 0, fileSize - 1

	if rangeHeader == "" {
		return start, end
	}

	rangeParts := strings.Split(strings.Replace(rangeHeader, "bytes=", "", 1), "-")
	if len(rangeParts) > 0 && rangeParts[0] != "" {
		s, _ := strconv.ParseInt(rangeParts[0], 10, 64)
		start = s
	}
	if len(rangeParts) > 1 && rangeParts[1] != "" {
		e, _ := strconv.ParseInt(rangeParts[1], 10, 64)
		end = e
	}
	return start, end
}
