# ------------------------------
# ETAPA 1: BUILD
# ------------------------------
# Go ≥1.22 con Debian Bullseye
FROM golang:1.23-bullseye AS builder

# 1. Instalar herramientas de compilación y headers de OpenCV
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      pkg-config \
      libopencv-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copiar módulos e instalar dependencias Go
COPY go.mod go.sum ./
RUN go mod download

# 3. Copiar código y compilar binario Linux
COPY . .
RUN CGO_ENABLED=1 GOOS=linux go build -ldflags="-s -w" -o omr main.go

# ------------------------------
# ETAPA 2: RUNTIME
# ------------------------------
# OpenCV 4.11 precompilado (CPU-only)
FROM gocv/opencv:4.11.0-static

WORKDIR /app

# 4. Copiar binario desde builder
COPY --from=builder /app/omr .

# 5. Configuración final
EXPOSE 8090
CMD ["./omr"]
