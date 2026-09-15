package services

import (
	"io"
	"net/http"
	"strconv"
	"streaming-service/utils"

	"github.com/gin-gonic/gin"
)

type StreamingService struct{}

func NewStreamingService() *StreamingService {
	return &StreamingService{}
}

func (s *StreamingService) Stream(c *gin.Context, file io.ReadSeeker, size int64, rangeHeader string) {
	start, end := utils.ParseRange(rangeHeader, size)
	length := end - start + 1

	c.Header("Content-Type", "audio/mpeg")
	c.Header("Content-Length", strconv.FormatInt(length, 10))
	c.Header("Content-Range",
		"bytes "+strconv.FormatInt(start, 10)+"-"+strconv.FormatInt(end, 10)+"/"+strconv.FormatInt(size, 10))
	c.Status(http.StatusPartialContent)

	file.Seek(start, 0)
	buf := make([]byte, 1024*32) // 32KB buffer
	var sent int64

	for sent < length {
		toRead := int64(len(buf))
		if length-sent < toRead {
			toRead = length - sent
		}
		n, err := file.Read(buf[:toRead])
		if n > 0 {
			c.Writer.Write(buf[:n])
			sent += int64(n)
		}
		if err != nil {
			break
		}
	}
}
