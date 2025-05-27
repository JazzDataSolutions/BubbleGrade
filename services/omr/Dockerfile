
FROM golang:1.22-alpine as build
WORKDIR /src
COPY . .
RUN go build -o /omr

FROM alpine:3.19
COPY --from=build /omr /omr
EXPOSE 8090
CMD ["/omr"]
