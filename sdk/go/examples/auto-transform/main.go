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

	fmt.Println("AUTO-TRANSFORM EXAMPLES")
	fmt.Println("=======================\n")

	// 1. Get current configuration
	fmt.Println("1. Getting current auto-transform configuration...")
	config, err := client.AutoTransform.GetConfig(ctx)
	if err != nil {
		log.Printf("Error getting config: %v", err)
	} else {
		fmt.Printf("Auto-transform enabled: %v\n", config.Enabled)
		fmt.Printf("Default transformation: %s\n", config.DefaultTransformationType)
		fmt.Printf("Default intensity: %d\n", config.DefaultIntensity)
		fmt.Printf("Require confirmation: %v\n", config.RequireConfirmation)
	}
	fmt.Println()

	// 2. Create auto-transform rules
	fmt.Println("2. Creating auto-transform rules...")
	
	// Rule 1: Soften harsh sentiment
	harshSentimentRule := &tonebridge.AutoTransformRule{
		RuleName:               "Soften Harsh Messages",
		Description:            "Automatically soften messages with negative sentiment",
		Enabled:                true,
		Priority:               1,
		TriggerType:            tonebridge.TriggerSentiment,
		TriggerValue: map[string]interface{}{
			"threshold": -0.5,
			"operator":  "less_than",
		},
		TransformationType:      tonebridge.TransformationSoften,
		TransformationIntensity: 2,
		Platforms:               []string{"slack", "teams"},
	}

	rule1, err := client.AutoTransform.CreateRule(ctx, harshSentimentRule)
	if err != nil {
		log.Printf("Error creating harsh sentiment rule: %v", err)
	} else {
		fmt.Printf("Created rule: %s (ID: %s)\n", rule1.RuleName, rule1.ID)
	}

	// Rule 2: Clarify long messages
	longMessageRule := &tonebridge.AutoTransformRule{
		RuleName:               "Clarify Long Messages",
		Description:            "Automatically clarify messages over 500 characters",
		Enabled:                true,
		Priority:               2,
		TriggerType:            tonebridge.TriggerPattern,
		TriggerValue: map[string]interface{}{
			"pattern":      "length",
			"min_length":   500,
		},
		TransformationType:      tonebridge.TransformationClarify,
		TransformationIntensity: 2,
		Channels:                []string{"general", "announcements"},
	}

	rule2, err := client.AutoTransform.CreateRule(ctx, longMessageRule)
	if err != nil {
		log.Printf("Error creating long message rule: %v", err)
	} else {
		fmt.Printf("Created rule: %s (ID: %s)\n", rule2.RuleName, rule2.ID)
	}

	// Rule 3: Structure requirements for project channels
	requirementsRule := &tonebridge.AutoTransformRule{
		RuleName:               "Structure Requirements",
		Description:            "Structure requirements in project channels",
		Enabled:                true,
		Priority:               3,
		TriggerType:            tonebridge.TriggerKeyword,
		TriggerValue: map[string]interface{}{
			"keywords": []string{"requirement", "need to", "must have", "should have"},
			"mode":     "any",
		},
		TransformationType:      tonebridge.TransformationRequirementStructuring,
		TransformationIntensity: 2,
		Channels:                []string{"project-*", "dev-*"},
	}

	rule3, err := client.AutoTransform.CreateRule(ctx, requirementsRule)
	if err != nil {
		log.Printf("Error creating requirements rule: %v", err)
	} else {
		fmt.Printf("Created rule: %s (ID: %s)\n", rule3.RuleName, rule3.ID)
	}
	fmt.Println()

	// 3. List all rules
	fmt.Println("3. Listing all auto-transform rules...")
	rules, err := client.AutoTransform.ListRules(ctx, nil)
	if err != nil {
		log.Printf("Error listing rules: %v", err)
	} else {
		fmt.Printf("Found %d rules:\n", len(rules))
		for _, rule := range rules {
			status := "disabled"
			if rule.Enabled {
				status = "enabled"
			}
			fmt.Printf("  - [%s] %s (Priority: %d, Type: %s)\n", 
				status, rule.RuleName, rule.Priority, rule.TriggerType)
		}
	}
	fmt.Println()

	// 4. Evaluate rules for a message
	fmt.Println("4. Evaluating rules for sample messages...")
	
	testMessages := []struct {
		text     string
		platform tonebridge.Platform
		channel  string
	}{
		{
			text:     "This is absolutely terrible! You completely messed up the deployment!",
			platform: tonebridge.PlatformSlack,
			channel:  "general",
		},
		{
			text:     "We need to implement user authentication, must have OAuth support, should have 2FA",
			platform: tonebridge.PlatformTeams,
			channel:  "project-auth",
		},
		{
			text:     "Here's a quick update on the project status.",
			platform: tonebridge.PlatformSlack,
			channel:  "random",
		},
	}

	for i, test := range testMessages {
		fmt.Printf("\nTest Message %d: %s\n", i+1, test.text)
		fmt.Printf("Platform: %s, Channel: %s\n", test.platform, test.channel)
		
		messageCtx := &tonebridge.MessageContext{
			Message:   test.text,
			UserID:    "user123",
			TenantID:  "tenant456",
			Platform:  test.platform,
			ChannelID: test.channel,
		}
		
		result, err := client.AutoTransform.EvaluateRules(ctx, messageCtx)
		if err != nil {
			log.Printf("Error evaluating rules: %v", err)
		} else {
			if result.ShouldTransform {
				fmt.Printf("✓ Should transform: YES\n")
				fmt.Printf("  Matching rule: %s\n", result.RuleName)
				fmt.Printf("  Transformation: %s (intensity: %d)\n", 
					result.TransformationType, result.TransformationIntensity)
				fmt.Printf("  Confidence: %.2f\n", result.Confidence)
				fmt.Printf("  Reason: %s\n", result.Reason)
				
				// Apply the transformation
				transformed, err := client.AutoTransform.ApplyTransformation(ctx, messageCtx)
				if err != nil {
					log.Printf("Error applying transformation: %v", err)
				} else {
					fmt.Printf("  Transformed text: %s\n", transformed.TransformedText)
				}
			} else {
				fmt.Printf("✗ Should transform: NO\n")
				fmt.Printf("  Reason: %s\n", result.Reason)
			}
		}
	}
	fmt.Println()

	// 5. Use templates
	fmt.Println("5. Using auto-transform templates...")
	templates, err := client.AutoTransform.ListTemplates(ctx, "communication")
	if err != nil {
		log.Printf("Error listing templates: %v", err)
	} else {
		fmt.Printf("Available templates:\n")
		for _, template := range templates {
			fmt.Printf("  - %s: %s\n", template.TemplateName, template.Description)
			if template.IsSystem {
				fmt.Printf("    (System template)\n")
			}
		}
		
		// Apply a template if available
		if len(templates) > 0 {
			fmt.Printf("\nApplying template: %s\n", templates[0].TemplateName)
			customization := map[string]interface{}{
				"channels": []string{"support", "customer-feedback"},
				"priority": 5,
			}
			
			newRule, err := client.AutoTransform.ApplyTemplate(ctx, templates[0].ID, customization)
			if err != nil {
				log.Printf("Error applying template: %v", err)
			} else {
				fmt.Printf("Created rule from template: %s\n", newRule.RuleName)
			}
		}
	}
	fmt.Println()

	// 6. Test a rule
	fmt.Println("6. Testing a rule with sample text...")
	if rule1 != nil {
		sampleText := "I'm really frustrated with this situation and need it resolved ASAP!"
		
		testResult, err := client.AutoTransform.TestRule(ctx, rule1, sampleText)
		if err != nil {
			log.Printf("Error testing rule: %v", err)
		} else {
			fmt.Printf("Rule: %s\n", rule1.RuleName)
			fmt.Printf("Sample text: %s\n", sampleText)
			fmt.Printf("Would trigger: %v\n", testResult.WouldTrigger)
			if testResult.WouldTrigger {
				fmt.Printf("Transformed: %s\n", testResult.TransformedText)
				fmt.Printf("Confidence: %.2f\n", testResult.Confidence)
			}
			fmt.Printf("Reason: %s\n", testResult.Reason)
		}
	}
	fmt.Println()

	// 7. Get statistics
	fmt.Println("7. Getting auto-transform statistics...")
	stats, err := client.AutoTransform.GetStatistics(ctx, "daily")
	if err != nil {
		log.Printf("Error getting statistics: %v", err)
	} else {
		fmt.Printf("Period: %s\n", stats.Period)
		fmt.Printf("Total transformations: %d\n", stats.TotalTransformations)
		fmt.Printf("Successful: %d\n", stats.SuccessfulTransforms)
		fmt.Printf("Failed: %d\n", stats.FailedTransforms)
		fmt.Printf("Average confidence: %.2f\n", stats.AverageConfidence)
		fmt.Printf("Average processing time: %dms\n", stats.AverageProcessingTime)
		
		if len(stats.TopRules) > 0 {
			fmt.Println("Top rules by usage:")
			for i, ruleStat := range stats.TopRules {
				fmt.Printf("  %d. %s - %d uses (%.1f%% success rate)\n",
					i+1, ruleStat.RuleName, ruleStat.UsageCount, ruleStat.SuccessRate*100)
			}
		}
		
		if len(stats.TransformationTypes) > 0 {
			fmt.Println("Transformation types:")
			for tType, count := range stats.TransformationTypes {
				fmt.Printf("  - %s: %d\n", tType, count)
			}
		}
	}
	fmt.Println()

	// 8. Get history
	fmt.Println("8. Getting auto-transform history...")
	historyFilters := &tonebridge.HistoryFilters{
		Limit: 5,
	}
	history, err := client.AutoTransform.GetHistory(ctx, historyFilters)
	if err != nil {
		log.Printf("Error getting history: %v", err)
	} else {
		fmt.Printf("Recent transformations:\n")
		for _, entry := range history {
			fmt.Printf("  - Rule: %s\n", entry.RuleName)
			fmt.Printf("    Original: %s\n", entry.OriginalText)
			fmt.Printf("    Transformed: %s\n", entry.TransformedText)
			fmt.Printf("    Platform: %s\n", entry.Platform)
			fmt.Printf("    Applied: %v (Confidence: %.2f)\n", entry.Applied, entry.Confidence)
			fmt.Printf("    Time: %s\n", entry.CreatedAt)
			fmt.Println()
		}
	}

	// 9. Update a rule
	if rule1 != nil {
		fmt.Println("9. Updating a rule...")
		rule1.Description = "Updated: Automatically soften very harsh messages"
		rule1.TransformationIntensity = 3
		
		updated, err := client.AutoTransform.UpdateRule(ctx, rule1.ID, rule1)
		if err != nil {
			log.Printf("Error updating rule: %v", err)
		} else {
			fmt.Printf("Updated rule: %s\n", updated.RuleName)
			fmt.Printf("New description: %s\n", updated.Description)
			fmt.Printf("New intensity: %d\n", updated.TransformationIntensity)
		}
	}
	fmt.Println()

	// 10. Export and import rules
	fmt.Println("10. Exporting and importing rules...")
	exportedRules, err := client.AutoTransform.ExportRules(ctx)
	if err != nil {
		log.Printf("Error exporting rules: %v", err)
	} else {
		fmt.Printf("Exported %d rules\n", len(exportedRules))
		
		// Could import these to another environment
		// importResult, err := client.AutoTransform.ImportRules(ctx, exportedRules, false)
	}

	// Clean up - disable or delete created rules (optional)
	fmt.Println("\nCleaning up created rules...")
	if rule1 != nil {
		err := client.AutoTransform.DisableRule(ctx, rule1.ID)
		if err != nil {
			log.Printf("Error disabling rule1: %v", err)
		} else {
			fmt.Printf("Disabled rule: %s\n", rule1.RuleName)
		}
	}
	
	if rule2 != nil {
		err := client.AutoTransform.DeleteRule(ctx, rule2.ID)
		if err != nil {
			log.Printf("Error deleting rule2: %v", err)
		} else {
			fmt.Printf("Deleted rule: %s\n", rule2.RuleName)
		}
	}

	fmt.Println("\nAuto-transform examples completed!")
}