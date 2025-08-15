package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/tonebridge/go-sdk/tonebridge"
)

func main() {
	// Get API key from environment
	apiKey := os.Getenv("TONEBRIDGE_API_KEY")
	if apiKey == "" {
		log.Fatal("TONEBRIDGE_API_KEY environment variable is required")
	}

	// Initialize client
	client := tonebridge.NewClient(apiKey)

	ctx := context.Background()

	// Sample texts for analysis
	samples := []struct {
		name string
		text string
	}{
		{
			name: "Harsh Email",
			text: "This is completely unacceptable! You've failed to meet the deadline again and I'm extremely disappointed with your performance!",
		},
		{
			name: "Friendly Message",
			text: "Great job on the presentation! I really appreciated your insights and the team loved your ideas. Keep up the excellent work!",
		},
		{
			name: "Confusing Instructions",
			text: "So, you know, maybe we should like consider possibly implementing the thing we discussed, but only if the other stuff is done first, unless the client says otherwise.",
		},
		{
			name: "Technical Report",
			text: "The API latency increased due to inefficient database queries causing N+1 problems, resulting in degraded performance and increased CPU utilization on the RDS instances.",
		},
		{
			name: "Urgent Request",
			text: "URGENT: Server is down! Production is completely broken. Customers can't access the platform. Need immediate fix NOW!",
		},
	}

	for _, sample := range samples {
		fmt.Printf("\n" + strings.Repeat("=", 60) + "\n")
		fmt.Printf("Analyzing: %s\n", sample.name)
		fmt.Printf("Text: %s\n", sample.text)
		fmt.Println(strings.Repeat("-", 60))

		// 1. Analyze tone
		fmt.Println("\n1. TONE ANALYSIS:")
		toneResult, err := client.Analyze.AnalyzeTone(ctx, sample.text)
		if err != nil {
			log.Printf("Error analyzing tone: %v", err)
		} else {
			fmt.Printf("   Tone: %s (confidence: %.2f)\n", toneResult.Tone, toneResult.Confidence)
			if len(toneResult.SubTones) > 0 {
				fmt.Printf("   Sub-tones: %v\n", toneResult.SubTones)
			}
			if len(toneResult.Suggestions) > 0 {
				fmt.Println("   Suggestions:")
				for _, suggestion := range toneResult.Suggestions {
					fmt.Printf("   - %s\n", suggestion)
				}
			}
		}

		// 2. Analyze clarity
		fmt.Println("\n2. CLARITY ANALYSIS:")
		clarityResult, err := client.Analyze.AnalyzeClarity(ctx, sample.text)
		if err != nil {
			log.Printf("Error analyzing clarity: %v", err)
		} else {
			fmt.Printf("   Clarity Score: %.2f/10\n", clarityResult.ClarityScore)
			if len(clarityResult.Issues) > 0 {
				fmt.Println("   Issues found:")
				for _, issue := range clarityResult.Issues {
					fmt.Printf("   - [%s] %s: %s\n", issue.Severity, issue.Type, issue.Description)
				}
			}
			if len(clarityResult.Suggestions) > 0 {
				fmt.Println("   Suggestions:")
				for _, suggestion := range clarityResult.Suggestions {
					fmt.Printf("   - %s\n", suggestion)
				}
			}
		}

		// 3. Analyze priority
		fmt.Println("\n3. PRIORITY ANALYSIS (Eisenhower Matrix):")
		priorityResult, err := client.Analyze.AnalyzePriority(ctx, sample.text)
		if err != nil {
			log.Printf("Error analyzing priority: %v", err)
		} else {
			fmt.Printf("   Priority Score: %.2f\n", priorityResult.Score)
			fmt.Printf("   Quadrant: %s\n", priorityResult.Quadrant)
			fmt.Printf("   Urgency: %.2f/10\n", priorityResult.Urgency)
			fmt.Printf("   Importance: %.2f/10\n", priorityResult.Importance)
			if priorityResult.Reasoning != "" {
				fmt.Printf("   Reasoning: %s\n", priorityResult.Reasoning)
			}
		}

		// 4. Analyze sentiment
		fmt.Println("\n4. SENTIMENT ANALYSIS:")
		sentimentResult, err := client.Analyze.AnalyzeSentiment(ctx, sample.text)
		if err != nil {
			log.Printf("Error analyzing sentiment: %v", err)
		} else {
			fmt.Printf("   Sentiment: %s\n", sentimentResult.Sentiment)
			fmt.Printf("   Polarity: %.2f (range: -1 to 1)\n", sentimentResult.Polarity)
			fmt.Printf("   Subjectivity: %.2f (0=objective, 1=subjective)\n", sentimentResult.Subjectivity)
			if len(sentimentResult.Emotions) > 0 {
				fmt.Println("   Emotions detected:")
				for emotion, score := range sentimentResult.Emotions {
					fmt.Printf("   - %s: %.2f%%\n", emotion, score*100)
				}
			}
		}

		// 5. Analyze readability
		fmt.Println("\n5. READABILITY ANALYSIS:")
		readabilityResult, err := client.Analyze.AnalyzeReadability(ctx, sample.text)
		if err != nil {
			log.Printf("Error analyzing readability: %v", err)
		} else {
			fmt.Printf("   Flesch Reading Ease: %.1f\n", readabilityResult.FleschScore)
			fmt.Printf("   Flesch-Kincaid Grade: %.1f\n", readabilityResult.FleschKincaidGrade)
			fmt.Printf("   Reading Level: %s\n", readabilityResult.ReadingLevel)
			fmt.Printf("   Word Count: %d\n", readabilityResult.WordCount)
			fmt.Printf("   Sentence Count: %d\n", readabilityResult.SentenceCount)
			fmt.Printf("   Avg Sentence Length: %.1f words\n", readabilityResult.AverageSentenceLen)
			fmt.Printf("   Estimated Read Time: %d seconds\n", readabilityResult.EstimatedReadTime)
		}
	}

	// 6. Comprehensive analysis on a longer text
	fmt.Printf("\n" + strings.Repeat("=", 60) + "\n")
	fmt.Println("COMPREHENSIVE ANALYSIS")
	fmt.Println(strings.Repeat("=", 60))

	comprehensiveText := `Dear Team,

I wanted to update you on our Q4 progress. We've successfully launched the new feature set, 
but there are some concerns about performance that need immediate attention. The customer 
feedback has been mostly positive, with a 4.2/5 rating, though some users reported issues 
with the mobile experience.

Our next steps include optimizing the database queries, improving the UI responsiveness, 
and adding the requested export functionality. This is high priority as it directly impacts 
our enterprise clients.

Please review the attached metrics and provide your feedback by EOD Friday.

Best regards,
Project Manager`

	fmt.Printf("\nText:\n%s\n", comprehensiveText)

	comprehensive, err := client.Analyze.ComprehensiveAnalysis(ctx, comprehensiveText)
	if err != nil {
		log.Printf("Error with comprehensive analysis: %v", err)
	} else {
		fmt.Println("\nCOMPREHENSIVE ANALYSIS RESULTS:")
		fmt.Printf("Tone: %s\n", comprehensive.Tone)
		fmt.Printf("Clarity Score: %.2f/10\n", comprehensive.ClarityScore)
		fmt.Printf("Priority: %s\n", comprehensive.Priority)
		
		if comprehensive.Sentiment != nil {
			fmt.Printf("Sentiment - Polarity: %.2f, Subjectivity: %.2f\n", 
				comprehensive.Sentiment.Polarity, 
				comprehensive.Sentiment.Subjectivity)
		}
		
		if len(comprehensive.Suggestions) > 0 {
			fmt.Println("\nSuggestions:")
			for i, suggestion := range comprehensive.Suggestions {
				fmt.Printf("%d. %s\n", i+1, suggestion)
			}
		}
		
		if len(comprehensive.Improvements) > 0 {
			fmt.Println("\nPotential Improvements:")
			for i, improvement := range comprehensive.Improvements {
				fmt.Printf("%d. %s\n", i+1, improvement)
			}
		}
	}

	// 7. Extract key points
	fmt.Printf("\n" + strings.Repeat("=", 60) + "\n")
	fmt.Println("KEY POINTS EXTRACTION")
	fmt.Println(strings.Repeat("=", 60))

	keyPointsResult, err := client.Analyze.ExtractKeyPoints(ctx, comprehensiveText, 5)
	if err != nil {
		log.Printf("Error extracting key points: %v", err)
	} else {
		fmt.Println("\nKey Points:")
		for i, point := range keyPointsResult.KeyPoints {
			fmt.Printf("%d. [Importance: %.1f] %s\n", 
				i+1, point.Importance, point.Point)
			if point.Category != "" {
				fmt.Printf("   Category: %s\n", point.Category)
			}
		}
		if keyPointsResult.Summary != "" {
			fmt.Printf("\nSummary: %s\n", keyPointsResult.Summary)
		}
	}

	// 8. Compare tone between two texts
	fmt.Printf("\n" + strings.Repeat("=", 60) + "\n")
	fmt.Println("TONE COMPARISON")
	fmt.Println(strings.Repeat("=", 60))

	text1 := "This needs to be fixed immediately! I can't believe this happened again!"
	text2 := "When you have a moment, could you please look into this issue? Thank you for your help."

	fmt.Printf("\nText 1: %s\n", text1)
	fmt.Printf("Text 2: %s\n", text2)

	comparison, err := client.Analyze.CompareTone(ctx, text1, text2)
	if err != nil {
		log.Printf("Error comparing tones: %v", err)
	} else {
		fmt.Printf("\nComparison Results:\n")
		fmt.Printf("Text 1 Tone: %s\n", comparison.Text1Tone)
		fmt.Printf("Text 2 Tone: %s\n", comparison.Text2Tone)
		fmt.Printf("Similarity: %.2f%%\n", comparison.Similarity*100)
		if len(comparison.Differences) > 0 {
			fmt.Println("Key Differences:")
			for _, diff := range comparison.Differences {
				fmt.Printf("- %s\n", diff)
			}
		}
	}

	fmt.Println("\nAnalysis examples completed!")
}