package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/tonebridge/go-sdk/tonebridge"
)

func main() {
	// Get API key from environment
	apiKey := os.Getenv("TONEBRIDGE_API_KEY")
	if apiKey == "" {
		log.Fatal("TONEBRIDGE_API_KEY environment variable is required")
	}

	// Create wait group for async operations
	var wg sync.WaitGroup

	// Initialize client with WebSocket callbacks
	client := tonebridge.NewClient(apiKey,
		tonebridge.WithWebSocket(
			// onConnect callback
			func() {
				fmt.Println("✓ WebSocket connected")
			},
			// onDisconnect callback
			func() {
				fmt.Println("✗ WebSocket disconnected")
			},
			// onMessage callback
			func(msg interface{}) {
				fmt.Printf("📨 Message received: %v\n", msg)
			},
			// onError callback
			func(err error) {
				fmt.Printf("❌ WebSocket error: %v\n", err)
			},
		),
	)

	ctx := context.Background()

	// Authenticate to get access token (required for WebSocket)
	fmt.Println("Authenticating...")
	email := os.Getenv("TONEBRIDGE_EMAIL")
	password := os.Getenv("TONEBRIDGE_PASSWORD")
	
	if email != "" && password != "" {
		authResp, err := client.Authenticate(ctx, email, password)
		if err != nil {
			log.Printf("Warning: Authentication failed: %v", err)
			log.Println("Continuing with API key only...")
		} else {
			fmt.Printf("✓ Authenticated as: %s\n", authResp.User.Email)
		}
	} else {
		fmt.Println("Using API key authentication only")
		// Manually initialize WebSocket since we're not authenticating
		if err := client.WebSocket.Connect(); err != nil {
			log.Fatalf("Failed to connect WebSocket: %v", err)
		}
	}

	// Wait for connection
	time.Sleep(2 * time.Second)

	if !client.WebSocket.IsConnected() {
		log.Fatal("WebSocket is not connected")
	}

	fmt.Println("\nWEBSOCKET REAL-TIME EXAMPLES")
	fmt.Println("=============================\n")

	// 1. Subscribe to channels
	fmt.Println("1. Subscribing to channels...")
	channels := []string{"transformations", "analysis", "auto-transform"}
	for _, channel := range channels {
		if err := client.WebSocket.Subscribe(channel); err != nil {
			log.Printf("Error subscribing to %s: %v", channel, err)
		} else {
			fmt.Printf("✓ Subscribed to: %s\n", channel)
		}
	}
	fmt.Println()

	// 2. Real-time text transformation
	fmt.Println("2. Real-time text transformation...")
	wg.Add(1)
	
	transformReq := &tonebridge.TransformRequest{
		Text:               "This is absolutely unacceptable! Fix it immediately!",
		TransformationType: tonebridge.TransformationSoften,
		Intensity:          2,
	}
	
	err := client.WebSocket.TransformRealtime(transformReq, 
		func(resp *tonebridge.TransformResponse, err error) {
			defer wg.Done()
			if err != nil {
				fmt.Printf("Transform error: %v\n", err)
				return
			}
			fmt.Println("Real-time transformation completed:")
			fmt.Printf("  Original: %s\n", resp.Data.OriginalText)
			fmt.Printf("  Transformed: %s\n", resp.Data.TransformedText)
			fmt.Printf("  Processing time: %dms\n", resp.Data.ProcessingTimeMs)
		})
	
	if err != nil {
		log.Printf("Error sending transform request: %v", err)
		wg.Done()
	}
	
	// Wait for transformation to complete
	wg.Wait()
	fmt.Println()

	// 3. Real-time text analysis
	fmt.Println("3. Real-time text analysis...")
	wg.Add(1)
	
	analyzeReq := &tonebridge.AnalyzeRequest{
		Text: "I'm really excited about this new feature! It's going to be amazing for our users.",
		AnalysisTypes: []tonebridge.AnalysisType{
			tonebridge.AnalysisTone,
			tonebridge.AnalysisSentiment,
		},
		IncludeSuggestions: true,
	}
	
	err = client.WebSocket.AnalyzeRealtime(analyzeReq,
		func(resp *tonebridge.AnalyzeResponse, err error) {
			defer wg.Done()
			if err != nil {
				fmt.Printf("Analysis error: %v\n", err)
				return
			}
			fmt.Println("Real-time analysis completed:")
			fmt.Printf("  Text: %s\n", resp.Data.Text)
			fmt.Printf("  Tone: %s\n", resp.Data.Tone)
			fmt.Printf("  Clarity Score: %.2f\n", resp.Data.ClarityScore)
			if resp.Data.Sentiment != nil {
				fmt.Printf("  Sentiment - Polarity: %.2f, Subjectivity: %.2f\n",
					resp.Data.Sentiment.Polarity,
					resp.Data.Sentiment.Subjectivity)
			}
		})
	
	if err != nil {
		log.Printf("Error sending analyze request: %v", err)
		wg.Done()
	}
	
	// Wait for analysis to complete
	wg.Wait()
	fmt.Println()

	// 4. Real-time auto-transformation
	fmt.Println("4. Real-time auto-transformation...")
	wg.Add(1)
	
	messageCtx := &tonebridge.MessageContext{
		Message:   "This is terrible! I can't believe you messed this up again!",
		UserID:    "user123",
		TenantID:  "tenant456",
		Platform:  tonebridge.PlatformSlack,
		ChannelID: "general",
	}
	
	err = client.WebSocket.AutoTransformRealtime(messageCtx,
		func(resp *tonebridge.AutoTransformResponse, err error) {
			defer wg.Done()
			if err != nil {
				fmt.Printf("Auto-transform error: %v\n", err)
				return
			}
			fmt.Println("Real-time auto-transformation completed:")
			fmt.Printf("  Original: %s\n", resp.OriginalText)
			fmt.Printf("  Transformed: %s\n", resp.TransformedText)
			if resp.RuleApplied != nil {
				fmt.Printf("  Rule applied: %s\n", resp.RuleApplied.RuleName)
			}
			fmt.Printf("  Confidence: %.2f\n", resp.Confidence)
			fmt.Printf("  Processing time: %dms\n", resp.ProcessingTime)
		})
	
	if err != nil {
		log.Printf("Error sending auto-transform request: %v", err)
		wg.Done()
	}
	
	// Wait for auto-transformation to complete
	wg.Wait()
	fmt.Println()

	// 5. Batch real-time operations
	fmt.Println("5. Sending multiple real-time requests...")
	
	texts := []string{
		"Fix this bug NOW!",
		"Could you please review this when you have time?",
		"This approach is completely wrong and needs to be redone.",
	}
	
	for i, text := range texts {
		wg.Add(1)
		index := i
		currentText := text
		
		req := &tonebridge.TransformRequest{
			Text:               currentText,
			TransformationType: tonebridge.TransformationSoften,
			Intensity:          2,
		}
		
		err := client.WebSocket.TransformRealtime(req,
			func(resp *tonebridge.TransformResponse, err error) {
				defer wg.Done()
				if err != nil {
					fmt.Printf("Request %d error: %v\n", index+1, err)
					return
				}
				fmt.Printf("Request %d completed:\n", index+1)
				fmt.Printf("  Original: %s\n", currentText)
				fmt.Printf("  Transformed: %s\n", resp.Data.TransformedText)
			})
		
		if err != nil {
			log.Printf("Error sending request %d: %v", index+1, err)
			wg.Done()
		}
		
		// Small delay between requests
		time.Sleep(100 * time.Millisecond)
	}
	
	// Wait for all requests to complete
	wg.Wait()
	fmt.Println()

	// 6. Stream continuous updates
	fmt.Println("6. Streaming continuous updates...")
	fmt.Println("(Simulating real-time message stream)")
	
	// Create a channel to stop the stream
	stopStream := make(chan bool)
	
	go func() {
		messages := []string{
			"Update: Server deployment completed",
			"Alert: High CPU usage detected",
			"Info: New user registered",
			"Warning: API rate limit approaching",
			"Success: All tests passed",
		}
		
		for i, msg := range messages {
			select {
			case <-stopStream:
				return
			default:
				fmt.Printf("\n[Stream %d] Processing: %s\n", i+1, msg)
				
				// Send for analysis
				req := &tonebridge.AnalyzeRequest{
					Text: msg,
					AnalysisTypes: []tonebridge.AnalysisType{
						tonebridge.AnalysisPriority,
					},
				}
				
				client.WebSocket.AnalyzeRealtime(req,
					func(resp *tonebridge.AnalyzeResponse, err error) {
						if err != nil {
							fmt.Printf("[Stream %d] Error: %v\n", i+1, err)
							return
						}
						fmt.Printf("[Stream %d] Priority: %s (Quadrant: %s)\n",
							i+1, resp.Data.Priority, resp.Data.PriorityQuadrant)
					})
				
				time.Sleep(2 * time.Second)
			}
		}
	}()
	
	// Let the stream run for a bit
	time.Sleep(12 * time.Second)
	close(stopStream)
	fmt.Println("\nStream stopped")
	fmt.Println()

	// 7. Handle reconnection
	fmt.Println("7. Testing reconnection...")
	fmt.Println("Disconnecting...")
	client.WebSocket.Disconnect()
	
	time.Sleep(2 * time.Second)
	
	fmt.Println("Reconnecting...")
	if err := client.WebSocket.Connect(); err != nil {
		log.Printf("Failed to reconnect: %v", err)
	} else {
		fmt.Println("✓ Reconnected successfully")
		
		// Resubscribe happens automatically
		time.Sleep(1 * time.Second)
		
		// Test that connection works
		wg.Add(1)
		testReq := &tonebridge.TransformRequest{
			Text:               "Testing reconnection",
			TransformationType: tonebridge.TransformationClarify,
			Intensity:          1,
		}
		
		err := client.WebSocket.TransformRealtime(testReq,
			func(resp *tonebridge.TransformResponse, err error) {
				defer wg.Done()
				if err != nil {
					fmt.Printf("Post-reconnection test failed: %v\n", err)
					return
				}
				fmt.Println("✓ Post-reconnection test successful")
			})
		
		if err != nil {
			log.Printf("Error sending test request: %v", err)
			wg.Done()
		}
		
		wg.Wait()
	}
	fmt.Println()

	// 8. Clean shutdown
	fmt.Println("8. Setting up graceful shutdown...")
	fmt.Println("Press Ctrl+C to stop...")
	
	// Set up signal handling
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	
	// Keep the connection alive
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-sigChan:
			fmt.Println("\nShutting down gracefully...")
			
			// Unsubscribe from channels
			for _, channel := range channels {
				if err := client.WebSocket.Unsubscribe(channel); err != nil {
					log.Printf("Error unsubscribing from %s: %v", channel, err)
				} else {
					fmt.Printf("✓ Unsubscribed from: %s\n", channel)
				}
			}
			
			// Disconnect WebSocket
			client.WebSocket.Disconnect()
			
			// Close client
			client.Close()
			
			fmt.Println("✓ Shutdown complete")
			return
			
		case <-ticker.C:
			// Send periodic ping to keep connection alive
			if client.WebSocket.IsConnected() {
				fmt.Println("♥ Heartbeat - Connection alive")
			} else {
				fmt.Println("⚠ Connection lost, attempting to reconnect...")
				if err := client.WebSocket.Connect(); err != nil {
					log.Printf("Reconnection failed: %v", err)
				}
			}
		}
	}
}