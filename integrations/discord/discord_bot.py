"""
Discord Integration for ToneBridge
Uses py-cord for Discord bot functionality
"""

import os
import asyncio
from typing import Optional, List, Dict, Any
import discord
from discord import app_commands
from discord.ext import commands
import httpx
from datetime import datetime
import json

# Configuration
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
TONEBRIDGE_API_URL = os.environ.get("TONEBRIDGE_API_URL", "http://localhost:8080")
COMMAND_PREFIX = "!"

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class ToneBridgeBot(commands.Bot):
    """
    Discord bot for ToneBridge
    """
    
    def __init__(self):
        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            help_command=None  # We'll create a custom help command
        )
        self.tonebridge_client = ToneBridgeClient(TONEBRIDGE_API_URL)
    
    async def setup_hook(self):
        """Setup hook for bot initialization"""
        # Sync slash commands
        await self.tree.sync()
        print(f"Synced {len(self.tree.get_commands())} slash commands")
    
    async def on_ready(self):
        """Called when bot is ready"""
        print(f'{self.user} has connected to Discord!')
        print(f'Connected to {len(self.guilds)} guilds')
        
        # Set presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.helping,
                name="with message transformation"
            )
        )

# Create bot instance
bot = ToneBridgeBot()

class TransformView(discord.ui.View):
    """Interactive view for message transformations"""
    
    def __init__(self, original_text: str, transformed_text: str):
        super().__init__(timeout=300)  # 5 minute timeout
        self.original_text = original_text
        self.transformed_text = transformed_text
    
    @discord.ui.button(label="Apply Another Transform", style=discord.ButtonStyle.primary, emoji="🔄")
    async def apply_another(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Apply another transformation"""
        await interaction.response.send_message(
            "Choose a transformation:",
            view=TransformSelectionView(self.transformed_text),
            ephemeral=True
        )
    
    @discord.ui.button(label="Show Original", style=discord.ButtonStyle.secondary, emoji="📝")
    async def show_original(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show original text"""
        embed = discord.Embed(
            title="Original Text",
            description=self.original_text[:4000],
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Analyze", style=discord.ButtonStyle.success, emoji="📊")
    async def analyze(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Analyze the transformed text"""
        await interaction.response.defer(ephemeral=True)
        
        client = ToneBridgeClient(TONEBRIDGE_API_URL)
        result = await client.analyze_text(self.transformed_text)
        
        if result["success"]:
            data = result["data"]
            embed = create_analysis_embed(data)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("Failed to analyze text", ephemeral=True)

class TransformSelectionView(discord.ui.View):
    """View for selecting transformation type"""
    
    def __init__(self, text: str):
        super().__init__(timeout=60)
        self.text = text
    
    @discord.ui.select(
        placeholder="Choose a transformation...",
        options=[
            discord.SelectOption(label="Soften", value="soften", description="Make text warmer", emoji="🤗"),
            discord.SelectOption(label="Formalize", value="formalize", description="Make more professional", emoji="👔"),
            discord.SelectOption(label="Clarify", value="clarify", description="Improve structure", emoji="📋"),
            discord.SelectOption(label="Summarize", value="summarize", description="Create summary", emoji="📄"),
        ]
    )
    async def select_transformation(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Handle transformation selection"""
        transformation = select.values[0]
        await interaction.response.defer()
        
        client = ToneBridgeClient(TONEBRIDGE_API_URL)
        
        # Map selection to API parameters
        transform_map = {
            "soften": ("tone", "warm"),
            "formalize": ("tone", "professional"),
            "clarify": ("structure", None),
            "summarize": ("summarize", None)
        }
        
        transform_type, target_tone = transform_map[transformation]
        result = await client.transform_text(self.text, transform_type, target_tone)
        
        if result["success"]:
            embed = create_transform_embed(
                self.text,
                result["data"]["transformed_text"],
                transformation
            )
            view = TransformView(self.text, result["data"]["transformed_text"])
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send("Failed to transform text", ephemeral=True)

# Slash Commands
@bot.tree.command(name="soften", description="Make your message warmer and more considerate")
@app_commands.describe(text="The text to soften")
async def soften_slash(interaction: discord.Interaction, text: str):
    """Slash command to soften text"""
    await interaction.response.defer()
    
    client = ToneBridgeClient(TONEBRIDGE_API_URL)
    result = await client.transform_text(text, "tone", "warm")
    
    if result["success"]:
        embed = create_transform_embed(
            text, 
            result["data"]["transformed_text"],
            "Softened"
        )
        view = TransformView(text, result["data"]["transformed_text"])
        await interaction.followup.send(embed=embed, view=view)
    else:
        await interaction.followup.send("Failed to transform text", ephemeral=True)

@bot.tree.command(name="clarify", description="Structure your message for better clarity")
@app_commands.describe(text="The text to clarify")
async def clarify_slash(interaction: discord.Interaction, text: str):
    """Slash command to clarify text"""
    await interaction.response.defer()
    
    client = ToneBridgeClient(TONEBRIDGE_API_URL)
    result = await client.transform_text(text, "structure")
    
    if result["success"]:
        embed = create_transform_embed(
            text,
            result["data"]["transformed_text"],
            "Clarified"
        )
        view = TransformView(text, result["data"]["transformed_text"])
        await interaction.followup.send(embed=embed, view=view)
    else:
        await interaction.followup.send("Failed to transform text", ephemeral=True)

@bot.tree.command(name="analyze", description="Analyze message tone and priority")
@app_commands.describe(text="The text to analyze")
async def analyze_slash(interaction: discord.Interaction, text: str):
    """Slash command to analyze text"""
    await interaction.response.defer()
    
    client = ToneBridgeClient(TONEBRIDGE_API_URL)
    result = await client.analyze_text(text)
    
    if result["success"]:
        embed = create_analysis_embed(result["data"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to analyze text", ephemeral=True)

@bot.tree.command(name="prioritize", description="Score message priority using Eisenhower Matrix")
@app_commands.describe(text="The text to prioritize")
async def prioritize_slash(interaction: discord.Interaction, text: str):
    """Slash command to score priority"""
    await interaction.response.defer()
    
    client = ToneBridgeClient(TONEBRIDGE_API_URL)
    result = await client.score_priority(text)
    
    if result["success"]:
        embed = create_priority_embed(result["data"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to score priority", ephemeral=True)

@bot.tree.command(name="structure", description="Structure text into organized requirements")
@app_commands.describe(text="The text to structure")
async def structure_slash(interaction: discord.Interaction, text: str):
    """Slash command to structure requirements"""
    await interaction.response.defer()
    
    client = ToneBridgeClient(TONEBRIDGE_API_URL)
    result = await client.structure_requirements(text)
    
    if result["success"]:
        embed = create_structure_embed(result["data"])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Failed to structure text", ephemeral=True)

# Context Menu Commands (right-click on messages)
@bot.tree.context_menu(name="Soften Message")
async def soften_context(interaction: discord.Interaction, message: discord.Message):
    """Context menu to soften a message"""
    await interaction.response.defer(ephemeral=True)
    
    client = ToneBridgeClient(TONEBRIDGE_API_URL)
    result = await client.transform_text(message.content, "tone", "warm")
    
    if result["success"]:
        embed = create_transform_embed(
            message.content,
            result["data"]["transformed_text"],
            "Softened"
        )
        view = TransformView(message.content, result["data"]["transformed_text"])
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.followup.send("Failed to transform text", ephemeral=True)

@bot.tree.context_menu(name="Analyze Message")
async def analyze_context(interaction: discord.Interaction, message: discord.Message):
    """Context menu to analyze a message"""
    await interaction.response.defer(ephemeral=True)
    
    client = ToneBridgeClient(TONEBRIDGE_API_URL)
    result = await client.analyze_text(message.content)
    
    if result["success"]:
        embed = create_analysis_embed(result["data"])
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send("Failed to analyze text", ephemeral=True)

# Regular Commands (prefix-based)
@bot.command(name="help")
async def help_command(ctx):
    """Custom help command"""
    embed = discord.Embed(
        title="ToneBridge Help",
        description="Transform your messages for better communication",
        color=discord.Color.blue()
    )
    
    # Slash commands
    embed.add_field(
        name="📝 Slash Commands",
        value=(
            "`/soften [text]` - Make text warmer\n"
            "`/clarify [text]` - Improve structure\n"
            "`/analyze [text]` - Analyze tone & priority\n"
            "`/prioritize [text]` - Score priority\n"
            "`/structure [text]` - Structure requirements"
        ),
        inline=False
    )
    
    # Context menu
    embed.add_field(
        name="🖱️ Right-Click Options",
        value=(
            "Right-click any message and select:\n"
            "• **Soften Message** - Transform to warmer tone\n"
            "• **Analyze Message** - Get tone analysis"
        ),
        inline=False
    )
    
    # Tips
    embed.add_field(
        name="💡 Tips",
        value=(
            "• Use buttons on responses for additional transforms\n"
            "• Slash commands work in any channel\n"
            "• Right-click works on any visible message"
        ),
        inline=False
    )
    
    embed.set_footer(text="ToneBridge - Bridge the communication gap")
    await ctx.send(embed=embed)

# Helper functions to create embeds
def create_transform_embed(original: str, transformed: str, transform_type: str) -> discord.Embed:
    """Create embed for transformation result"""
    embed = discord.Embed(
        title=f"✨ {transform_type} Message",
        color=discord.Color.green()
    )
    
    # Truncate if too long
    if len(original) > 1000:
        original = original[:997] + "..."
    if len(transformed) > 1000:
        transformed = transformed[:997] + "..."
    
    embed.add_field(name="Original", value=original, inline=False)
    embed.add_field(name="Transformed", value=transformed, inline=False)
    embed.set_footer(text="Use the buttons below for more options")
    
    return embed

def create_analysis_embed(data: Dict[str, Any]) -> discord.Embed:
    """Create embed for analysis result"""
    tone = data.get("tone", "unknown")
    clarity = data.get("clarity", 0)
    priority = data.get("priority", "medium")
    suggestions = data.get("suggestions", [])
    
    # Priority colors
    priority_colors = {
        "critical": discord.Color.red(),
        "high": discord.Color.orange(),
        "medium": discord.Color.yellow(),
        "low": discord.Color.green()
    }
    
    embed = discord.Embed(
        title="📊 Message Analysis",
        color=priority_colors.get(priority, discord.Color.blue())
    )
    
    embed.add_field(name="Tone", value=tone.title(), inline=True)
    embed.add_field(name="Clarity", value=f"{clarity:.1%}", inline=True)
    embed.add_field(name="Priority", value=priority.title(), inline=True)
    
    if suggestions:
        suggestions_text = "\n".join([f"• {s}" for s in suggestions[:5]])
        embed.add_field(name="Suggestions", value=suggestions_text, inline=False)
    
    return embed

def create_priority_embed(data: Dict[str, Any]) -> discord.Embed:
    """Create embed for priority scoring"""
    urgency = data.get("urgency_score", 0)
    importance = data.get("importance_score", 0)
    priority_level = data.get("priority_level", "medium")
    quadrant = data.get("priority_matrix_quadrant", "Q2")
    response_time = data.get("recommended_response_time", "within 24 hours")
    
    # Priority emoji and color
    priority_map = {
        "critical": ("🔴", discord.Color.red()),
        "high": ("🟠", discord.Color.orange()),
        "medium": ("🟡", discord.Color.yellow()),
        "low": ("🟢", discord.Color.green())
    }
    
    emoji, color = priority_map.get(priority_level, ("⚪", discord.Color.default()))
    
    embed = discord.Embed(
        title=f"{emoji} Priority Assessment",
        color=color
    )
    
    embed.add_field(name="Urgency Score", value=f"{urgency:.0f}/100", inline=True)
    embed.add_field(name="Importance Score", value=f"{importance:.0f}/100", inline=True)
    embed.add_field(name="Eisenhower Quadrant", value=quadrant, inline=True)
    embed.add_field(
        name="Recommended Response",
        value=response_time,
        inline=False
    )
    
    # Quadrant explanation
    quadrant_info = {
        "Q1": "Do First - Urgent & Important",
        "Q2": "Schedule - Important but not Urgent",
        "Q3": "Delegate - Urgent but not Important",
        "Q4": "Eliminate - Neither Urgent nor Important"
    }
    
    embed.add_field(
        name="Action",
        value=quadrant_info.get(quadrant, "Unknown"),
        inline=False
    )
    
    return embed

def create_structure_embed(data: Dict[str, Any]) -> discord.Embed:
    """Create embed for structured requirements"""
    embed = discord.Embed(
        title="📋 Structured Requirements",
        color=discord.Color.blue()
    )
    
    background = data.get("background", "Not specified")
    requests = data.get("requests", [])
    constraints = data.get("constraints", [])
    timeline = data.get("timeline", "Not specified")
    missing_info = data.get("missing_info", [])
    
    # Add fields
    embed.add_field(
        name="🎯 Background",
        value=background[:1000] if background else "Not specified",
        inline=False
    )
    
    if requests:
        requests_text = "\n".join([f"• {r}" for r in requests[:5]])
        embed.add_field(name="📝 Requests", value=requests_text, inline=False)
    
    if constraints:
        constraints_text = "\n".join([f"• {c}" for c in constraints[:5]])
        embed.add_field(name="⚠️ Constraints", value=constraints_text, inline=False)
    
    embed.add_field(name="⏰ Timeline", value=timeline, inline=False)
    
    if missing_info:
        missing_text = "\n".join([f"• {m}" for m in missing_info[:3]])
        embed.add_field(name="❓ Missing Information", value=missing_text, inline=False)
    
    return embed

class ToneBridgeClient:
    """Client for ToneBridge API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
    
    async def transform_text(self, text: str, transformation_type: str, target_tone: str = None):
        """Transform text - mock implementation"""
        return {
            "success": True,
            "data": {
                "transformed_text": f"[{transformation_type}]: {text}",
                "suggestions": ["Consider adding context", "Use active voice"]
            }
        }
    
    async def analyze_text(self, text: str):
        """Analyze text - mock implementation"""
        return {
            "success": True,
            "data": {
                "tone": "professional",
                "clarity": 0.75,
                "priority": "medium",
                "suggestions": ["Add deadlines", "Clarify action items"]
            }
        }
    
    async def score_priority(self, text: str):
        """Score priority - mock implementation"""
        return {
            "success": True,
            "data": {
                "urgency_score": 65,
                "importance_score": 70,
                "priority_level": "high",
                "priority_matrix_quadrant": "Q1",
                "recommended_response_time": "within 4 hours"
            }
        }
    
    async def structure_requirements(self, text: str):
        """Structure requirements - mock implementation"""
        return {
            "success": True,
            "data": {
                "background": "User needs Discord integration",
                "requests": ["Add slash commands", "Implement context menus"],
                "constraints": ["Must use py-cord", "Rate limits apply"],
                "timeline": "1 week",
                "missing_info": ["Bot permissions needed", "Target Discord version"]
            }
        }

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)