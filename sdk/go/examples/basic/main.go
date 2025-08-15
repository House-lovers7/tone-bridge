package main

import (
	"context"
	"fmt"
	"log"
	"os"

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

	// Example harsh text
	harshText := "This is absolutely ridiculous! You need to fix this terrible mess immediately or there will be serious consequences!"

	fmt.Println("Original text:")
	fmt.Println(harshText)
	fmt.Println()

	// 1. Soften the harsh text
	fmt.Println("1. Softening harsh text...")
	softenResp, err := client.Transform.Soften(ctx, harshText, 2, nil)
	if err != nil {
		log.Printf("Error softening text: %v", err)
	} else {
		fmt.Printf("Softened (intensity 2): %s\n", softenResp.Data.TransformedText)
	}
	fmt.Println()

	// 2. Try different intensities
	fmt.Println("2. Trying different softening intensities...")
	for intensity := 1; intensity <= 3; intensity++ {
		resp, err := client.Transform.Soften(ctx, harshText, intensity, nil)
		if err != nil {
			log.Printf("Error with intensity %d: %v", intensity, err)
			continue
		}
		fmt.Printf("Intensity %d: %s\n", intensity, resp.Data.TransformedText)
	}
	fmt.Println()

	// 3. Clarify confusing text
	confusingText := "The thing is, you know, we should maybe possibly consider perhaps looking into the potential of maybe implementing something that could help with the stuff we talked about before."
	
	fmt.Println("3. Clarifying confusing text...")
	fmt.Printf("Original: %s\n", confusingText)
	clarifyResp, err := client.Transform.Clarify(ctx, confusingText, 2, nil)
	if err != nil {
		log.Printf("Error clarifying text: %v", err)
	} else {
		fmt.Printf("Clarified: %s\n", clarifyResp.Data.TransformedText)
	}
	fmt.Println()

	// 4. Structure unorganized text
	unorganizedText := "Need to fix bugs. Also documentation needs updating. Oh and we should test the new feature. Client meeting tomorrow at 2pm. Deploy to production after testing. Review PR from John."
	
	fmt.Println("4. Structuring unorganized text...")
	fmt.Printf("Original: %s\n", unorganizedText)
	structureResp, err := client.Transform.Structure(ctx, unorganizedText, 2, nil)
	if err != nil {
		log.Printf("Error structuring text: %v", err)
	} else {
		fmt.Printf("Structured:\n%s\n", structureResp.Data.TransformedText)
	}
	fmt.Println()

	// 5. Summarize long text
	longText := `The quarterly report shows significant progress in multiple areas. Revenue increased by 
	15% compared to the previous quarter, driven primarily by strong performance in the enterprise segment. 
	Customer acquisition costs decreased by 8%, while customer lifetime value increased by 12%. 
	The product team successfully launched three major features that were well-received by users, 
	resulting in a 20% increase in user engagement metrics. The engineering team improved system 
	reliability, achieving 99.9% uptime for the quarter. Marketing campaigns generated 30% more 
	qualified leads with a 10% reduction in spend. The sales team exceeded their targets by 18%, 
	with particularly strong performance in the APAC region. Looking forward, we plan to expand 
	our presence in European markets and launch two new product lines in Q2.`
	
	fmt.Println("5. Summarizing long text...")
	fmt.Printf("Original length: %d characters\n", len(longText))
	summarizeResp, err := client.Transform.Summarize(ctx, longText, 2, nil)
	if err != nil {
		log.Printf("Error summarizing text: %v", err)
	} else {
		fmt.Printf("Summary:\n%s\n", summarizeResp.Data.TransformedText)
		fmt.Printf("Summary length: %d characters\n", len(summarizeResp.Data.TransformedText))
	}
	fmt.Println()

	// 6. Transform with custom options
	fmt.Println("6. Transform with custom options...")
	options := &tonebridge.TransformOptions{
		PreserveFormatting: true,
		TargetAudience:     "executives",
		Language:           "en",
	}
	
	technicalText := "The API endpoint is throwing 500 errors due to null pointer exceptions in the authentication middleware."
	customResp, err := client.Transform.TransformTerminology(ctx, technicalText, options)
	if err != nil {
		log.Printf("Error transforming terminology: %v", err)
	} else {
		fmt.Printf("Original: %s\n", technicalText)
		fmt.Printf("Non-technical: %s\n", customResp.Data.TransformedText)
	}
	fmt.Println()

	// 7. Custom transformation
	fmt.Println("7. Custom transformation...")
	casualText := "Hey! Wanna grab lunch? There's this cool place nearby."
	customInstructions := "Make this message more formal and professional"
	
	customTransformResp, err := client.Transform.CustomTransform(ctx, casualText, customInstructions, nil)
	if err != nil {
		log.Printf("Error with custom transformation: %v", err)
	} else {
		fmt.Printf("Original: %s\n", casualText)
		fmt.Printf("Formal: %s\n", customTransformResp.Data.TransformedText)
	}

	fmt.Println("\nBasic transformation examples completed!")
}