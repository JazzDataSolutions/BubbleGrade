# Use OpenCV-enabled Go image
FROM denismakogon/gocv:4.6.0-ubuntu AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=1 GOOS=linux go build -ldflags="-s -w" -o omr main.go

# Production stage
FROM denismakogon/gocv:4.6.0-ubuntu-runtime

WORKDIR /app

# Copy the binary from builder stage
COPY --from=builder /app/omr .

# Expose port
EXPOSE 8090

# Run the application
CMD ["./omr"]