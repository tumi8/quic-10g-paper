package main

import (
	"crypto/tls"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"

	"github.com/lucas-clemente/quic-go"
	"github.com/lucas-clemente/quic-go/http3"
	"github.com/lucas-clemente/quic-go/internal/handshake"
	"github.com/lucas-clemente/quic-go/interop/utils"
)

var tlsConf *tls.Config

func main() {
	logs := os.Getenv("LOGS")
	logFile, err := os.Create(logs + "/log.txt")
	if err != nil {
		fmt.Printf("Could not create log file: %s\n", err.Error())
		os.Exit(1)
	}
	defer logFile.Close()
	log.SetOutput(logFile)

	keyLog, err := utils.GetSSLKeyLog()
	if err != nil {
		fmt.Printf("Could not create key log: %s\n", err.Error())
		os.Exit(1)
	}
	if keyLog != nil {
		defer keyLog.Close()
	}

	testcase := os.Getenv("TESTCASE")

	// a quic.Config that doesn't do a Retry
	quicConf := &quic.Config{
		RequireAddressValidation: func(net.Addr) bool { return testcase == "retry" },
	}

	handshake.KeyUpdateInterval = 1 << 24

	if testcase == "versionnegotiation" {
		quicConf.Versions = []quic.VersionNumber{quic.Version1}
	}

	certdir := os.Getenv("CERTS")
	cert, err := tls.LoadX509KeyPair(certdir+"/cert.pem", certdir+"/priv.key")
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	tlsConf = &tls.Config{
		Certificates: []tls.Certificate{cert},
		KeyLogWriter: keyLog,
	}

	switch testcase {
	case "retry", "versionnegotiation", "handshake", "transfer", "resumption", "zerortt", "multihandshake", "goodput", "optimize", "qlog":
		err = runHTTP3Server(quicConf)
	case "transportparameter":
		quicConf.MaxIncomingStreams = 10
		err = runHTTP3Server(quicConf)
	case "chacha20":
		tlsConf.CipherSuites = []uint16{tls.TLS_CHACHA20_POLY1305_SHA256}
		err = runHTTP3Server(quicConf)
	case "http3":
		err = runHTTP3Server(quicConf)
	default:
		fmt.Printf("unsupported test case: %s\n", testcase)
		os.Exit(127)
	}

	if err != nil {
		fmt.Printf("Error running server: %s\n", err.Error())
		os.Exit(1)
	}
}

func runHTTP3Server(quicConf *quic.Config) error {
	ip := os.Getenv("IP")
	port := os.Getenv("PORT")
	server := http3.Server{
		Addr:       ip + ":" + port,
		TLSConfig:  tlsConf,
		QuicConfig: quicConf,
	}
	www := os.Getenv("WWW")
	http.DefaultServeMux.Handle("/", http.FileServer(http.Dir(www)))
	return server.ListenAndServe()
}
