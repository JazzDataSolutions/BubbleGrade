# ETAPA 1: BUILD
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum* ./
RUN go mod download
COPY . .

# Compila sin CGO para simplificar
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o omr main.go

# ETAPA 2: RUNTIME
FROM alpine:latest

# Instalar certificados SSL para HTTPS
RUN apk add --no-cache ca-certificates

WORKDIR /app
COPY --from=builder /app/omr .

EXPOSE 8090
CMD ["./omr"]

